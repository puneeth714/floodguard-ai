import os
import sys
import unittest
import asyncio
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.orchestrator import Orchestrator

class TestFloodGuardAgents(unittest.IsolatedAsyncioTestCase):
    
    @classmethod
    def setUpClass(cls):
        # Load environment variables
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
        os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "True"
        os.environ["GOOGLE_CLOUD_PROJECT"] = "floodguardai-501409"
        print("\n=== Initializing ADK 2.0 Agent Test Suite ===")


    async def test_1_geospatial_flow(self):
        """Test Orchestrator delegating to GeospatialAgent to fetch metrics and compute FVI."""
        print("\n--- Test 1: Geospatial Agent Delegation Flow ---")
        orchestrator = Orchestrator()
        
        # Sector 4 center coordinate (cached basin point)
        result = await orchestrator.run(
            session_id="test_session_geo_hsr",
            user_query="Check local risk status at HSR Layout.",
            latitude=12.9279,
            longitude=77.6271
        )
        
        self.assertIsNotNone(result["final_response"])
        self.assertTrue(len(result["final_response"]) > 0)
        
        state = result["state"]
        # Verify geospatial tools stored results in framework state
        self.assertIn("weather_data", state)
        self.assertIn("elevation_data", state)
        self.assertIn("flood_risk_score", state)
        
        print(f"  FVI Score computed: {state['flood_risk_score']:.2f}")
        print(f"  Weather: {state['weather_data']['status']} ({state['weather_data']['precipitation_mm_hr']} mm/hr)")
        print(f"  Elevation: {state['elevation_data']['elevation_m']}m (sink depth: {state['elevation_data']['relative_sink_depth']}m)")
        print(f"  Orchestrator Final text length: {len(result['final_response'])} characters")

    async def test_2_policy_rag_flow(self):
        """Test Orchestrator delegating to PolicyAgent to perform guidelines vector search."""
        print("\n--- Test 2: Policy Agent RAG Guideline Vector Search ---")
        orchestrator = Orchestrator()
        
        result = await orchestrator.run(
            session_id="test_session_policy_rag",
            user_query="What are the design criteria for storm water drainage networks under guidelines?",
        )
        
        self.assertIsNotNone(result["final_response"])
        state = result["state"]
        
        # Verify vector search RAG guidelines were retrieved
        self.assertIn("policy_documents", state)
        self.assertTrue(len(state["policy_documents"]) > 0)
        
        print(f"  Policy RAG matches returned: {len(state['policy_documents'])}")
        for idx, doc in enumerate(state["policy_documents"][:2]):
            print(f"    Match {idx+1}: {doc['doc_name']} (Page {doc['page_num']})")
            print(f"      Snippet: {doc['content'][:80]}...")

    async def test_3_vision_analysis_flow(self):
        """Test Orchestrator delegating to VisionAgent using image path."""
        print("\n--- Test 3: Vision Agent Image Processing Flow ---")
        orchestrator = Orchestrator()
        
        # Using the standard sample image path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_img = os.path.join(base_dir, "app", "tools", "sample_image.png")
        
        result = await orchestrator.run(
            session_id="test_session_vision_photo",
            user_query="Inspect this waterlogging picture I just uploaded.",
            image_path=sample_img
        )
        
        self.assertIsNotNone(result["final_response"])
        state = result["state"]
        
        # Verify vision results stored in state
        self.assertIn("vision_result", state)
        self.assertIn("detected_depth", state)
        self.assertIn("flood_severity", state)
        
        print(f"  Detected depth: {state['detected_depth']} cm")
        print(f"  Flood severity: {state['flood_severity']}")
        print(f"  Vision summary: {state['vision_result']['summary']}")

if __name__ == "__main__":
    unittest.main()
