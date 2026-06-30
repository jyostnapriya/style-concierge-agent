import datetime
import re
import json
import sys
from typing import Any, Optional
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent, Context
from google.adk.models import Gemini
from google.adk.workflow import Workflow, START, Edge, node
from google.adk.events.request_input import RequestInput
from google.adk.tools import AgentTool, McpToolset
from google.adk.apps import App
from mcp import StdioServerParameters
from app.config import config

# Define Shared State
class StyleState(BaseModel):
    user_request: str = ""
    weather_info: str = ""
    outfit_suggestion: str = ""
    hitl_feedback: str = ""
    security_error_message: str = ""
    audit_log: list[str] = Field(default_factory=list)

# Initialize MCP Toolset to connect to our local MCP server
mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"]
    )
)

# 1. Specialized Sub-Agents using the MCP Toolset
weather_agent = LlmAgent(
    name="weather_agent",
    model=Gemini(model=config.model),
    instruction="Given a location, retrieve and summarize the weather forecast using the weather tool from the toolset. Keep it concise.",
    tools=[mcp_toolset]
)

style_recommender = LlmAgent(
    name="style_recommender",
    model=Gemini(model=config.model),
    instruction=(
        "Given the weather summary and style preferences, suggest a cohesive outfit (top, bottom, shoes, accessories) "
        "and explain why it fits the weather. Use the color palette, wardrobe basics, and style tips tools from the toolset."
    ),
    tools=[mcp_toolset]
)

# 2. Main Orchestrator Agent
orchestrator = LlmAgent(
    name="orchestrator",
    model=Gemini(model=config.model),
    instruction=(
        "You are the main Style Concierge Orchestrator. "
        "Your task is to provide style suggestions. "
        "1. First, call weather_agent to analyze the weather for the user's location. "
        "2. Once you have the weather, call style_recommender to get outfit suggestions based on the weather and the event/style preferences. "
        "Return the final combined outfit recommendations."
    ),
    tools=[
        AgentTool(agent=weather_agent),
        AgentTool(agent=style_recommender),
    ]
)

# 3. Security Checkpoint Node
@node(rerun_on_resume=False)
async def security_checkpoint(ctx: Context, node_input: Any) -> str:
    # Parse prompt
    prompt = ""
    if isinstance(node_input, dict):
        prompt = node_input.get("request", "")
    elif isinstance(node_input, str):
        prompt = node_input
    else:
        prompt = str(node_input)

    ctx.state["user_request"] = prompt

    # PII Scrubbing
    scrubbed_prompt = prompt
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    scrubbed_prompt = re.sub(email_pattern, "[REDACTED_EMAIL]", scrubbed_prompt)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    scrubbed_prompt = re.sub(phone_pattern, "[REDACTED_PHONE]", scrubbed_prompt)

    ctx.state["user_request"] = scrubbed_prompt

    # Prompt Injection Detection
    injection_keywords = ["ignore previous instructions", "system prompt", "override instructions", "bypass security"]
    is_injection = any(kw in prompt.lower() for kw in injection_keywords)

    # Domain-specific rule
    inappropriate_words = ["nude", "naked"]
    is_inappropriate = any(w in prompt.lower() for w in inappropriate_words)

    # Audit Log
    log_entry = {
        "timestamp": str(datetime.datetime.now()),
        "severity": "INFO",
        "action": "security_check",
        "pii_scrubbed": scrubbed_prompt != prompt,
        "injection_detected": is_injection,
        "inappropriate_detected": is_inappropriate
    }

    # Safely retrieve and update the audit log list
    audit_log = ctx.state.get("audit_log")
    if audit_log is None:
        audit_log = []
    # Make a copy or update list
    if not isinstance(audit_log, list):
        audit_log = list(audit_log)

    if is_injection:
        log_entry["severity"] = "CRITICAL"
        log_entry["reason"] = "Prompt injection attempt detected"
        audit_log.append(json.dumps(log_entry))
        ctx.state["audit_log"] = audit_log
        ctx.state["security_error_message"] = "Security violation: potential prompt injection detected."
        ctx.route = "SECURITY_EVENT"
        return "SECURITY_EVENT"
    
    if is_inappropriate:
        log_entry["severity"] = "WARNING"
        log_entry["reason"] = "Inappropriate request detected"
        audit_log.append(json.dumps(log_entry))
        ctx.state["audit_log"] = audit_log
        ctx.state["security_error_message"] = "Policy violation: request contains inappropriate terms."
        ctx.route = "SECURITY_EVENT"
        return "SECURITY_EVENT"

    audit_log.append(json.dumps(log_entry))
    ctx.state["audit_log"] = audit_log
    ctx.route = "clean"
    return "clean"

# 4. Security Error Node
@node
async def security_error(ctx: Context) -> str:
    err = ctx.state.get("security_error_message", "A security violation occurred.")
    return f"Access Denied: {err}"

# 5. Orchestration Runner Node
@node(rerun_on_resume=True)
async def run_orchestration(ctx: Context) -> str:
    user_request = ctx.state.get("user_request", "")
    response = await ctx.run_node(orchestrator, node_input=user_request)
    ctx.state["outfit_suggestion"] = str(response)
    return str(response)

# 6. Human-in-the-Loop Feedback Node
@node(rerun_on_resume=True)
async def human_review(ctx: Context, node_input: Any):
    interrupt_id = "user_approval"
    if interrupt_id in ctx.resume_inputs:
        response = ctx.resume_inputs[interrupt_id]
        feedback = str(response).strip().lower()
        if feedback in ["yes", "approve", "approved", "ok", "y"]:
            ctx.state["hitl_feedback"] = "approved"
            ctx.route = "approved"
            return "approved"
        else:
            ctx.state["hitl_feedback"] = f"rejected: {response}"
            # Append feedback to request for regeneration
            ctx.state["user_request"] = (
                f"{ctx.state.get('user_request')}\n"
                f"[Feedback from human]: Please adjust the suggestion based on: {response}"
            )
            ctx.route = "rejected"
            return "rejected"

    suggestion = ctx.state.get("outfit_suggestion", "")
    message = (
        f"\n=== Outfit Suggestion ===\n{suggestion}\n=========================\n"
        "Do you approve this suggestion? Enter 'yes' to approve, or enter your feedback to adjust:"
    )
    return RequestInput(interrupt_id=interrupt_id, message=message)

# 7. Final Output Node
@node
async def final_output(ctx: Context) -> str:
    suggestion = ctx.state.get("outfit_suggestion", "")
    return f"Here is your final outfit suggestion:\n\n{suggestion}"

# Create Workflow Graph
workflow = Workflow(
    name="style_concierge_workflow",
    state_schema=StyleState,
    edges=[
        (START, security_checkpoint),
        (security_checkpoint, {"clean": run_orchestration, "SECURITY_EVENT": security_error}),
        (run_orchestration, human_review),
        (human_review, {"approved": final_output, "rejected": run_orchestration})
    ]
)

# App instance
app = App(
    root_agent=workflow,
    name="app"
)
