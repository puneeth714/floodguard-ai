import requests
from typing import Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext
from app.core.config import settings

def get_weather_telemetry(
    latitude: float, 
    longitude: float, 
    use_mock: bool = False, 
    mock_precipitation: Optional[float] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """
    Fetches real-time precipitation metrics from the Open-Meteo API,
    or returns mock telemetry overrides if requested.
    
    Args:
        latitude: Target latitude coordinate.
        longitude: Target longitude coordinate.
        use_mock: If True, uses mock overrides.
        mock_precipitation: Value in mm/hr to return as override.
        tool_context: Optional ADK ToolContext to store result in session state.
        
    Returns:
        Dictionary containing precipitation rate and description.
    """
    # Helper nested function to save and return
    def _save_and_return(res: Dict[str, Any]) -> Dict[str, Any]:
        if tool_context is not None:
            tool_context.state["weather_data"] = res
        return res

    # Check for session state profile overrides
    state_use_mock = False
    state_precip = None
    if tool_context is not None:
        state_use_mock = tool_context.state.get("use_mock", False)
        state_precip = tool_context.state.get("precipitation_mm_hr")

    # 1. Handle mock overrides
    if use_mock or settings.USE_MOCK_TELEMETRY or state_use_mock:
        precipitation = mock_precipitation
        if precipitation is None:
            precipitation = state_precip if state_precip is not None else settings.MOCK_WEATHER_PRECIPITATION
            
        return _save_and_return({
            "source": "mock_override",
            "precipitation_mm_hr": precipitation,
            "status": "Severe Downpour (Simulated)" if precipitation > 20 else "Moderate Rain (Simulated)",
            "forecast_next_2hr": [precipitation * 1.1, precipitation * 0.9]
        })


        
    # 2. Call real Open-Meteo API
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}&current=precipitation&hourly=precipitation"
        )
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Parse current precipitation
        current_precip = data.get("current", {}).get("precipitation", 0.0)
        
        # Parse next two hourly forecasts
        hourly_precip = data.get("hourly", {}).get("precipitation", [])
        forecast = hourly_precip[:2] if len(hourly_precip) >= 2 else [current_precip, current_precip]
        
        status = "Clear"
        if current_precip > 20.0:
            status = "Severe Downpour"
        elif current_precip > 5.0:
            status = "Moderate Rain"
        elif current_precip > 0.0:
            status = "Light Drizzle"
            
        return _save_and_return({
            "source": "open_meteo_api",
            "precipitation_mm_hr": float(current_precip),
            "status": status,
            "forecast_next_2hr": [float(p) for p in forecast]
        })
    except Exception as e:
        # Fallback to safe default if network fails
        print(f"Weather API error (falling back to clear default): {e}")
        return _save_and_return({
            "source": "fallback_default",
            "precipitation_mm_hr": 0.0,
            "status": "Clear (Fallback)",
            "forecast_next_2hr": [0.0, 0.0]
        })

