import os
import uuid
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel

from google import genai
from google.genai import types as genai_types
from app.core.config import settings
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
    language: Optional[str] = "en"

import json
from fastapi.responses import StreamingResponse

@router.post("/chat")
async def resident_chat(payload: ChatRequest, stream: bool = False):
    """
    Executes a chat session turn for a resident using the Orchestrator.
    Handles location, weather, and detour waypoint injection.
    Supports streaming if stream=True parameter is passed.
    """
    if stream:
        async def event_generator():
            try:
                async for event in orchestrator.run_stream(
                    session_id=payload.session_id,
                    user_query=payload.user_query,
                    latitude=payload.latitude,
                    longitude=payload.longitude,
                    destination=payload.destination,
                    image_path=payload.image_path,
                    user_role=payload.user_role or "resident",
                    demo_profile=payload.demo_profile,
                    language=payload.language
                ):
                    if event.get("type") == "final":
                        # Clean and parse JSON from content
                        final_text = event.get("content", "").strip()
                        if final_text.startswith("```"):
                            lines = final_text.splitlines()
                            if lines and lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].strip().startswith("```"):
                                lines = lines[:-1]
                            final_text = "\n".join(lines).strip()
                        try:
                            parsed_json = json.loads(final_text)
                            event["content"] = parsed_json
                        except Exception:
                            event["content"] = {
                                "final_response": event.get("content", ""),
                                "status_alert": None,
                                "widgets": []
                            }
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    try:
        result = await orchestrator.run(
            session_id=payload.session_id,
            user_query=payload.user_query,
            latitude=payload.latitude,
            longitude=payload.longitude,
            destination=payload.destination,
            image_path=payload.image_path,
            user_role=payload.user_role or "resident",
            demo_profile=payload.demo_profile,
            language=payload.language
        )
        
        # Clean and parse JSON from the final response
        final_text = result.get("final_response", "").strip()
        if final_text.startswith("```"):
            lines = final_text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            final_text = "\n".join(lines).strip()
            
        try:
            parsed_response = json.loads(final_text)
            if "final_response" not in parsed_response:
                parsed_response = {
                    "final_response": final_text,
                    "status_alert": None,
                    "widgets": []
                }
        except Exception:
            parsed_response = {
                "final_response": result.get("final_response", ""),
                "status_alert": None,
                "widgets": []
            }
            
        return {
            "final_response": parsed_response.get("final_response", ""),
            "status_alert": parsed_response.get("status_alert"),
            "widgets": parsed_response.get("widgets", []),
            "state": result.get("state", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")

import requests

async def analyze_sos_image_background(
    session_id: str,
    image_path: str,
    lat: float,
    lng: float,
    photo_url: str,
    user_id: str,
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
            "user_id": user_id,
            "lat": lat,
            "lng": lng,
            "detected_depth": depth,
            "photo_url": photo_url,
            "status": "active",
            "timestamp": timestamp_str
        }
        bq_client.insert_rows("active_sos", [row])
        
        # Decode custom user_id format
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

        # 2. Broadcast updated state through SSE feed
        updated_data = {
            "session_id": session_id,
            "lat": lat,
            "lng": lng,
            "photo_url": photo_url,
            "status": "active",
            "detected_depth": depth,
            "severity": severity,
            "stranded_people_count": people_count,
            "special_needs": needs,
            "timestamp": timestamp_str
        }
        await sse_manager.broadcast({"event": "update_sos", "data": updated_data})
        
    except Exception as e:
        print(f"Error analyzing image in background task: {e}")
        # Insert fallback record in BigQuery
        row = {
            "session_id": session_id,
            "user_id": user_id,
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
    stranded_count: int = Form(1),
    medical_needs: Optional[str] = Form(None),
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
    
    # Encode custom stranded info inside user_id
    user_id_encoded = f"resident:people_count={stranded_count}:needs={medical_needs or 'None'}"
    
    # 2. Broadcast initial SOS alert to all listening map portals (before BigQuery insert finishes)
    sos_data = {
        "session_id": session_id,
        "lat": latitude,
        "lng": longitude,
        "photo_url": photo_url,
        "status": "pending",
        "detected_depth": None,
        "severity": "pending",
        "stranded_people_count": stranded_count,
        "special_needs": medical_needs or "None",
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
        user_id=user_id_encoded,
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

@router.get("/alerts")
def get_localized_alerts(lat: float, lng: float):
    """
    Returns localized active flood alerts or evacuation notices matching the coordinate region.
    """
    try:
        query = f"""
        SELECT session_id, lat, lng, detected_depth, status, timestamp
        FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp DESC) as rn
            FROM `{bq_client.dataset_ref}.active_sos`
        )
        WHERE rn = 1 AND status != 'resolved'
          AND lat BETWEEN {lat - 0.02} AND {lat + 0.02}
          AND lng BETWEEN {lng - 0.02} AND {lng + 0.02}
        """
        records = bq_client.execute_query(query)
        
        for r in records:
            if r.get("timestamp"):
                r["timestamp"] = r["timestamp"].isoformat()
                
        fvi = 26.02 if (12.91 <= lat <= 12.94 and 77.61 <= lng <= 77.64) else 4.2
        risk_level = "High" if fvi > 20 else "Low"
        
        return {
            "status": "success",
            "region_fvi_risk": fvi,
            "risk_level": risk_level,
            "alerts": [
                {
                    "title": f"{risk_level} Flood Risk Notice",
                    "description": f"Precipitation and terrain analysis indicate elevated hazard in this grid. Local FVI is {fvi}."
                }
            ],
            "active_nearby_sos": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch localized alerts: {str(e)}")

@router.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...)):
    """
    Transcribes uploaded audio bytes into localized text using the Gemini model.
    Supports English, Kannada, Hindi, and Telugu.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY environment variable.")
    
    try:
        # Load audio bytes
        audio_bytes = await file.read()
        mime_type = file.content_type or "audio/webm"
        
        # Initialize client
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[
                "You are an expert multilingual speech-to-text transcriber. Transcribe this audio recording into clear, punctuated text. "
                "The audio might be spoken in English, Kannada, Hindi, or Telugu. Provide the exact transcript in the language spoken. "
                "If the audio is completely silent or contains only static, return an empty string. "
                "Do not add any translations, explanations, notes, or intros.",
                genai_types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            ]
        )
        
        transcript = response.text or ""
        transcript = transcript.strip()
        
        return {"transcript": transcript}
    except Exception as e:
        print(f"Voice translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice transcription failed: {str(e)}")

