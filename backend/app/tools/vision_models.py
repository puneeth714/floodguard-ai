"""
FloodGuard AI
Vision Tool Data Models

This module contains all request/response models used by the
Vision Tool.

These models are intentionally independent of Vertex AI,
Gemini, FastAPI and ADK so they can be reused across the
entire backend.

"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# ENUMS
# ============================================================

class FloodSeverity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RescuePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    IMMEDIATE = "IMMEDIATE"


class RoadCondition(str, Enum):
    CLEAR = "CLEAR"
    PARTIALLY_BLOCKED = "PARTIALLY_BLOCKED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


# ============================================================
# INPUT MODEL
# ============================================================

class VisionRequest(BaseModel):
    """
    Input sent to the Vision Tool.

    This model is passed from the API layer to the
    Vision Tool.
    """

    image_bytes: bytes

    latitude: Optional[float] = Field(
        default=None,
        description="Latitude where image was captured."
    )

    longitude: Optional[float] = Field(
        default=None,
        description="Longitude where image was captured."
    )

    session_id: Optional[str] = None
    user_id: Optional[str] = None


# ============================================================
# OUTPUT MODEL
# ============================================================

class VisionResult(BaseModel):
    """
    Structured response returned by the Vision Tool.

    This is consumed by the AI Orchestrator.
    """

    water_depth_cm: float = Field(
        ge=0,
        description="Estimated flood water depth in centimeters."
    )

    severity: FloodSeverity

    rescue_priority: RescuePriority

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score returned by AI model."
    )

    road_condition: RoadCondition

    road_blocked: bool

    vehicle_detected: bool

    vehicle_submerged: bool

    people_detected: bool

    property_damage: bool

    recommendations: List[str] = Field(
        default_factory=list
    )

    summary: str


# ============================================================
# API RESPONSE WRAPPER
# ============================================================

class VisionResponse(BaseModel):
    """
    Standard response returned to the API layer.
    """

    success: bool

    result: Optional[VisionResult] = None

    error: Optional[str] = None


# ============================================================
# MOCK RESPONSE
# Used while Vertex AI is unavailable.
# ============================================================

def get_mock_result() -> VisionResult:
    """
    Returns a sample response for development/demo.

    This allows the frontend and orchestrator to be
    developed before Vertex AI integration.
    """

    return VisionResult(
        water_depth_cm=42.5,
        severity=FloodSeverity.HIGH,
        rescue_priority=RescuePriority.HIGH,
        confidence=0.94,
        road_condition=RoadCondition.BLOCKED,
        road_blocked=True,
        vehicle_detected=True,
        vehicle_submerged=False,
        people_detected=False,
        property_damage=True,
        recommendations=[
            "Avoid this route.",
            "Use alternate road.",
            "Notify local authorities.",
            "Do not drive through standing water."
        ],
        summary=(
            "Flood water approximately 42 cm deep. "
            "Road is unsafe for passenger vehicles."
        )
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    response = VisionResponse(
        success=True,
        result=get_mock_result()
    )

    print(response.model_dump_json(indent=4))