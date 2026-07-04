import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ADK elements
from app.agents.orchestrator import Orchestrator

# Setup Logger with Debug mode and write to file
LOG_DIR = "/home/puneeth/.gemini/antigravity-cli/brain/c8262929-b970-4f35-a528-b82a9640a966/scratch"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "agent_test_scenarios.log")

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Add file handler for debug logs
file_handler = logging.FileHandler(LOG_FILE, mode="w")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Scenarios Definition
SCENARIOS = [
    {
        "id": 1,
        "name": "General Chat / Greeting (Resident Role)",
        "session_id": "session_scen_1",
        "role": "resident",
        "query": "Hello! What is the FloodGuard AI Platform?",
        "lat": None, "lng": None, "dest": None, "img": None
    },
    {
        "id": 2,
        "name": "Resident Low-Lying Risk Check (Cached Basin)",
        "session_id": "session_scen_2",
        "role": "resident",
        "query": "Check local flooding risk.",
        "lat": 12.9279, "lng": 77.6271, "dest": None, "img": None
    },
    {
        "id": 3,
        "name": "Resident High-Ground Risk Check (GCP Center API)",
        "session_id": "session_scen_3",
        "role": "resident",
        "query": "Is it safe from waterlogging here?",
        "lat": 12.9716, "lng": 77.5946, "dest": None, "img": None
    },
    {
        "id": 4,
        "name": "Standard Safe Navigation Routing Check",
        "session_id": "session_scen_4",
        "role": "resident",
        "query": "Route from Rajesh to Bengaluru Center.",
        "lat": 12.9279, "lng": 77.6271, "dest": "12.9716,77.5946", "img": None
    },
    {
        "id": 5,
        "name": "Avoiding Blocked Routing / Detour Injection (Mock)",
        "session_id": "session_scen_5",
        "role": "resident",
        "query": "Route from low-lying flooded region to Airport.",
        "lat": 12.9165, "lng": 77.6220, "dest": "13.1986,77.7066", "img": None
    },
    {
        "id": 6,
        "name": "Multi-Turn A [Turn 1]: Upload Flood Image",
        "session_id": "session_multiturn_a",
        "role": "resident",
        "query": "Please analyze the severity and depth of this waterlogged road.",
        "lat": None, "lng": None, "dest": None, "img": "app/tools/sample_image.png"
    },
    {
        "id": 7,
        "name": "Multi-Turn A [Turn 2]: Get Safe Waypoint Path",
        "session_id": "session_multiturn_a",
        "role": "resident",
        "query": "Since the depth looks high, I am at HSR Sector 4 (coords: 12.9279,77.6271). Recommend a safe path to Airport.",
        "lat": 12.9279, "lng": 77.6271, "dest": "13.1986,77.7066", "img": None
    },
    {
        "id": 8,
        "name": "Multi-Turn B [Turn 1]: Resident Simulation Try (Block)",
        "session_id": "session_multiturn_b",
        "role": "resident",
        "query": "Simulate desilting storm water drain HSR-D01.",
        "lat": None, "lng": None, "dest": None, "img": None
    },
    {
        "id": 9,
        "name": "Multi-Turn B [Turn 2]: Official Simulation Try (Allow)",
        "session_id": "session_multiturn_b",
        "role": "official",
        "query": "Now I am logged in as an official. Simulate desilting storm water drain HSR-D01.",
        "lat": None, "lng": None, "dest": None, "img": None
    },
    {
        "id": 10,
        "name": "Official Guidelines Vector Search RAG",
        "session_id": "session_scen_10",
        "role": "official",
        "query": "What are the engineering design criteria for stormwater drainage structures?",
        "lat": None, "lng": None, "dest": None, "img": None
    }
]

async def run_scenario(orchestrator: Orchestrator, scenario: dict) -> dict:
    logging.info(f"=== Starting Scenario {scenario['id']}: {scenario['name']} ===")
    
    # Resolve absolute path for image if present
    img_path = None
    if scenario["img"]:
        img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), scenario["img"])
        
    try:
        # Run orchestrator runner flow
        result = await orchestrator.run(
            session_id=scenario["session_id"],
            user_query=scenario["query"],
            latitude=scenario["lat"],
            longitude=scenario["lng"],
            destination=scenario["dest"],
            image_path=img_path,
            user_role=scenario["role"]
        )
        
        logging.info(f"=== Finished Scenario {scenario['id']} successfully. ===")
        return {
            "id": scenario["id"],
            "name": scenario["name"],
            "session_id": scenario["session_id"],
            "role": scenario["role"],
            "success": True,
            "response": result["final_response"],
            "state_keys": list(result["state"].keys()),
            "risk_score": result["state"].get("flood_risk_score"),
            "sim_result": "Yes" if "simulation_result" in result["state"] else "No"
        }
    except Exception as e:
        logging.exception(f"=== Failed Scenario {scenario['id']}: {e} ===")
        return {
            "id": scenario["id"],
            "name": scenario["name"],
            "session_id": scenario["session_id"],
            "role": scenario["role"],
            "success": False,
            "error": str(e)
        }

async def main():
    # Load env variables (ensuring VertexAI environment vars are set)
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "True"
    os.environ["GOOGLE_CLOUD_PROJECT"] = "floodguardai-501409"
    
    orchestrator = Orchestrator()
    results = []
    
    print("\n==========================================================================")
    print("         RUNNING 10 ADK 2.0 SCENARIO FLOWS (INCL. MULTI-TURN & IMAGE)     ")
    print("==========================================================================")
    
    for s in SCENARIOS:
        print(f"Running Scenario {s['id']}: {s['name']} (Role: {s['role']})...")
        res = await run_scenario(orchestrator, s)
        results.append(res)
        # Bounded sleep to respect free tier rate limits (Gemini API 429 warnings)
        await asyncio.sleep(8)
        
    print("\n==========================================================================================")
    print("                                   SCENARIO RUN SUMMARY                                   ")
    print("==========================================================================================")
    print(f"{'ID':<3} | {'Scenario Name':<45} | {'Role':<8} | {'Status':<6} | {'Risk':<6} | {'Sim?':<4} | {'Response Snippet'}")
    print("-" * 125)
    for r in results:
        if r["success"]:
            risk = f"{r['risk_score']:.1f}" if r["risk_score"] is not None else "N/A"
            snippet = r["response"].replace("\n", " ")[:40] + "..."
            print(f"{r['id']:<3} | {r['name']:<45} | {r['role']:<8} | {'PASS':<6} | {risk:<6} | {r['sim_result']:<4} | {snippet}")
        else:
            print(f"{r['id']:<3} | {r['name']:<45} | {r['role']:<8} | {'FAIL':<6} | {'N/A':<6} | {'No':<4} | Error: {r['error']}")
            
    print("\nDetailed debug logs are saved to:")
    print(f"  file://{LOG_FILE}")
    print("==========================================================================================")

if __name__ == "__main__":
    asyncio.run(main())
