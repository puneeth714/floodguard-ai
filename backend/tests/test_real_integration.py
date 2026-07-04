import os
import sys
import unittest
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.bigquery_client import BigQueryClientWrapper
from app.tools.weather import get_weather_telemetry
from app.tools.elevation import get_elevation_profile
from app.tools.routing import calculate_safe_route
from app.tools.simulation import run_what_if_simulation
from google import genai

class TestRealIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Load environment variables
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))
        print("\n=== Initializing Real Integration Test Suite ===")
        cls.bq_client = BigQueryClientWrapper()
        cls.dataset = cls.bq_client.dataset_ref
        print(f"Connected to BigQuery. Target dataset: {cls.dataset}")
        
    def test_1_real_bigquery_connection(self):
        """Test active BigQuery read queries against seeded tables."""
        print("\n--- Test 1: Real BigQuery Table Checks ---")
        
        # Query Low-lying Hotspots count
        hotspot_query = f"SELECT COUNT(*) as count FROM `{self.dataset}.low_lying_hotspots`"
        rows = self.bq_client.execute_query(hotspot_query)
        self.assertTrue(len(rows) > 0)
        hotspot_count = rows[0]["count"]
        print(f"Verified Table: low_lying_hotspots. Row count: {hotspot_count}")
        self.assertTrue(hotspot_count > 100) # We seeded 128
        
        # Query Drainage nodes count
        drain_query = f"SELECT COUNT(*) as count FROM `{self.dataset}.drainage_network`"
        d_rows = self.bq_client.execute_query(drain_query)
        self.assertTrue(len(d_rows) > 0)
        drain_count = d_rows[0]["count"]
        print(f"Verified Table: drainage_network. Row count: {drain_count}")
        self.assertEqual(drain_count, 5) # 5 drains seeded
        
    def test_2_real_vector_search(self):
        """Test real BigQuery Vector Search on index guidelines."""
        print("\n--- Test 2: BigQuery Vector Search RAG Inquiries ---")
        
        # Initialize Google GenAI client to generate query embedding
        client = genai.Client(vertexai=True, project="floodguardai-501409", location="us-central1")
        query_text = "What is the design criteria for storm water drainage structures?"
        
        print(f"Embedding query text: '{query_text}'")
        emb_response = client.models.embed_content(
            model="text-embedding-004",
            contents=query_text
        )
        query_embedding = emb_response.embeddings[0].values
        
        # Perform Vector Search directly in BigQuery
        # Since we use exact nearest neighbors (brute force) because guidelines is small,
        # we write a cosine distance query using BigQuery SQL functions
        vector_query = f"""
            SELECT 
                doc_name, 
                page_num, 
                category,
                section_title,
                content,
                (
                    SELECT SUM(q * e) 
                    FROM UNNEST(embedding) e WITH OFFSET idx 
                    JOIN UNNEST(@query_emb) q WITH OFFSET idx2 ON idx = idx2
                ) as cosine_similarity
            FROM `{self.dataset}.guidelines_vector`
            ORDER BY cosine_similarity DESC
            LIMIT 3
        """
        
        # Execute parameterized query
        from google.cloud import bigquery
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("query_emb", "FLOAT64", [float(x) for x in query_embedding])
            ]
        )
        
        results = self.bq_client.client.query(vector_query, job_config=job_config).result()
        matched_rows = [dict(row) for row in results]
        
        self.assertTrue(len(matched_rows) > 0)
        print(f"Vector search returned top {len(matched_rows)} matches:")
        for idx, row in enumerate(matched_rows):
            print(f"  Match {idx+1}: {row['doc_name']} (Page {row['page_num']})")
            print(f"    Category: {row['category']} | Section: {row['section_title']}")
            print(f"    Content snippet: {row['content'][:120]}...")
            print(f"    Cosine Similarity: {row['cosine_similarity']:.4f}")
            
    def test_3_real_weather_api(self):
        """Test real Open-Meteo precipitation query."""
        print("\n--- Test 3: Real Weather Telemetry API ---")
        
        # Bengaluru coordinates
        lat, lng = 12.9279, 77.6271
        result = get_weather_telemetry(lat, lng, use_mock=False)
        
        self.assertEqual(result["source"], "open_meteo_api")
        self.assertIn("precipitation_mm_hr", result)
        print(f"Weather at HSR Layout ({lat}, {lng}):")
        print(f"  Precipitation rate: {result['precipitation_mm_hr']} mm/hr")
        print(f"  Status classification: {result['status']}")
        print(f"  2-Hour Forecast trend: {result['forecast_next_2hr']}")
        
    def test_4_real_elevation_api(self):
        """Test real Google Maps Elevation API query."""
        print("\n--- Test 4: Real Google Maps Elevation API ---")
        
        # Bengaluru center point (forces Elevation API over cache if not matching HSR)
        lat, lng = 12.9716, 77.5946
        result = get_elevation_profile(lat, lng, use_mock=False)
        
        self.assertEqual(result["source"], "google_elevation_api")
        self.assertTrue(result["elevation_m"] > 800) # Bengaluru sits high
        print(f"Elevation at Bengaluru Center ({lat}, {lng}):")
        print(f"  Altitude: {result['elevation_m']} meters")
        print(f"  Relative Basin Sink Depth: {result['relative_sink_depth']} meters")
        
    def test_5_real_routing_api(self):
        """Test real Google Maps Directions API & spatial polyline decoding."""
        print("\n--- Test 5: Real Directions & Spatial Route Filtering ---")
        
        # Route from Rajesh Sector 4 to BLR Airport
        origin = "12.9279,77.6271"      # Sector 4 low-lying basin
        destination = "13.1986,77.7066" # BLR Airport
        
        result = calculate_safe_route(origin, destination, use_mock=False)
        
        self.assertEqual(result["source"], "google_directions_api")
        self.assertTrue(len(result["routes"]) > 0)
        
        print(f"Directions query from Rajesh to Airport returned {len(result['routes'])} paths:")
        for r in result["routes"]:
            print(f"  Route: {r['summary']}")
            print(f"    Is Safe from flood points? {r['is_safe']}")
            print(f"    Collisions detected: {r['flood_intersections']}")
            print(f"    Nav Link: {r['google_maps_link'][:80]}..." if r['google_maps_link'] else "    Nav Link: None (Blocked)")

    def test_6_real_hydrological_simulation(self):
        """Test real BigQuery what-if simulator run."""
        print("\n--- Test 6: Real Hydrological What-If Simulator ---")
        
        details = {"drain_id": "HSR-D01"}
        result = run_what_if_simulation("desilt_drain", details)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["intervention"], "desilt_drain")
        print("Hydrological simulation results:")
        print(f"  Affected grid points: {result['affected_grid_points']}")
        print(f"  Baseline Avg FVI: {result['baseline_avg_fvi']}")
        print(f"  Simulated Avg FVI: {result['simulated_avg_fvi']}")
        print(f"  Total FVI Reduction: {result['fvi_reduction_percent']}%")
        print(f"  Estimated Protected Residents: {result['estimated_residents_protected']}")
        print(f"  Model Explanation: {result['explanation']}")

if __name__ == "__main__":
    unittest.main()
