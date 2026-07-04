import sys
import os
import random
import datetime

# Add backend to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.bigquery_client import BigQueryClientWrapper

def generate_mock_grids():
    """Generates 50+ grid coordinates around HSR Layout, Bengaluru."""
    grids = []
    # HSR Layout Center: Lat 12.9279, Lng 77.6271
    center_lat, center_lng = 12.9279, 77.6271
    
    # Generate a grid pattern of 8x8 points
    for i in range(-4, 4):
        for j in range(-4, 4):
            lat = center_lat + (i * 0.002)
            lng = center_lng + (j * 0.002)
            
            # Base values
            altitude = 864.0 + random.uniform(-1.0, 1.0)
            slope = random.uniform(1.0, 3.0)
            drainage_capacity = random.uniform(70.0, 95.0)
            
            # Make HSR Sector 4 a topographical basin (low elevation, flat slope, lower drainage)
            # Center of the basin around Rajesh's coordinates
            dist_to_center = ((lat - center_lat)**2 + (lng - center_lng)**2)**0.5
            if dist_to_center < 0.005:
                # Topographical sink
                altitude = 858.0 + random.uniform(-0.5, 0.5)
                slope = random.uniform(0.1, 0.5)
                drainage_capacity = random.uniform(40.0, 60.0)
                
            grids.append({
                "lat": float(lat),
                "lng": float(lng),
                "altitude": float(altitude),
                "slope": float(slope),
                "drainage_capacity": float(drainage_capacity),
                "fvi": None  # Will be calculated dynamically
            })
            
    # Explicitly ensure Rajesh and Radha coordinates are in the dataset
    grids.append({
        "lat": 12.9279,
        "lng": 77.6271,
        "altitude": 858.0,
        "slope": 0.2,
        "drainage_capacity": 50.0,
        "fvi": None
    })
    grids.append({
        "lat": 12.9312,
        "lng": 77.6254,
        "altitude": 858.5,
        "slope": 0.3,
        "drainage_capacity": 45.0,
        "fvi": None
    })
    return grids

def generate_mock_drains():
    """Generates mock stormwater drains around HSR Layout."""
    return [
        {"drain_id": "HSR-D01", "name": "Sector 4 Primary Main Drain", "lat": 12.9250, "lng": 77.6240, "status": "cleared"},
        {"drain_id": "HSR-D02", "name": "Sector 4 Secondary Drain A", "lat": 12.9280, "lng": 77.6260, "status": "blocked"}, # Rajesh near
        {"drain_id": "HSR-D03", "name": "Sector 3 Collector Sewer", "lat": 12.9300, "lng": 77.6250, "status": "blocked"},  # Radha near
        {"drain_id": "HSR-D04", "name": "Silk Board Junction Storm Drain", "lat": 12.9180, "lng": 77.6230, "status": "cleared"},
        {"drain_id": "HSR-D05", "name": "Sector 2 High-Capacity Culvert", "lat": 12.9340, "lng": 77.6320, "status": "cleared"},
    ]

def generate_mock_guidelines():
    """Generates mock PDF chunks and 768-dimensional embeddings for RAG tests."""
    chunks = [
        {
            "chunk_id": "chunk_01",
            "doc_name": "BBMP_Flood_Mitigation_Plan_2026.pdf",
            "page_num": 14,
            "content": (
                "For HSR Layout Sector 4: The BBMP flood mitigation guidelines require immediate "
                "desilting of secondary stormwater drains HSR-D02 and HSR-D03 before monsoons. "
                "In case of waterlogging, mobile water pumps must be deployed at coordinates "
                "(12.9279, 77.6271) to route overflow towards the Sector 2 elevated culverts."
            )
        },
        {
            "chunk_id": "chunk_02",
            "doc_name": "KSDMP_Disaster_Protocol_v3.pdf",
            "page_num": 42,
            "content": (
                "Karnataka State Disaster Management Plan (KSDMP) Evacuation Protocol: When flood depth "
                "exceeds 1.5 feet, citizens must be instructed to shut off ground-level primary electrical "
                "breakers, move two-wheelers and vehicles to elevated roads (above 864m), and gather "
                "at assembly points. The primary safe spot in HSR Layout is the Sector 2 Community Hall."
            )
        },
        {
            "chunk_id": "chunk_03",
            "doc_name": "BBMP_Local_Recovery_Claims.pdf",
            "page_num": 5,
            "content": (
                "Post-Flood Insurance & Compensation Claims: To file claims for property damage due to "
                "monsoonal stagnation, residents must document the water level using visual photographs "
                "of submergence, noting tire markers or doorway levels. BBMP is required to clear water "
                "logging within 6 hours of rain cessation."
            )
        }
    ]
    
    # Generate random 768-dimensional float arrays for embeddings
    for chunk in chunks:
        # Generate stable pseudo-random embeddings so search is testable
        random.seed(hash(chunk["chunk_id"]))
        chunk["embedding"] = [random.uniform(-0.1, 0.1) for _ in range(768)]
        
    return chunks

def seed_data():
    print("Connecting to BigQuery...")
    bq_wrapper = BigQueryClientWrapper()
    
    print("Initializing table schemas...")
    bq_wrapper.init_tables()
    
    # Clean old data to avoid duplicates during re-runs
    print("Clearing existing data...")
    dataset = bq_wrapper.dataset_ref
    bq_wrapper.client.query(f"DELETE FROM `{dataset}.vulnerability_grids` WHERE TRUE").result()
    bq_wrapper.client.query(f"DELETE FROM `{dataset}.drainage_network` WHERE TRUE").result()
    bq_wrapper.client.query(f"DELETE FROM `{dataset}.guidelines_vector` WHERE TRUE").result()
    
    print("Seeding vulnerability_grids...")
    grids = generate_mock_grids()
    bq_wrapper.insert_rows("vulnerability_grids", grids)
    print(f"Successfully seeded {len(grids)} vulnerability grids.")
    
    print("Seeding drainage_network...")
    drains = generate_mock_drains()
    bq_wrapper.insert_rows("drainage_network", drains)
    print(f"Successfully seeded {len(drains)} drainage nodes.")
    
    print("Seeding guidelines_vector...")
    guidelines = generate_mock_guidelines()
    bq_wrapper.insert_rows("guidelines_vector", guidelines)
    print(f"Successfully seeded {len(guidelines)} RAG guidelines.")
    
    print("--- BigQuery Seeding Completed Successfully ---")

if __name__ == "__main__":
    seed_data()
