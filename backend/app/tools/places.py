import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

def geocode_place(place_name: str, use_mock: bool = False) -> Dict[str, Any]:
    """
    Resolves a textual place name into geographical coordinates.
    """
    if use_mock:
        return {
            "source": "mock_override",
            "lat": 12.9279,
            "lng": 77.6271,
            "formatted_address": "HSR Layout Sector 4, Bengaluru, Karnataka, India (Simulated)",
            "place_id": "ChIJc2EYO7QWrjsR5t7HM5lZ4t0"
        }

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "source": "fallback_Bangalore_center",
            "lat": 12.9716,
            "lng": 77.5946,
            "formatted_address": "Bengaluru, Karnataka, India (No Key)",
            "place_id": "ChIJc2EYO7QWrjsR5t7HM5lZ4t0"
        }
        
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(place_name)}&key={api_key}"
        response = requests.get(url, timeout=15)
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
    except Exception as e:
        print(f"Geocoding error: {e}")
        
    return {
        "source": "fallback_error",
        "lat": 12.9716,
        "lng": 77.5946,
        "formatted_address": "Bengaluru, Karnataka, India (Fallback)",
        "place_id": "ChIJc2EYO7QWrjsR5t7HM5lZ4t0"
    }

def get_place_photo_references(place_id: str, use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Queries Google Place Details API to fetch photo references for a place.
    """
    if use_mock or not place_id:
        return [{"photo_reference": "mock_photo_ref_1", "width": 600, "height": 400}]

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return []
        
    try:
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,photos,geometry&key={api_key}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and "result" in data:
            photos_data = data["result"].get("photos", [])
            photos_list = []
            for p in photos_data[:3]:
                photos_list.append({
                    "photo_reference": p["photo_reference"],
                    "width": p.get("width"),
                    "height": p.get("height")
                })
            return photos_list
    except Exception as e:
        print(f"Place Details API photo fetch error: {e}")
        
    return []

def get_nearby_places_photos(
    lat: float, 
    lng: float, 
    radius_meters: int = 100, 
    use_mock: bool = False
) -> List[Dict[str, Any]]:
    """
    Searches for nearby points of interest within X meters of user coordinates
    and retrieves structural building photo references for risk inspections.
    
    Args:
        lat: User latitude.
        lng: User longitude.
        radius_meters: Proximity radius (defaults to 100 meters).
        use_mock: If True, returns mock photo reference hashes.
        
    Returns:
        List of photo references.
    """
    if use_mock:
        return [
            {"name": "Mock Apartment Society", "photo_reference": "mock_nearby_ref_1", "distance_m": 45},
            {"name": "Mock Commercial Gate", "photo_reference": "mock_nearby_ref_2", "distance_m": 80}
        ]

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return []
        
    try:
        # Google Places Nearby Search URL
        url = (
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
            f"location={lat},{lng}&radius={radius_meters}&key={api_key}"
        )
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        photo_results = []
        if data.get("status") == "OK" and "results" in data:
            for place in data["results"][:5]:  # Process top 5 closest places
                place_name = place.get("name", "Unknown Place")
                photos = place.get("photos", [])
                
                # Check if place has photos
                if photos:
                    photo_results.append({
                        "name": place_name,
                        "photo_reference": photos[0]["photo_reference"],
                        "place_id": place.get("place_id")
                    })
            return photo_results
        else:
            print(f"Nearby Search API returned non-OK status: {data.get('status')}")
    except Exception as e:
        print(f"Nearby places photo query failed: {e}")
        
    return []

def download_place_photo(photo_reference: str, max_width: int = 600, use_mock: bool = False) -> Optional[bytes]:
    """
    Downloads raw binary bytes of a place photo.
    """
    if use_mock or photo_reference.startswith("mock_"):
        # Return a tiny 1x1 mock transparent GIF bytes
        return b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return None
        
    try:
        url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={api_key}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading place photo: {e}")
        
    return None
