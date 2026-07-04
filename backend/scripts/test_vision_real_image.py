import os
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.vision import VisionTool
from dotenv import load_dotenv

def run_vision_test():
    # Load env variables (for GCloud / Vertex AI configuration)
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))
    
    image_path = "/home/puneeth/programmes/genai_apac/cohort2/test_data/bengaluru_flooded.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return
        
    print(f"Initializing VisionTool...")
    try:
        vision_tool = VisionTool()
        print(f"Running multimodal flood analysis on real image: {image_path}...")
        result = vision_tool.analyze_flood_image(image_path)
        
        print("\n========================================================")
        print("REAL IMAGE VISION ANALYSIS RESULT")
        print("========================================================")
        print(f"Status: SUCCESS")
        print(f"Water Depth: {result.water_depth_cm} cm (approx {round(result.water_depth_cm / 30.48, 2)} ft)")
        print(f"Severity Level: {result.severity.value}")
        print(f"Rescue Priority: {result.rescue_priority.value}")
        print(f"Road Condition: {result.road_condition.value}")
        print(f"Road Blocked? {result.road_blocked}")
        print(f"Vehicle Detected? {result.vehicle_detected}")
        print(f"Vehicle Submerged? {result.vehicle_submerged}")
        print(f"People Detected? {result.people_detected}")
        print(f"Property Damage Visible? {result.property_damage}")
        print(f"Model Confidence: {result.confidence * 100:.1f}%")
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")
        print(f"\nSummary Excerpt:\n  \"{result.summary}\"")
        print("========================================================")
        
    except Exception as e:
        print(f"Error running VisionTool: {e}")

if __name__ == "__main__":
    run_vision_test()
