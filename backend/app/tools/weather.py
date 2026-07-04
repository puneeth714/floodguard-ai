import requests
from typing import Dict, Any, Optional

def get_weather_telemetry(
    latitude: float, 
    longitude: float, 
    use_mock: bool = False, 
    mock_precipitation: Optional[float] = None
) -> Dict[str, Any]:
    """
    Fetches real-time precipitation metrics from the Open-Meteo API,
    or returns mock telemetry overrides if requested.
    
    Args:
        latitude: Target latitude coordinate.
        longitude: Target longitude coordinate.
        use_mock: If True, uses mock overrides.
        mock_precipitation: Value in mm/hr to return as override.
        
    Returns:
        Dictionary containing precipitation rate and description.
    """
    # 1. Handle mock overrides
    if use_mock:
        precipitation = mock_precipitation if mock_precipitation is not None else 45.0
        return {
            "source": "mock_override",
            "precipitation_mm_hr": precipitation,
            "status": "Severe Downpour (Simulated)" if precipitation > 20 else "Moderate Rain (Simulated)",
            "forecast_next_2hr": [precipitation * 1.1, precipitation * 0.9]
        }
        
    # 2. Call real Open-Meteo API
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}&current=precipitation&hourly=precipitation"
        )
        response = requests.get(url, timeout=5)
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
            
        return {
            "source": "open_meteo_api",
            "precipitation_mm_hr": float(current_precip),
            "status": status,
            "forecast_next_2hr": [float(p) for p in forecast]
        }
    except Exception as e:
        # Fallback to safe default if network fails
        print(f"Weather API error (falling back to clear default): {e}")
        return {
            "source": "fallback_default",
            "precipitation_mm_hr": 0.0,
            "status": "Clear (Fallback)",
            "forecast_next_2hr": [0.0, 0.0]
        }
