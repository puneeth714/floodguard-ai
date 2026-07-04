import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

def geocode_place(place_name: str) -> Dict[str, Any]:
    """
    Resolves a textual place name (e.g., 'Koramangala', 'Hebbal', or 'Prestige St Johns Apartment')
    into geographical coordinates using the Google Maps Geocoding API.
    
    Args:
        place_name: The textual search term for the place.
        
    Returns:
        Dict containing lat, lng, formatted_address, and place_id.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        # Fallback coordinates for Bangalore center
        return {
            "source": "fallback_ Bangalore_center",
            "lat": 12.9716,
            "lng": 77.5946,
            "formatted_address": "Bengaluru, Karnataka, India",
            "place_id": "ChIJc2EYO7QWrjsR5t7HM5lZ4t0"
        }
        
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(place_name)}&key={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            loc = result["geometry"]["location"]
            return {
                "source": "google_geocoding_api",
                "lat": float(loc["lat"]),
                "lng": float(loc["lng"]),
                "formatted_address": result.get("formatted_address"),
                "place_id": result.get("place_id")
            }
        else:
            print(f"Geocoding API status returned non-OK: {data.get('status')}")
    except Exception as e:
        print(f"Geocoding error: {e}")
        
    # Standard Bangalore center fallback
    return {
        "source": "fallback_error",
        "lat": 12.9716,
        "lng": 77.5946,
        "formatted_address": "Bengaluru, Karnataka, India (Fallback)",
        "place_id": "ChIJc2EYO7QWrjsR5t7HM5lZ4t0"
    }

def get_place_photo_references(place_id: str) -> List[Dict[str, Any]]:
    """
    Queries Google Place Details API to fetch metadata and photo references for a place,
    allowing us to inspect the physical structures (ramps, gates, elevations).
    
    Args:
        place_id: The unique Google Place ID.
        
    Returns:
        List of dictionaries containing photo_reference hashes, width, and height.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key or not place_id:
        return []
        
    try:
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,photos,geometry&key={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and "result" in data:
            photos_data = data["result"].get("photos", [])
            photos_list = []
            for p in photos_data[:3]:  # Limit to top 3 photos for analysis
                photos_list.append({
                    "photo_reference": p["photo_reference"],
                    "width": p.get("width"),
                    "height": p.get("height")
                })
            return photos_list
    except Exception as e:
        print(f"Place Details API photo fetch error: {e}")
        
    return []

def download_place_photo(photo_reference: str, max_width: int = 600) -> Optional[bytes]:
    """
    Downloads the actual binary photo bytes from Google Places Photo API using a reference hash.
    These photo bytes are passed directly to Gemini Vision to inspect for flood risks.
    
    Args:
        photo_reference: The Google Photo reference hash.
        max_width: Limit image width to reduce token size.
        
    Returns:
        Binary bytes of the image, or None if download fails.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key or not photo_reference:
        return None
        
    try:
        url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={api_key}"
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading place photo: {e}")
        
    return None
