from mcp.server.fastmcp import FastMCP

mcp = FastMCP("style-concierge-mcp")

@mcp.tool()
def get_weather(location: str) -> str:
    """Get the current weather forecast for a location.
    
    Args:
        location: The city or location name.
    """
    loc = location.lower()
    if "new york" in loc or "ny" in loc:
        return "Temp: 65°F (18°C), Rain showers, high humidity (85%), wind 10mph."
    elif "london" in loc:
        return "Temp: 55°F (13°C), Overcast, cool breezes, 40% chance of light drizzle."
    elif "tokyo" in loc:
        return "Temp: 72°F (22°C), Clear skies, sunny, low humidity."
    elif "san francisco" in loc or "sf" in loc:
        return "Temp: 60°F (15°C), Foggy morning clearing to partial sun, cool ocean wind."
    return "Temp: 70°F (21°C), Mild temperature, partly cloudy, gentle breeze."

@mcp.tool()
def get_style_tips(style_preference: str) -> str:
    """Retrieve style and outfit layering tips for a given preference.
    
    Args:
        style_preference: The preference type (e.g., casual, business, formal, smart-casual).
    """
    pref = style_preference.lower()
    if "business" in pref or "formal" in pref:
        return (
            "1. Focus on structured tailoring (blazers, dress pants, pencil skirts).\n"
            "2. Keep colors conservative: navy, charcoal, black, and white.\n"
            "3. Closed-toe shoes (oxfords, loafers, or pumps) are recommended.\n"
            "4. Minimize accessories to elegant, simple pieces (watches, studs)."
        )
    elif "casual" in pref:
        return (
            "1. Prioritize comfort with high-quality basics (breathable cotton tees, clean denim, knitwear).\n"
            "2. Layer with a denim jacket or light cardigan for depth.\n"
            "3. Wear clean, minimalist sneakers or casual boots.\n"
            "4. Play with texture and relaxed silhouettes."
        )
    return (
        "1. Combine structured and unstructured elements (e.g., blazers with clean dark jeans).\n"
        "2. Choose high-quality materials like merino wool, linen, or fine cotton.\n"
        "3. Footwear should be clean and neat: loafers, chelsea boots, or minimalist white sneakers.\n"
        "4. Neutral tones mixed with one accent color work best."
    )

@mcp.tool()
def get_color_palette(vibe: str) -> str:
    """Suggest a harmonized color palette based on the desired style vibe.
    
    Args:
        vibe: The style vibe or aesthetic (e.g., minimalist, earth-tones, vibrant, pastel).
    """
    v = vibe.lower()
    if "minimalist" in v or "monochromatic" in v:
        return "Palette: Charcoal, Slate Grey, Crisp White, and Jet Black. Accent: Soft Cream."
    elif "earth" in v or "warm" in v:
        return "Palette: Olive Green, Mustard Yellow, Terracotta, and Warm Beige. Accent: Chocolate Brown."
    elif "pastel" in v or "light" in v:
        return "Palette: Lavender, Dusty Rose, Mint Green, and Creamy White. Accent: Soft Gold."
    elif "vibrant" in v or "bold" in v:
        return "Palette: Royal Blue, Emerald Green, Mustard Yellow, and Ruby Red. Accent: Black."
    return "Palette: Navy Blue, Heather Grey, Olive Green, and Off-White. Accent: Tan Leather."

@mcp.tool()
def get_wardrobe_basics(category: str) -> str:
    """List must-have wardrobe basics for different outfit categories.
    
    Args:
        category: The category (e.g., tops, bottoms, outerwear, shoes).
    """
    cat = category.lower()
    if "top" in cat:
        return "Basics: Plain white t-shirt, light blue button-down shirt, neutral crewneck sweater, black turtleneck."
    elif "bottom" in cat:
        return "Basics: Dark-wash slim denim, beige chinos, tailored black trousers, pleated midi-skirt."
    elif "outer" in cat:
        return "Basics: Camel trench coat, navy wool overcoat, versatile leather jacket, unstructured blazer."
    elif "shoe" in cat:
        return "Basics: Minimalist white leather sneakers, brown leather loafers, black ankle boots, classic dress shoes."
    return "Basics: Unstructured blazer, clean white leather sneakers, dark slim denim, white button-down shirt."

if __name__ == "__main__":
    mcp.run()
