import sys
import os
import xml.etree.ElementTree as ET
import math

# Add backend to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.bigquery_client import BigQueryClientWrapper

def parse_kml(kml_path: str):
    """
    Parses the low-lying locations KML file and extracts the placemarks.
    """
    print(f"Reading and parsing KML file: {kml_path}")
    tree = ET.parse(kml_path)
    root = tree.getroot()
    
    # Standard KML namespace
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    placemarks = root.findall('.//kml:Placemark', ns)
    hotspots = []
    
    for idx, pm in enumerate(placemarks):
        name_elem = pm.find('kml:name', ns)
        name = name_elem.text.strip() if name_elem is not None else f"Unnamed Hotspot {idx + 1}"
        
        # ExtendedData for OBJECTID
        object_id = idx + 1
        simple_data = pm.find('.//kml:SimpleData[@name="OBJECTID"]', ns)
        if simple_data is not None and simple_data.text:
            try:
                object_id = int(float(simple_data.text))
            except ValueError:
                pass
                
        # Get coordinates
        coords_elem = pm.find('.//kml:coordinates', ns)
        if coords_elem is not None and coords_elem.text:
            coords_str = coords_elem.text.strip()
            # KML coordinates are longitude,latitude,altitude
            parts = coords_str.split(',')
            if len(parts) >= 2:
                try:
                    lng = float(parts[0])
                    lat = float(parts[1])
                    if math.isnan(lng) or math.isnan(lat):
                        print(f"Skipping coordinate parsing for placemark {name} (contains NaN).")
                        continue
                    hotspots.append({
                        "name": name,
                        "lat": lat,
                        "lng": lng,
                        "object_id": object_id
                    })
                except ValueError:
                    print(f"Skipping coordinate parsing for placemark {name} (invalid float conversion).")
                    
    return hotspots

def seed_kml_data():
    kml_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "docs", "guidelines", "8e87a2fc-e014-4c6e-81f1-d5cb4db57a46.kml"
    )
    
    if not os.path.exists(kml_file_path):
        print(f"Error: KML file not found at {kml_file_path}")
        return
        
    hotspots = parse_kml(kml_file_path)
    print(f"Parsed {len(hotspots)} active hotspots from KML.")
    
    if not hotspots:
        print("No valid coordinates parsed. Aborting database ingestion.")
        return
        
    print("Connecting to BigQuery...")
    bq_wrapper = BigQueryClientWrapper()
    
    # Initialize tables (to ensure low_lying_hotspots exists)
    bq_wrapper.init_tables()
    
    # Clear old entries
    print("Clearing old low-lying hotspots...")
    dataset = bq_wrapper.dataset_ref
    bq_wrapper.client.query(f"DELETE FROM `{dataset}.low_lying_hotspots` WHERE TRUE").result()
    
    # Batch insertion (split into chunks of 100 rows to prevent payload limit warnings)
    print("Uploading hotspots to BigQuery...")
    chunk_size = 100
    for i in range(0, len(hotspots), chunk_size):
        chunk = hotspots[i:i + chunk_size]
        bq_wrapper.insert_rows("low_lying_hotspots", chunk)
        print(f"Uploaded hotspots {i + 1} to {min(i + chunk_size, len(hotspots))}...")
        
    print("--- Low-Lying Hotspots Ingestion Completed Successfully ---")

if __name__ == "__main__":
    seed_kml_data()
