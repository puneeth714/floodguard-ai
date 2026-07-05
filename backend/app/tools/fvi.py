from google.adk.tools.tool_context import ToolContext

def calculate_flood_vulnerability_index(tool_context: ToolContext) -> dict:
    """
    Calculates the Flood Vulnerability Index (FVI) using current weather 
    and elevation properties stored in session state.
    
    Formula:
        V = (w_elev * rel_sink) + (w_slope * slope) + (w_rain * rain) + (w_drain * D)
    """
    elev = tool_context.state.get("elevation_data", {})
    weather = tool_context.state.get("weather_data", {})
    
    rel_sink = elev.get("relative_sink_depth", 0.0)
    slope = elev.get("slope_percent", 0.0)
    rain = weather.get("precipitation_mm_hr", 0.0)
    
    dist_penalty = 50.0 if rel_sink > 2.0 else 10.0
    fvi = (0.35 * rel_sink) + (0.15 * max(0.0, 3.0 - slope)) + (0.30 * rain) + (0.20 * dist_penalty)
    fvi = min(100.0, max(0.0, fvi))
    
    tool_context.state["flood_risk_score"] = fvi
    return {"flood_risk_score": fvi}
