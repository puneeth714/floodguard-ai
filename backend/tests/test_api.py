import os
import sys
import unittest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.bigquery_client import BigQueryClientWrapper

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

    def test_reverse_geocode(self):
        """Test that the reverse geocoding endpoint returns a valid address response."""
        response = self.client.get("/api/resident/reverse-geocode?latitude=12.9279&longitude=77.6271")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("formatted_address", data)

    def test_update_sos_status(self):
        """Test updating active SOS distress signal lifecycle status."""
        # Create a mock entry first
        from datetime import datetime
        bq_client = BigQueryClientWrapper()
        mock_id = "test_sos_lifecycle_update"
        row = {
            "session_id": mock_id,
            "user_id": "resident:people_count=2:needs=Insulin",
            "lat": 12.9279,
            "lng": 77.6271,
            "detected_depth": 40.0,
            "photo_url": "/static/uploads/mock.png",
            "status": "pending",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        }
        bq_client.insert_rows("active_sos", [row])

        # Execute status change request
        payload = {
            "session_id": mock_id,
            "status": "dispatching"
        }
        response = self.client.post("/api/official/update-sos-status", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

        # Verify in dashboard summary (resolves latest status)
        res_summary = self.client.get("/api/official/dashboard-summary")
        self.assertEqual(res_summary.status_code, 200)
        summary_data = res_summary.json()
        matches = [s for s in summary_data["active_sos"] if s["session_id"] == mock_id]
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0]["status"], "dispatching")
        self.assertEqual(matches[0]["stranded_people_count"], 2)
        self.assertEqual(matches[0]["special_needs"], "Insulin")

        # Mark as resolved
        payload_resolve = {
            "session_id": mock_id,
            "status": "resolved"
        }
        response_res = self.client.post("/api/official/update-sos-status", json=payload_resolve)
        self.assertEqual(response_res.status_code, 200)

        # Verify filtered out of active alerts
        res_summary2 = self.client.get("/api/official/dashboard-summary")
        summary_data2 = res_summary2.json()
        matches2 = [s for s in summary_data2["active_sos"] if s["session_id"] == mock_id]
        self.assertEqual(len(matches2), 0)

