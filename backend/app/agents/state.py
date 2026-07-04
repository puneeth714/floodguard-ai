"""
state.py

FloodGuard AI
Conversation State

This module defines the shared state that flows between
all AI agents in the ADK Graph.

Every agent receives a ConversationState,
updates only its own fields,
and returns the updated state.

The orchestrator is responsible for passing this state
between agents until the workflow is complete.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Reuse your existing model
from backend.app.tools.vision_models import VisionResult


class ConversationState(BaseModel):
    """
    Shared state exchanged between all AI agents.

    This object represents one complete user session.
    """

    # ==========================================================
    # Session Information
    # ==========================================================

    session_id: str

    user_id: Optional[str] = None

    conversation_id: Optional[str] = None

    role: str = "resident"

    # ==========================================================
    # User Request
    # ==========================================================

    user_query: Optional[str] = None

    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    # ==========================================================
    # User Location
    # ==========================================================

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    destination: Optional[str] = None

    # ==========================================================
    # Image
    # ==========================================================

    image_path: Optional[str] = None

    image_uploaded: bool = False

    # ==========================================================
    # Vision Agent Output
    # ==========================================================

    vision_result: Optional[VisionResult] = None

    # ==========================================================
    # Weather Agent Output
    # ==========================================================

    weather_data: Optional[Dict[str, Any]] = None

    # ==========================================================
    # Geospatial Agent Output
    # ==========================================================

    elevation_data: Optional[Dict[str, Any]] = None

    safe_route: Optional[Dict[str, Any]] = None

    flood_polygons: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    # ==========================================================
    # Policy Agent Output
    # ==========================================================

    policy_documents: List[str] = Field(
        default_factory=list
    )

    mitigation_actions: List[str] = Field(
        default_factory=list
    )

    # ==========================================================
    # Simulation Agent Output
    # ==========================================================

    simulation_result: Optional[Dict[str, Any]] = None

    # ==========================================================
    # Flood Risk
    # ==========================================================

    flood_risk_score: Optional[float] = None

    #flood_severity: Optional[str] = None

    evacuation_required: bool = False

    # ==========================================================
    # Final Response
    # ==========================================================

    final_response: Optional[str] = None

    completed_agents: List[str] = Field(
        default_factory=list
    )

    errors: List[str] = Field(
        default_factory=list
    )


if __name__ == "__main__":

    state = ConversationState(
        session_id="demo-session",
        user_query="Can I drive to the airport?",
        latitude=12.9716,
        longitude=77.5946,
        image_uploaded=True,
        image_path="sample_image.png",
    )

    print(state.model_dump_json(indent=4))