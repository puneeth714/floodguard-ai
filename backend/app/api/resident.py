import os
import uuid
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.agents.orchestrator import Orchestrator
from app.db.bigquery_client import BigQueryClientWrapper
from app.tools.vision import VisionTool
from app.core.sse import sse_manager

router = APIRouter(prefix="/api/resident", tags=["Resident"])

# Initialize Orchestrator and BQ clients
orchestrator = Orchestrator()
bq_client = BigQueryClientWrapper()

# Define storage directory for uploads
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "app", "static", "uploads"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    session_id: str
    user_query: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    destination: Optional[str] = None
    image_path: Optional[str] = None
    user_role: Optional[str] = "resident"
    demo_profile: Optional[str] = None

@router.post("/chat")
async def resident_chat(payload: ChatRequest):
    """
    Executes a chat session turn for a resident using the Orchestrator.
    Handles location, weather, and detour waypoint injection.
    """
    try:
        result = await orchestrator.run(
            session_id=payload.session_id,
            user_query=payload.user_query,
            latitude=payload.latitude,
            longitude=payload.longitude,
            destination=payload.destination,
            image_path=payload.image_path,
            user_role=payload.user_role or "resident",
            demo_profile=payload.demo_profile
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")

async def analyze_sos_image_background(
    session_id: str,
    image_path: str,
    lat: float,
    lng: float,
    photo_url: str,
    timestamp_str: str
):
    """
    Background worker that runs the Gemini Flash Vision tool to estimate
    flood depth/severity and update the active_sos record in BigQuery.
    """
    try:
        print(f"Background Task: Analyzing SOS image {image_path} for session {session_id}...")
        vision_tool = VisionTool()
        vision_result = vision_tool.analyze_flood_image(image_path)
        
        depth = float(vision_result.water_depth_cm)
        severity = vision_result.hazard_level.value  # 'low', 'medium', 'high', 'critical'
        
        print(f"Vision Result: Estimated depth {depth}cm, severity: {severity}")
        
        # 1. Update BigQuery table
        query = f"""
        UPDATE `{bq_client.dataset_ref}.active_sos`
        SET detected_depth = {depth}, status = 'active'
        WHERE session_id = '{session_id}'
        """
        bq_client.client.query(query).result()
        
        # 2. Broadcast updated state through SSE feed
        updated_data = {
            "session_id": session_id,
            "lat": lat,
            "lng": lng,
            "photo_url": photo_url,
            "status": "active",
            "detected_depth": depth,
            "severity": severity,
            "timestamp": timestamp_str
        }
        await sse_manager.broadcast({"event": "update_sos", "data": updated_data})
        
    except Exception as e:
        print(f"Error analyzing image in background task: {e}")
        # Mark as error or default active state
        try:
            query = f"""
            UPDATE `{bq_client.dataset_ref}.active_sos`
            SET status = 'active_error'
            WHERE session_id = '{session_id}'
            """
            bq_client.client.query(query).result()
        except Exception as bq_err:
            print(f"Failed to set BQ error status: {bq_err}")

@router.post("/upload-sos")
async def upload_sos(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    user_query: Optional[str] = Form(None)
):
    """
    Allows residents to upload geo-tagged photos of flash flood locations.
    Stores photos locally, logs to BigQuery, broadcasts SSE, and kicks off
    background vision analysis.
    """
    # 1. Generate filename and save locally
    file_ext = os.path.splitext(file.filename)[1] or ".png"
    session_id = f"sos_{uuid.uuid4().hex[:8]}"
    filename = f"{session_id}{file_ext}"
    local_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload locally: {e}")
        
    photo_url = f"/static/uploads/{filename}"
    timestamp_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    
    # 2. Pre-seed the distress event row in BigQuery
    row = {
        "session_id": session_id,
        "user_id": "resident",
        "lat": latitude,
        "lng": longitude,
        "detected_depth": None,
        "photo_url": photo_url,
        "status": "pending",
        "timestamp": timestamp_str
    }
    
    try:
        bq_client.insert_rows("active_sos", [row])
    except Exception as e:
        # Cleanup file if DB insert fails
        if os.path.exists(local_path):
            os.remove(local_path)
        raise HTTPException(status_code=500, detail=f"Database logging failure: {e}")
        
    # 3. Broadcast initial SOS alert to all listening map portals
    sos_data = {
        "session_id": session_id,
        "lat": latitude,
        "lng": longitude,
        "photo_url": photo_url,
        "status": "pending",
        "detected_depth": None,
        "severity": "pending",
        "timestamp": timestamp_str
    }
    await sse_manager.broadcast({"event": "new_sos", "data": sos_data})
    
    # 4. Spawn background thread for Vision Agent depth estimation
    background_tasks.add_task(
        analyze_sos_image_background,
        session_id=session_id,
        image_path=local_path,
        lat=latitude,
        lng=longitude,
        photo_url=photo_url,
        timestamp_str=timestamp_str
    )
    
    return {
        "status": "success",
        "sos_id": session_id,
        "photo_url": photo_url,
        "message": " Distress signal logged. Back-end analysis running."
    }
