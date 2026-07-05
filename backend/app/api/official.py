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

from datetime import datetime

class UpdateSosStatusRequest(BaseModel):
    session_id: str
    status: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_url: Optional[str] = None
    user_id: Optional[str] = None
    detected_depth: Optional[float] = None

@router.post("/update-sos-status")
async def update_sos_status(payload: UpdateSosStatusRequest):
    """
    Inserts an updated status row for the given session_id in the active_sos table.
    This append-only architecture bypasses BigQuery's streaming buffer update lock.
    """
    try:
        bq_client = BigQueryClientWrapper()
        
        # 1. Fetch latest row to copy coordinates/depth/url/user_id if not supplied
        query = f"""
        SELECT session_id, user_id, lat, lng, detected_depth, photo_url
        FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp DESC) as rn
            FROM `{bq_client.dataset_ref}.active_sos`
        )
        WHERE rn = 1 AND session_id = '{payload.session_id}'
        """
        existing = bq_client.execute_query(query)
        if not existing:
            raise HTTPException(status_code=404, detail="SOS session not found")
            
        prev_row = existing[0]
        lat = payload.lat if payload.lat is not None else prev_row["lat"]
        lng = payload.lng if payload.lng is not None else prev_row["lng"]
        photo_url = payload.photo_url if payload.photo_url is not None else prev_row["photo_url"]
        user_id = payload.user_id if payload.user_id is not None else prev_row["user_id"]
        detected_depth = payload.detected_depth if payload.detected_depth is not None else prev_row["detected_depth"]
        
        # 2. Insert new event row
        timestamp_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        new_row = {
            "session_id": payload.session_id,
            "user_id": user_id,
            "lat": lat,
            "lng": lng,
            "detected_depth": detected_depth,
            "photo_url": photo_url,
            "status": payload.status,
            "timestamp": timestamp_str
        }
        bq_client.insert_rows("active_sos", [new_row])
        
        # Decode stranded stats inside user_id
        people_count = 1
        needs = "None"
        if ":" in user_id:
            parts = user_id.split(":")
            for p in parts:
                if p.startswith("people_count="):
                    try:
                        people_count = int(p.split("=")[1])
                    except:
                        pass
                elif p.startswith("needs="):
                    needs = p.split("=")[1]

        # 3. Broadcast update to SSE feed
        broadcast_payload = {
            "session_id": payload.session_id,
            "lat": lat,
            "lng": lng,
            "photo_url": photo_url,
            "status": payload.status,
            "detected_depth": detected_depth,
            "stranded_people_count": people_count,
            "special_needs": needs,
            "timestamp": timestamp_str
        }
        await sse_manager.broadcast({"event": "update_sos", "data": broadcast_payload})
        
        return {"status": "success", "message": f"SOS status updated to {payload.status}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update SOS status: {str(e)}")

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
        # 1. Fetch active SOS records (latest state per session_id, filter out resolved)
        sos_query = f"""
        SELECT session_id, user_id, lat, lng, detected_depth, photo_url, status, timestamp
        FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp DESC) as rn
            FROM `{bq_client.dataset_ref}.active_sos`
        )
        WHERE rn = 1 AND status != 'resolved'
        ORDER BY timestamp DESC
        """
        sos_records = bq_client.execute_query(sos_query)
        
        # Format timestamps to ISO strings and decode custom user_id format
        for s in sos_records:
            if s.get("timestamp"):
                s["timestamp"] = s["timestamp"].isoformat()
            
            user_id_str = s.get("user_id", "resident")
            people_count = 1
            needs = "None"
            if ":" in user_id_str:
                parts = user_id_str.split(":")
                for p in parts:
                    if p.startswith("people_count="):
                        try:
                            people_count = int(p.split("=")[1])
                        except:
                            pass
                    elif p.startswith("needs="):
                        needs = p.split("=")[1]
            s["stranded_people_count"] = people_count
            s["special_needs"] = needs
            
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

class SimulateRequest(BaseModel):
    intervention_type: str
    details: dict

@router.post("/simulate")
def simulate_intervention(payload: SimulateRequest):
    """
    Runs a mock simulation query to evaluate FVI risk changes after interventions.
    """
    baseline_avg_fvi = 65.4
    if payload.intervention_type == "desilt_drain":
        simulated_avg_fvi = 42.1
        reduction = 35.6
        residents = 1600
    elif payload.intervention_type == "deploy_pump":
        simulated_avg_fvi = 53.2
        reduction = 18.6
        residents = 750
    else:
        simulated_avg_fvi = 60.1
        reduction = 8.1
        residents = 200

    return {
        "status": "success",
        "intervention": payload.intervention_type,
        "baseline_avg_fvi": baseline_avg_fvi,
        "simulated_avg_fvi": simulated_avg_fvi,
        "fvi_reduction_percent": reduction,
        "estimated_residents_protected": residents,
        "confidence_score": 90.0
    }

@router.get("/export-report")
def export_recovery_report(session_id: str):
    """
    Compiles and exports a post-recovery briefing report in markdown.
    """
    report_md = f"""# FloodGuard AI — Post-Flood Incident Recovery Report
*   **Session Ref:** {session_id}
*   **Report Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
*   **Target Region:** HSR Layout Sector 4 Basin Area
*   **Confidence Index:** 95%

## 1. Executive Summary
During the simulated rain storm cell precipitating at 45mm/hr, total water levels peaked in Sector 4 low points. Emergency tactical interventions were executed.

## 2. Infrastructure Stats
*   **Active Water Pumps:** 2 (Sector 4 High Capacity, Sector 2 Flyover Drainage)
*   **Stopped Water Pumps:** 1 (Sector 4 Outer Ring Aux)
*   **Blocked Storm Drains:** 1 (Sector 4 Secondary Drain A - HSR-D02)

## 3. Rescue & Evacuation Metrics
All distress alerts registered in the active monitoring log have been successfully dispatched and transitioned to RESOLVED.
    """
    return {
        "status": "success",
        "session_id": session_id,
        "report_markdown": report_md
    }
