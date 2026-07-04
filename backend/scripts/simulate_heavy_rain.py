import os
import sys
import urllib.parse
import polyline
import requests
from shapely.geometry import LineString, Point
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.bigquery_client import BigQueryClientWrapper
from app.tools.weather import get_weather_telemetry

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

def run_heavy_rain_routing(origin: str, destination: str, simulated_rain_rate: float):
    """
    Simulates a route query under heavy rain conditions.
    1. Fetches current weather override.
    2. Queries live Google Maps Directions API for route options.
    3. Fetches real KML low-lying hotspots from BigQuery.
    4. Evaluates which route segments are blocked by active flood hotspots.
    5. Returns detailed road explanations, safety assessments, and detour links.
    """
    print(f"\n======================================================================")
    print(f"Simulating heavy rain route search:")
    print(f"  Origin: {origin}")
    print(f"  Destination: {destination}")
    print(f"  Simulated Rain: {simulated_rain_rate} mm/hr")
    print(f"======================================================================")
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY missing in configuration.")
        return
        
    # Initialize BigQuery to get KML low-lying points
    bq_wrapper = BigQueryClientWrapper()
    dataset = bq_wrapper.dataset_ref
    
    print("Fetching municipal low-lying hotspots from BigQuery...")
    hotspots_rows = bq_wrapper.execute_query(f"SELECT name, lat, lng FROM `{dataset}.low_lying_hotspots`")
    print(f"Loaded {len(hotspots_rows)} real municipal hotspots.")
    
    # Under heavy rain (> 15mm/hr), low-lying points become active flood zones (200m buffer)
    active_flood_buffers = []
    if simulated_rain_rate > 15.0:
        for hs in hotspots_rows:
            # We construct a spatial point and buffer it by approx 200m (0.0018 degrees)
            point = Point(hs["lat"], hs["lng"])
            buffer = point.buffer(0.0018)
            active_flood_buffers.append({
                "name": hs["name"],
                "lat": hs["lat"],
                "lng": hs["lng"],
                "geom": buffer
            })
        print(f"Precipitation triggers {len(active_flood_buffers)} active municipal flood zones.")
    else:
        print("Precipitation is light. Flood zones remain inactive.")
        
    # Query Directions API
    print("Querying Google Maps Directions API...")
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={urllib.parse.quote(origin)}&destination={urllib.parse.quote(destination)}"
        f"&alternatives=true&mode=driving&key={api_key}"
    )
    response = requests.get(url)
    data = response.json()
    
    if data.get("status") != "OK":
        print(f"Directions API returned status: {data.get('status')}")
        return
        
    routes = data.get("routes", [])
    print(f"Directions API returned {len(routes)} alternative routes.")
    
    analyzed_routes = []
    any_safe = False
    
    for idx, r in enumerate(routes):
        summary = r.get("summary", f"Route {idx+1}")
        encoded_poly = r.get("overview_polyline", {}).get("points", "")
        decoded_points = polyline.decode(encoded_poly)
        
        # Build Shapely LineString (lat, lng tuples format)
        route_line = LineString(decoded_points)
        
        # Check intersections against active flood points
        collisions = []
        for fb in active_flood_buffers:
            # Check proximity to the route line
            # In degrees, check distance to line (0.0018 deg is approx 200m)
            pt = Point(fb["lat"], fb["lng"])
            dist = route_line.distance(pt)
            if dist < 0.0018:
                collisions.append(fb["name"])
                
        is_safe = len(collisions) == 0
        
        # Parse road steps to extract names for the AI's explanation
        road_names = set()
        steps = r.get("legs", [{}])[0].get("steps", [])
        for step in steps:
            # Look for street names or highway indices in html_instructions (e.g. "Hosur Rd", "NH 44")
            instr = step.get("html_instructions", "")
            # Clean HTML tags
            clean_instr = re.sub(r'<[^>]+>', ' ', instr)
            match = re.search(r'\b(?:Rd|Road|Highway|NH\s?\d+|Outer\s?Ring\s?Rd|Hosur\b)[A-Za-z0-9\s]*', clean_instr)
            if match:
                road_names.add(match.group(0).strip())
                
        roads_taken = ", ".join(list(road_names)[:4])
        
        # Create Google Maps URL
        nav_link = (
            f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}"
            f"&destination={urllib.parse.quote(destination)}"
        )
        if not is_safe:
            nav_link += f"&waypoints=12.9340,77.6320" # Inject Sector 2 Flyover detour to bypass Silk Board/HSR low points
            
        analyzed_routes.append({
            "index": idx,
            "summary": summary,
            "roads": roads_taken,
            "is_safe": is_safe,
            "collisions": list(set(collisions))[:3], # Show top 3 collisions
            "link": nav_link
        })
        if is_safe:
            any_safe = True
            
    # Print detailed report
    print("\n--- SPATIAL FILTERING ROUTING REPORT ---")
    for r in analyzed_routes:
        print(f"\nRoute Option {r['index'] + 1}: via {r['summary']} (Roads: {r['roads']})")
        if r["is_safe"]:
            print("  🟢 STATUS: SAFE PATH")
            print("  🚗 RECOMMENDATION: This path is clear of any active low-lying flood points.")
            print(f"  🔗 Navigation Link: {r['link']}")
        else:
            print("  🔴 STATUS: FLOOD RISK PATH")
            print(f"  ⚠️ COLLISION ZONE: Passes near: {', '.join(r['collisions'])}")
            print(f"  ❌ AVOID THIS PATH: Heavy rain is causing waterlogging risk along {r['summary']}.")
            print("  🔄 DETOUR INJECTED: Detour waypoint coordinates injected to bypass the low points.")
            print(f"  🔗 Detour Navigation Link: {r['link']}")
            
    if not any_safe:
        print("\n🚨 WARNING: All standard routes are impacted by active waterlogging zones. A safe detour flyover has been injected as a waypoint on the navigation links.")

if __name__ == "__main__":
    import re
    # Run simulation from HSR Layout to Hebbal
    # Origin: HSR Layout (12.9279, 77.6271)
    # Destination: Hebbal (13.0354, 77.5988)
    # Simulated Rain: 35.0 mm/hr (Heavy Rain)
    run_heavy_rain_routing(
        origin="12.9279,77.6271",
        destination="13.0354,77.5988",
        simulated_rain_rate=35.0
    )
