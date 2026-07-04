import os
import sys
import urllib.parse
import requests
import polyline
from shapely.geometry import LineString, Polygon
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

def get_palace_road_detour():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("API Key missing.")
        return
        
    origin = "Koramangala, Bengaluru"
    destination = "Hebbal, Bengaluru"
    
    # Coordinates boundary representing the flooded Palace Road / Bengaluru Palace zone
    # Near Vasanth Nagar / Cunningham Road / Palace Cross Road
    palace_road_flood_zone = Polygon([
        (12.9850, 77.5800),
        (12.9990, 77.5800),
        (12.9990, 77.5920),
        (12.9850, 77.5920),
        (12.9850, 77.5800)
    ])
    
    # Safe East detour via Benson Town / Jayamahal Road: 13.0030, 77.6030
    safe_waypoint = "13.0030,77.6030" 
    
    print(f"Querying Directions from {origin} to {destination}...")
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={urllib.parse.quote(origin)}&destination={urllib.parse.quote(destination)}"
        f"&alternatives=true&mode=driving&key={api_key}"
    )
    response = requests.get(url)
    data = response.json()
    
    if data.get("status") != "OK":
        print("Error fetching directions.")
        return
        
    routes = data.get("routes", [])
    print(f"Directions API returned {len(routes)} routes.")
    
    for idx, r in enumerate(routes):
        summary = r.get("summary", f"Alternative {idx+1}")
        encoded_poly = r.get("overview_polyline", {}).get("points", "")
        points = polyline.decode(encoded_poly)
        route_line = LineString(points)
        
        # Check collision with Palace Road flooded zone
        intersects = route_line.intersects(palace_road_flood_zone)
        
        # Extract road names
        roads = set()
        for step in r.get("legs", [{}])[0].get("steps", []):
            clean_instr = step.get("html_instructions", "")
            import re
            clean_instr = re.sub(r'<[^>]+>', ' ', clean_instr)
            m = re.search(r'\b(?:Rd|Road|Highway|NH\s?\d+|Palace|Jayamahal|Bellary)\b', clean_instr)
            if m:
                roads.add(m.group(0).strip())
                
        roads_str = ", ".join(list(roads)[:3])
        
        if intersects:
            print(f"\n❌ Route {idx+1}: via {summary} ({roads_str}) -- BLOCKED")
            print("  Reason: Route passes through Vasanth Nagar / Palace Road flood zone.")
            # Construct detour link
            detour_url = (
                f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}"
                f"&destination={urllib.parse.quote(destination)}&waypoints={safe_waypoint}&travelmode=driving"
            )
            print(f"  Detour Link: {detour_url}")
        else:
            print(f"\n🟢 Route {idx+1}: via {summary} ({roads_str}) -- SAFE")
            print(f"  Link: https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}&destination={urllib.parse.quote(destination)}")

if __name__ == "__main__":
    get_palace_road_detour()
