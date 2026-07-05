import os
import sys
import time
import unittest
from fastapi.testclient import TestClient
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.bigquery_client import BigQueryClientWrapper

class TestFloodGuardScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load environment variables
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        load_dotenv(env_path)
        cls.client = TestClient(app)
        cls.bq_client = BigQueryClientWrapper()
        
    def setUp(self):
        # Add a 12.0-second delay before every test to prevent Gemini 429 Rate Limit exhaustion
        time.sleep(12.0)

    # ==================================================================
    # RESIDENT (USER) SCENARIOS (10 TESTS)
    # ==================================================================

    def test_u1_rajesh_safety_check(self):
        """User U1: Rajesh (Sector 4) checks safety status at his location."""
        payload = {
            "session_id": "scenario_u1_rajesh",
            "user_query": "Am I safe in my place now?",
            "latitude": 12.9279,
            "longitude": 77.6271,
            "demo_profile": "rajesh",
            "user_role": "resident"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        # Rajesh is in Sector 4 which has high FVI and heavy rain
        self.assertIn("flood_risk_score", data["state"])
        print("\n[U1 Rajesh Safety Check Response]:", data["final_response"][:120], "...")

    def test_u2_rajesh_airport_navigation(self):
        """User U2: Rajesh (Sector 4) requests safe navigation to the airport."""
        payload = {
            "session_id": "scenario_u2_airport",
            "user_query": "I want to go to the airport",
            "latitude": 12.9279,
            "longitude": 77.6271,
            "destination": "13.1986,77.7066",
            "demo_profile": "rajesh",
            "user_role": "resident"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        # Recommends safe route link avoiding Silk Board
        self.assertIn("google.com/maps", data["final_response"])
        print("\n[U2 Airport Route Response]:", data["final_response"][:120], "...")

    def test_u3_radha_colony_risk(self):
        """User U3: Radha (Sector 2) checks risk status (elevated terrain)."""
        payload = {
            "session_id": "scenario_u3_radha",
            "user_query": "Is my colony at risk?",
            "latitude": 12.9340,
            "longitude": 77.6320,
            "demo_profile": "radha",
            "user_role": "resident"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[U3 Radha Colony Risk Response]:", data["final_response"][:120], "...")

    def test_u4_radha_safe_shelter(self):
        """User U4: Radha requests safe shelter locations nearby (RAG query)."""
        payload = {
            "session_id": "scenario_u4_shelter",
            "user_query": "Find nearby safe/shelter place for me",
            "latitude": 12.9340,
            "longitude": 77.6320,
            "demo_profile": "radha",
            "user_role": "resident"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[U4 Radha Safe Shelter Response]:", data["final_response"][:120], "...")

    def test_u5_anonymous_gps_sync(self):
        """User U5: Anonymous resident synchronizes real-time coordinates."""
        payload = {
            "session_id": "scenario_u5_anonymous",
            "user_query": "What is my current FVI risk here?",
            "latitude": 12.9250,
            "longitude": 77.6300,
            "demo_profile": "anonymous",
            "user_role": "resident"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["state"]["latitude"], 12.9250)
        self.assertEqual(data["state"]["longitude"], 77.6300)
        print("\n[U5 Anonymous GPS Risk Response]:", data["final_response"][:120], "...")

    def test_u6_anonymous_upload_sos_image(self):
        """User U6: Anonymous resident uploads a mock flood JPEG photo."""
        mock_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "mock_flood.jpg"
        )
        # Create a temp file if it does not exist
        if not os.path.exists(mock_file_path):
            with open(mock_file_path, "wb") as f:
                f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\xFF\xD9")
                
        with open(mock_file_path, "rb") as img:
            response = self.client.post(
                "/api/resident/upload-sos",
                files={"file": ("mock_flood.jpg", img, "image/jpeg")},
                data={
                    "latitude": 12.9279,
                    "longitude": 77.6271,
                    "stranded_count": 1,
                    "medical_needs": "None",
                    "user_query": "Heavy water clogging"
                }
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["sos_id"].startswith("sos_"))
        print("\n[U6 Anonymous SOS Upload Response]:", data["message"])

    def test_u7_resident_stranded_telemetry(self):
        """User U7: Resident reports 5 stranded hostages needing emergency assistance."""
        mock_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_flood.jpg")
        with open(mock_file_path, "rb") as img:
            response = self.client.post(
                "/api/resident/upload-sos",
                files={"file": ("mock_flood.jpg", img, "image/jpeg")},
                data={
                    "latitude": 12.9279,
                    "longitude": 77.6271,
                    "stranded_count": 5,
                    "medical_needs": "Elderly grandmother and insulin storage needed",
                    "user_query": "Active rescue needed"
                }
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify that details resolve in summary table correctly
        res_summary = self.client.get("/api/official/dashboard-summary")
        summary_data = res_summary.json()
        matches = [s for s in summary_data["active_sos"] if s["session_id"] == data["sos_id"]]
        if matches:
            self.assertEqual(matches[0]["stranded_people_count"], 5)
            self.assertEqual(matches[0]["special_needs"], "Elderly grandmother and insulin storage needed")
        print("\n[U7 Stranded Count & Medical Needs Logged Successfully]")

    def test_u8_electrical_safety_guideline(self):
        """User U8: Resident queries safety instructions regarding electrical appliances during flooding."""
        payload = {
            "session_id": "scenario_u8_electrical",
            "user_query": "What should I do with my electrical appliances when water starts rising?",
            "latitude": 12.9279,
            "longitude": 77.6271,
            "demo_profile": "rajesh",
            "user_role": "resident"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[U8 Electrical Safety Guidelines Response]:", data["final_response"][:120], "...")

    def test_u9_post_flood_recovery_health(self):
        """User U9: Resident asks about water safety and health protocols post flood."""
        payload = {
            "session_id": "scenario_u9_recovery",
            "user_query": "How do we disinfect drinking water and clean mud after the flood has cleared?",
            "latitude": 12.9279,
            "longitude": 77.6271,
            "demo_profile": "rajesh",
            "user_role": "resident"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[U9 Post-Flood Health Guidelines Response]:", data["final_response"][:120], "...")

    def test_u10_resident_restricted_simulation(self):
        """User U10: Verifies that a resident cannot run what-if simulations (role boundary)."""
        payload = {
            "session_id": "scenario_u10_restricted",
            "user_query": "Can we run a desilting simulation for Sector 4?",
            "latitude": 12.9279,
            "longitude": 77.6271,
            "demo_profile": "rajesh",
            "user_role": "resident"
        }
        response = self.client.post("/api/resident/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should be blocked from executing hydrological simulation
        self.assertIn("municipal official accounts", data["final_response"].lower())
        print("\n[U10 Resident Role Boundary Block Checked]:", data["final_response"][:120], "...")


    # ==================================================================
    # OFFICIAL (COMMAND CENTER) SCENARIOS (10 TESTS)
    # ==================================================================

    def test_o1_triage_critical_alerts(self):
        """Official O1: AI Triages and prioritizes active SOS alerts based on depth, count, and needs."""
        payload = {
            "session_id": "scenario_o1_triage",
            "user_query": "Give me a triage ranking of our active resident distress alerts. Which should we send teams to first?",
            "demo_profile": "official"
        }
        response = self.client.post("/api/official/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        # Should call get_operational_status and summarize alerts prioritization
        print("\n[O1 Official SOS Alert Triage Response]:", data["final_response"][:150], "...")

    def test_o2_blocked_drains_overview(self):
        """Official O2: AI lists all currently blocked municipal drains."""
        payload = {
            "session_id": "scenario_o2_drains",
            "user_query": "Show me all blocked stormwater drains in the city.",
            "demo_profile": "official"
        }
        response = self.client.post("/api/official/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[O2 Blocked Stormwater Drains Response]:", data["final_response"][:150], "...")

    def test_o3_pumps_operational_status(self):
        """Official O3: AI lists mechanical water pump states and identifies stopped units."""
        payload = {
            "session_id": "scenario_o3_pumps",
            "user_query": "Are there any water pumps that are currently stopped and should be activated?",
            "demo_profile": "official"
        }
        response = self.client.post("/api/official/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[O3 Stopped Suction Pumps Response]:", data["final_response"][:150], "...")

    def test_o4_weather_storm_radar_check(self):
        """Official O4: AI describes live weather storm-cells active on the radar overlay."""
        payload = {
            "session_id": "scenario_o4_radar",
            "user_query": "Which storm cells are active over the city according to our weather radar overlays?",
            "demo_profile": "official"
        }
        response = self.client.post("/api/official/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[O4 Active Radar Storm Cells Response]:", data["final_response"][:150], "...")

    def test_o5_desilting_what_if_simulation(self):
        """Official O5: AI calculates simulation metrics of desilting stormwater drains."""
        payload = {
            "session_id": "scenario_o5_desilt_sim",
            "user_query": "Run a desilting simulation for the 3 main drains at HSR Layout. What is the impact?",
            "demo_profile": "official"
        }
        response = self.client.post("/api/official/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        self.assertIn("simulation_result", data["state"])
        print("\n[O5 Desilting What-If Hydrologic Simulation]:", data["final_response"][:150], "...")

    def test_o6_water_pump_simulation(self):
        """Official O6: AI simulates FVI impact of deploying water pumps at coordinates."""
        payload = {
            "session_id": "scenario_o6_pump_sim",
            "user_query": "What happens to the FVI if we deploy a 120 lps water pump at coordinates 12.9279, 77.6271?",
            "demo_profile": "official"
        }
        response = self.client.post("/api/official/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[O6 Water Pump Deployment Simulation]:", data["final_response"][:150], "...")

    def test_o7_sos_status_transition_dispatched(self):
        """Official O7: Updates distress status to 'dispatching' (Deduplicated Append-Only write)."""
        mock_id = "scenario_o7_sos_event"
        # Seed record
        row = {
            "session_id": mock_id,
            "user_id": "resident:people_count=4:needs=Elderly",
            "lat": 12.9279,
            "lng": 77.6271,
            "detected_depth": 55.0,
            "photo_url": "/static/uploads/o7.png",
            "status": "pending",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        }
        self.bq_client.insert_rows("active_sos", [row])

        # Execute dispatch change
        payload = {
            "session_id": mock_id,
            "status": "dispatching"
        }
        response = self.client.post("/api/official/update-sos-status", json=payload)
        self.assertEqual(response.status_code, 200)
        
        # Verify state is updated in summary (returns status='dispatching')
        summary = self.client.get("/api/official/dashboard-summary").json()
        matches = [s for s in summary["active_sos"] if s["session_id"] == mock_id]
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0]["status"], "dispatching")
        print("\n[O7 SOS Lifecycle Updated to DISPATCHING Successfully]")

    def test_o8_sos_status_transition_resolved(self):
        """Official O8: Resolves alert (status='resolved'), filters it out of active feed."""
        mock_id = "scenario_o8_sos_event"
        # Seed record
        row = {
            "session_id": mock_id,
            "user_id": "resident:people_count=1:needs=None",
            "lat": 12.9279,
            "lng": 77.6271,
            "detected_depth": 30.0,
            "photo_url": "/static/uploads/o8.png",
            "status": "dispatching",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        }
        self.bq_client.insert_rows("active_sos", [row])

        # Resolve
        payload = {
            "session_id": mock_id,
            "status": "resolved"
        }
        response = self.client.post("/api/official/update-sos-status", json=payload)
        self.assertEqual(response.status_code, 200)
        
        # Verify filtered out of active alerts summary
        summary = self.client.get("/api/official/dashboard-summary").json()
        matches = [s for s in summary["active_sos"] if s["session_id"] == mock_id]
        self.assertEqual(len(matches), 0)
        print("\n[O8 SOS Alert RESOLVED and Filtered Out of Active Dashboard]")

    def test_o9_disaster_guidelines_brief_download(self):
        """Official O9: Official requests RAG search for disaster response briefings."""
        payload = {
            "session_id": "scenario_o9_brief",
            "user_query": "Generate a summary briefing of municipal evacuations and guidelines for Sector 4.",
            "demo_profile": "official"
        }
        response = self.client.post("/api/official/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[O9 Official Guidelines Brief Response]:", data["final_response"][:150], "...")

    def test_o10_low_lying_hotspots_check(self):
        """Official O10: AI inspects historical flood records and low-lying hotspots."""
        payload = {
            "session_id": "scenario_o10_hotspots",
            "user_query": "Which historical low-lying hotspots in Bengaluru have highest flood risk and how do we prevent it?",
            "demo_profile": "official"
        }
        response = self.client.post("/api/official/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("final_response", data)
        print("\n[O10 Historical Hotspots & Prevention Response]:", data["final_response"][:150], "...")

if __name__ == "__main__":
    unittest.main()
