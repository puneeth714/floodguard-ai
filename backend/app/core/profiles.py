from typing import Optional, Dict, Any

TEST_PROFILES: Dict[str, Dict[str, Any]] = {
    "rajesh": {
        "name": "Rajesh (HSR Layout Sector 4)",
        "role": "resident",
        "latitude": 12.9279,
        "longitude": 77.6271,
        "destination": "13.1986,77.7066",  # Airport
        "elevation_altitude": 858.0,       # Low-lying basin
        "precipitation_mm_hr": 45.0,        # Severe downpour
        "use_mock": True
    },
    "radha": {
        "name": "Radha (HSR Layout Sector 2)",
        "role": "resident",
        "latitude": 12.9340,
        "longitude": 77.6320,               # Elevated high-ground area
        "destination": "13.1986,77.7066",  # Airport
        "elevation_altitude": 864.0,       # Normal high-ground
        "precipitation_mm_hr": 12.0,        # Moderate rain
        "use_mock": True
    },
    "anonymous": {
        "name": "Anonymous User",
        "role": "resident",
        "latitude": 12.9716,                # Default Central Bengaluru
        "longitude": 77.5946,
        "destination": None,
        "elevation_altitude": 920.0,
        "precipitation_mm_hr": 0.0,         # Clear weather
        "use_mock": True
    }
}
