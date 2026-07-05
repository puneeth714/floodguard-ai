import os
import sys
import unittest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

class TestFloodGuardAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load environment variables
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))
        os.environ["GOOGLE_CLOUD_PROJECT"] = "floodguardai-501409"
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        """Test that the gateway root returns the Resident App page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    def test_resident_chat(self):
        """Test resident chat controller triggers Orchestrator correctly in test mode."""
        payload = {
            "session_id": "test_api_resident_chat",
            "user_query": "Check local risk status at HSR Layout.",
            "demo_profile": "rajesh"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        self.assertIn("state", data)
        self.assertEqual(data["state"]["demo_profile"], "rajesh")

    def test_official_chat_denied_simulation(self):
        """Test that a resident query is blocked from running what-if simulations."""
        payload = {
            "session_id": "test_api_official_chat_denied",
            "user_query": "Can I run a desilting what-if simulation?",
            "demo_profile": "rajesh" # Rajesh is a resident profile
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("municipal official accounts", data["final_response"].lower())

    def test_dashboard_summary(self):
        """Test official dashboard metadata query compilation."""
        response = self.client.get("/api/official/dashboard-summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("active_sos", data)
        self.assertIn("drains", data)
        self.assertIn("pumps", data)
        self.assertIn("fvi_heatmap", data)
