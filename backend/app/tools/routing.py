import os
import requests
import urllib.parse
import polyline
from typing import Dict, Any, List
from shapely.geometry import LineString, Polygon
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

# Hardcoded active flood polygons for HSR / Silk Board (Fallback if BigQuery not active)
SILK_BOARD_FLOOD_POLYGON = Polygon([
    (12.9160, 77.6210),
    (12.9200, 77.6210),
    (12.9200, 77.6260),
    (12.9160, 77.6260),
    (12.9160, 77.6210)  # Close the polygon
])

BELLANDUR_FLOOD_POLYGON = Polygon([
    (12.9280, 77.6700),
    (12.9360, 77.6700),
    (12.9360, 77.6800),
    (12.9280, 77.6800),
    (12.9280, 77.6700)
])

# Safe detour waypoint in HSR Sector 2 (elevated dry zone: 12.9340, 77.6320)
SAFE_DETOUR_WAYPOINT = "12.9340,77.6320"

def calculate_safe_route(
    origin: str, 
    destination: str, 
    travel_mode: str = "driving", 
    use_mock: bool = False
) -> Dict[str, Any]:
    """
    Computes route alternatives from origin to destination, decodes polylines, 
    checks intersections against flood polygons using Shapely, and returns a safe waypoint-guided route.
    
    Args:
        origin: Start address or "lat,lng" string.
        destination: End address or "lat,lng" string.
        travel_mode: Mode of travel ('driving', 'walking', etc.)
        use_mock: If True, returns mock detour response.
        
    Returns:
        Dict containing route safety report, polylines, and the universal navigation link.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # 1. Handle mock scenario or missing API key
    if use_mock or not api_key:
        print("Using mock route generator (API Key missing or mock mode active).")
        # Simulate Rajesh HSR to Airport detour
        return {
            "source": "mock_route_generator",
            "routes": [
                {
                    "route_index": 0,
                    "summary": "Via Outer Ring Road (Flooded)",
                    "is_safe": False,
                    "flood_intersections": ["Silk Board Basin"],
                    "google_maps_link": None
                },
                {
                    "route_index": 1,
                    "summary": "Via Sector 2 Flyover (Safe - Detour Injected)",
                    "is_safe": True,
                    "flood_intersections": [],
                    "google_maps_link": (
                        f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}"
                        f"&destination={urllib.parse.quote(destination)}"
                        f"&waypoints={SAFE_DETOUR_WAYPOINT}&travelmode={travel_mode}"
                    )
                }
            ]
        }

    # 2. Call Google Maps Directions API to fetch route options
    try:
        url = (
            f"https://maps.googleapis.com/maps/api/directions/json?"
            f"origin={urllib.parse.quote(origin)}&destination={urllib.parse.quote(destination)}"
            f"&alternatives=true&mode={travel_mode}&key={api_key}"
        )
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "OK":
            raise Exception(f"Google Maps Directions API error: {data.get('status')}")
            
        routes_report = []
        any_safe_route = False
        primary_safe_url = None
        
        for idx, route in enumerate(data.get("routes", [])):
            encoded_poly = route.get("overview_polyline", {}).get("points", "")
            summary = route.get("summary", f"Alternative Route {idx + 1}")
            
            # Decode polyline points into coordinates
            decoded_points = polyline.decode(encoded_poly)
            
            # Perform Shapely intersection checks
            # Note: polyline returns (lat, lng), which matches shapely coordinates
            route_line = LineString(decoded_points)
            
            blocked_by = []
            if route_line.intersects(SILK_BOARD_FLOOD_POLYGON):
                blocked_by.append("Silk Board Inundation Zone")
            if route_line.intersects(BELLANDUR_FLOOD_POLYGON):
                blocked_by.append("Bellandur Corridor")
                
            is_safe = len(blocked_by) == 0
            
            nav_link = None
            if is_safe:
                any_safe_route = True
                nav_link = (
                    f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}"
                    f"&destination={urllib.parse.quote(destination)}&travelmode={travel_mode}"
                )
                if not primary_safe_url:
                    primary_safe_url = nav_link
                    
            routes_report.append({
                "route_index": idx,
                "summary": summary,
                "is_safe": is_safe,
                "flood_intersections": blocked_by,
                "google_maps_link": nav_link
            })
            
        # 3. Waypoint Injection: If all standard routes are blocked, calculate detour
        if not any_safe_route and routes_report:
            print("All paths blocked. Injecting safe waypoint detour...")
            detour_url = (
                f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}"
                f"&destination={urllib.parse.quote(destination)}"
                f"&waypoints={SAFE_DETOUR_WAYPOINT}&travelmode={travel_mode}"
            )
            # Add detour route entry
            routes_report.append({
                "route_index": len(routes_report),
                "summary": "Detour via Sector 2 Elevated Flyover (Safe)",
                "is_safe": True,
                "flood_intersections": [],
                "google_maps_link": detour_url
            })
            
        return {
            "source": "google_directions_api",
            "routes": routes_report
        }
        
    except Exception as e:
        print(f"Routing calculation error (falling back to mock): {e}")
        # Fallback to mock URL
        return {
            "source": "fallback_mock_generator",
            "routes": [
                {
                    "route_index": 0,
                    "summary": "Via Sector 2 Flyover (Safe - Detour Injected)",
                    "is_safe": True,
                    "flood_intersections": [],
                    "google_maps_link": (
                        f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}"
                        f"&destination={urllib.parse.quote(destination)}"
                        f"&waypoints={SAFE_DETOUR_WAYPOINT}&travelmode={travel_mode}"
                    )
                }
            ]
        }
