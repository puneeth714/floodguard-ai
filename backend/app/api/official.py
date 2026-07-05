import asyncio
import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.orchestrator import Orchestrator
from app.db.bigquery_client import BigQueryClientWrapper
from app.core.sse import sse_manager

router = APIRouter(prefix="/api/official", tags=["Official"])

# Initialize Orchestrator and BQ clients
orchestrator = Orchestrator()
bq_client = BigQueryClientWrapper()

class OfficialChatRequest(BaseModel):
    session_id: str
    user_query: str
    demo_profile: Optional[str] = None

@router.post("/chat")
async def official_chat(payload: OfficialChatRequest):
    """
    Executes a chat session turn for a municipal official.
    Binds the 'official' role boundary to authorize simulations and vector searches.
    """
    try:
        result = await orchestrator.run(
            session_id=payload.session_id,
            user_query=payload.user_query,
            user_role="official",
            demo_profile=payload.demo_profile
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")

@router.get("/dashboard-summary")
async def get_dashboard_summary():
    """
    Queries BigQuery and compiles the active status overview:
    - Active distress alerts (active_sos)
    - Stormwater drainage network status (drainage_network)
    - Active stormwater pumps status
    - Flood Vulnerability Index heatmap coords (vulnerability_grids)
    """
    try:
        # 1. Fetch active SOS records
        sos_query = f"""
        SELECT session_id, lat, lng, detected_depth, photo_url, status, timestamp
        FROM `{bq_client.dataset_ref}.active_sos`
        ORDER BY timestamp DESC
        """
        sos_records = bq_client.execute_query(sos_query)
        
        # Format timestamps to ISO strings
        for s in sos_records:
            if s.get("timestamp"):
                s["timestamp"] = s["timestamp"].isoformat()

        # 2. Fetch drainage network status
        drain_query = f"""
        SELECT drain_id, name, lat, lng, status
        FROM `{bq_client.dataset_ref}.drainage_network`
        """
        drains = bq_client.execute_query(drain_query)

        # 3. Fetch FVI vulnerability grids for heatmap
        grid_query = f"""
        SELECT lat, lng, fvi
        FROM `{bq_client.dataset_ref}.vulnerability_grids`
        WHERE fvi IS NOT NULL
        """
        fvi_grids = bq_client.execute_query(grid_query)

        # 4. Compile static/dynamic water pump list (placed in HSR Layout basin)
        pumps = [
            {"pump_id": "PUMP_HSR_4_01", "name": "Sector 4 High Capacity Suction", "lat": 12.9279, "lng": 77.6271, "status": "active", "flow_rate_lps": 120.0},
            {"pump_id": "PUMP_HSR_4_02", "name": "Sector 4 Outer Ring Aux", "lat": 12.9290, "lng": 77.6285, "status": "stopped", "flow_rate_lps": 80.0},
            {"pump_id": "PUMP_HSR_2_01", "name": "Sector 2 Flyover Drainage Unit", "lat": 12.9340, "lng": 77.6320, "status": "active", "flow_rate_lps": 150.0}
        ]

        # 5. Compile live weather radar / cloud formations data (for map visualization)
        weather_radar = [
            {"cloud_id": "CLOUD_HSR_B", "name": "HSR Basin Storm Cell (Heavy Rain)", "lat": 12.9279, "lng": 77.6271, "radius_m": 950.0, "intensity": "heavy", "precipitation_mm_hr": 45.0},
            {"cloud_id": "CLOUD_SB_D", "name": "Silk Board Cloud Deck (Moderate Rain)", "lat": 12.9180, "lng": 77.6230, "radius_m": 1300.0, "intensity": "moderate", "precipitation_mm_hr": 15.0}
        ]

        return {
            "active_sos": sos_records,
            "drains": drains,
            "pumps": pumps,
            "fvi_heatmap": fvi_grids,
            "weather_radar": weather_radar
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile dashboard summary: {str(e)}")

@router.get("/live-sos-feed")
async def live_sos_feed():
    """
    Server-Sent Events (SSE) stream endpoint to push real-time resident
    distress signals (flash SOS uploads) onto the official dashboard map.
    """
    async def event_generator():
        # Subscribe to SSE broadcasts
        q = sse_manager.subscribe()
        try:
            while True:
                try:
                    # Wait for a new broadcasted message (heartbeat at 15.0s timeout)
                    data = await asyncio.wait_for(q.get(), timeout=15.0)
                    
                    # Yield SSE formatted data
                    event_type = data.get("event", "message")
                    event_payload = json.dumps(data.get("data", {}))
                    yield f"event: {event_type}\ndata: {event_payload}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keep-alive heartbeat comments to prevent browser client timeouts
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            # Clean up subscription when client disconnects
            print("SSE client disconnected from live-sos-feed.")
        finally:
            sse_manager.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
