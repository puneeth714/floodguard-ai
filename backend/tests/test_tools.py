import os
import sys
import unittest

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.weather import get_weather_telemetry
from app.tools.elevation import get_elevation_profile
from app.tools.routing import calculate_safe_route
from app.tools.simulation import run_what_if_simulation

class TestFloodGuardTools(unittest.TestCase):
    
    def test_weather_telemetry_mock(self):
        """Test weather tool with simulated rain override."""
        result = get_weather_telemetry(12.9279, 77.6271, use_mock=True, mock_precipitation=45.0)
        self.assertEqual(result["source"], "mock_override")
        self.assertEqual(result["precipitation_mm_hr"], 45.0)
        self.assertIn("Severe", result["status"])
        
    def test_weather_telemetry_real(self):
        """Test weather tool with live API check."""
        result = get_weather_telemetry(12.9279, 77.6271, use_mock=False)
        self.assertIn(result["source"], ["open_meteo_api", "fallback_default"])
        self.assertIn("precipitation_mm_hr", result)

    def test_elevation_profile_mock(self):
        """Test elevation lookup mock override."""
        result = get_elevation_profile(12.9279, 77.6271, use_mock=True, mock_altitude=855.0)
        self.assertEqual(result["source"], "mock_override")
        self.assertEqual(result["elevation_m"], 855.0)
        self.assertEqual(result["relative_sink_depth"], 9.0)

    def test_elevation_profile_cache(self):
        """Test elevation lookup using HSR Layout localized coordinate cache."""
        # Rajesh's HSR Sector 4 coordinate
        result = get_elevation_profile(12.9279, 77.6271, use_mock=False)
        self.assertEqual(result["source"], "local_sink_cache")
        self.assertEqual(result["elevation_m"], 858.0)
        self.assertEqual(result["relative_sink_depth"], 6.0)

    def test_safe_route_mock(self):
        """Test route avoidance and detour waypoint injection under mock settings."""
        origin = "12.9279,77.6271" # HSR Sector 4
        destination = "13.1986,77.7066" # Airport
        
        result = calculate_safe_route(origin, destination, use_mock=True)
        self.assertEqual(result["source"], "mock_route_generator")
        
        # Check that we have multiple routes and one of them is the safe detour waypoint link
        self.assertTrue(len(result["routes"]) >= 2)
        detour_route = result["routes"][1]
        self.assertTrue(detour_route["is_safe"])
        self.assertIn("waypoints=12.9340,77.6320", detour_route["google_maps_link"])

    def test_hydrological_simulation(self):
        """Test simulation calculations for desilting a stormwater drain."""
        details = {"drain_id": "HSR-D01"}
        result = run_what_if_simulation("desilt_drain", details)
        
        # The seeder should have set up the tables, so we check query result status
        self.assertIn(result["status"], ["success", "fallback_mock"])
        self.assertIn("baseline_avg_fvi", result)
        self.assertIn("simulated_avg_fvi", result)
        self.assertIn("fvi_reduction_percent", result)
        self.assertTrue(result["estimated_residents_protected"] >= 0)

if __name__ == "__main__":
    unittest.main()
