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

import requests

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
    flood depth/severity and saves the completed alert once into BigQuery.
    """
    try:
        print(f"Background Task: Analyzing SOS image {image_path} for session {session_id}...")
        vision_tool = VisionTool()
        vision_result = vision_tool.analyze_flood_image(image_path)
        
        depth = float(vision_result.water_depth_cm)
        severity = vision_result.severity.value  # 'low', 'medium', 'high', 'critical'
        
        print(f"Vision Result: Estimated depth {depth}cm, severity: {severity}")
        
        # 1. Insert completed row into BigQuery (avoids streaming buffer UPDATE constraints!)
        row = {
            "session_id": session_id,
            "user_id": "resident",
            "lat": lat,
            "lng": lng,
            "detected_depth": depth,
            "photo_url": photo_url,
            "status": "active",
            "timestamp": timestamp_str
        }
        bq_client.insert_rows("active_sos", [row])
        
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
        # Insert fallback record in BigQuery
        row = {
            "session_id": session_id,
            "user_id": "resident",
            "lat": lat,
            "lng": lng,
            "detected_depth": 35.0,  # Fallback depth
            "photo_url": photo_url,
            "status": "active_error",
            "timestamp": timestamp_str
        }
        try:
            bq_client.insert_rows("active_sos", [row])
        except Exception as bq_err:
            print(f"Failed to write BQ fallback record: {bq_err}")

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
    Stores photos locally, broadcasts initial SSE event, and delegates
    BQ insertion and vision analysis to background task.
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
    
    # 2. Broadcast initial SOS alert to all listening map portals (before BigQuery insert finishes)
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
    
    # 3. Spawn background thread to perform single database insert and vision analysis
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

@router.get("/reverse-geocode")
def reverse_geocode(latitude: float, longitude: float):
    """
    Reverse geocodes latitude/longitude coordinates into a friendly address string.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"formatted_address": f"GPS Area ({latitude:.4f}, {longitude:.4f})"}
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "OK" and data.get("results"):
            return {"formatted_address": data["results"][0]["formatted_address"]}
    except Exception as e:
        print(f"Reverse geocode error: {e}")
    return {"formatted_address": f"GPS Area ({latitude:.4f}, {longitude:.4f})"}

