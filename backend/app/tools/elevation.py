import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext
from app.core.config import settings

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

def get_elevation_profile(
    latitude: float, 
    longitude: float, 
    use_mock: bool = False, 
    mock_altitude: Optional[float] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """
    Fetches terrain elevation from the Google Maps Elevation API,
    or falls back to mock values and localized cache parameters.
    
    Args:
        latitude: Target latitude coordinate.
        longitude: Target longitude coordinate.
        use_mock: If True, returns mock overrides.
        mock_altitude: Value in meters to return as override.
        tool_context: Optional ADK ToolContext to store result in session state.
        
    Returns:
        Dictionary containing elevation in meters and slope assessment.
    """
    def _save_and_return(res: Dict[str, Any]) -> Dict[str, Any]:
        if tool_context is not None:
            tool_context.state["elevation_data"] = res
        return res

    # Check for session state profile overrides
    state_use_mock = False
    state_alt = None
    if tool_context is not None:
        state_use_mock = tool_context.state.get("use_mock", False)
        state_alt = tool_context.state.get("elevation_altitude")

    # 1. Handle mock overrides
    if use_mock or settings.USE_MOCK_TELEMETRY or state_use_mock:
        alt = mock_altitude
        if alt is None:
            alt = state_alt if state_alt is not None else settings.MOCK_ELEVATION_ALTITUDE
            
        return _save_and_return({
            "source": "mock_override",
            "elevation_m": alt,
            "relative_sink_depth": 864.0 - alt if alt < 864.0 else 0.0,
            "slope_percent": 0.2
        })


    # 2. Localized HSR Layout Basin Cache Check
    # HSR Sector 4 Center: 12.9279, 77.6271
    dist_to_hsr_center = ((latitude - 12.9279)**2 + (longitude - 77.6271)**2)**0.5
    if dist_to_hsr_center < 0.005:
        # Known low-lying basin
        print("Coordinate matches HSR Layout basin, returning cached coordinates.")
        return _save_and_return({
            "source": "local_sink_cache",
            "elevation_m": 858.0,
            "relative_sink_depth": 6.0,
            "slope_percent": 0.2
        })

    # 3. Call Google Maps Elevation API
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if api_key:
        try:
            url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={latitude},{longitude}&key={api_key}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                elev = data["results"][0]["elevation"]
                return _save_and_return({
                    "source": "google_elevation_api",
                    "elevation_m": float(elev),
                    "relative_sink_depth": 864.0 - elev if elev < 864.0 else 0.0,
                    # Simple mock slope calculation based on HSR ward flat profile
                    "slope_percent": 1.5 if elev >= 864.0 else 0.3
                })
            else:
                print(f"Google Maps Elevation API returned non-OK status: {data.get('status')}")
        except Exception as e:
            print(f"Google Maps Elevation API network error: {e}")

    # 4. Fallback Default (Standard Bengaluru average elevation)
    return _save_and_return({
        "source": "fallback_default",
        "elevation_m": 864.0,
        "relative_sink_depth": 0.0,
        "slope_percent": 1.5
    })

