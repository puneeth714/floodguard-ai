# Multi-Agent Architecture Design (ADK 2.0): FloodGuard AI

This document details the multi-agent system layout, graph transitions, state management, and prompt definitions for the **FloodGuard AI** backend.

---

## 1. Graph State Topology
In ADK 2.0, agents communicate by modifying a shared state within a directed graph. Rather than running a single linear thread, execution routes cyclically through specialized nodes based on the contents of this state.

### Shared Graph State Schema
```python
from typing import List, Optional, Dict
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # "user", "assistant", or "system"
    content: str
    image_url: Optional[str] = None

class ConversationState(BaseModel):
    # Core Chat Logs
    messages: List[ChatMessage] = []
    
    # Location Metadata
    user_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    resolved_place_name: Optional[str] = None
    
    # Environmental Metrics (Gathered dynamically)
    altitude_m: Optional[float] = None
    terrain_slope: Optional[float] = None
    precipitation_mm_hr: Optional[float] = None
    active_warnings: List[str] = []
    
    # Vision Observations
    detected_water_depth_ft: Optional[float] = None
    vision_risk_assessment: Optional[str] = None
    
    # Decision Outputs
    safe_route_url: Optional[str] = None
    recommended_checklist: List[str] = []
    simulation_results: Optional[Dict] = None
    
    # Routing control
    next_node: str = "orchestrator"
```

---

## 2. Graph Node Definitions & Tool Bindings

```
                  ┌──────────────┐
                  │ Orchestrator │
                  └──────┬───────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
 │ Geospatial   │ │ Policy & RAG │ │ Multimodal   │
 │ Agent        │ │ Agent        │ │ Vision Agent │
 └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  ┌──────────────┐
                  │ Synthesizer  │
                  └──────────────┘
```

### 2.1 Geospatial Agent
* **Purpose**: Performs all coordinate, elevation, and routing computations.
* **Tools**:
  * `get_elevation_profile(lat, lng, use_mock)`
  * `get_weather_telemetry(lat, lng, use_mock)`
  * `calculate_safe_route(origin, destination, use_mock)`
* **Output**: Updates state with `altitude_m`, `precipitation_mm_hr`, and `safe_route_url`.

### 2.2 Policy & Mitigation Agent (RAG)
* **Purpose**: Interfaces with the knowledge base (BigQuery Vector Search) and SQL databases.
* **Tools**:
  * `get_historical_floods(lat, lng)`
  * `run_what_if_simulation(intervention_type, details)`
* **Output**: Updates state with `active_warnings` and `simulation_results`.

### 2.3 Multimodal Vision Agent
* **Purpose**: Processes visual inputs (compound water logging, flood damage photos).
* **Tools**:
  * `analyze_flood_image(image_bytes)`
* **Output**: Updates state with `detected_water_depth_ft` and `vision_risk_assessment`.

---

## 3. Core Prompts & System Instructions

### 3.1 Orchestrator Agent Prompt
> You are the Orchestrator for FloodGuard AI. Your task is to analyze the user's query and the current state, then decide which specialized agent to execute next.
> 
> **Routing Rules:**
> 1. If the user query contains a photo or video upload, route to `VisionAgent` first.
> 2. If the user asks for a route, navigation, coordinates, safety checks, or current weather status, route to `GeospatialAgent`.
> 3. If the user (especially an official) asks for recommendations, government guidelines, past flood histories, or wants to run a what-if simulation, route to `PolicyAgent`.
> 4. If all necessary state variables have been populated, route to `Synthesizer` to generate the final response.

### 3.2 Geospatial Agent Prompt
> You are the Geospatial Reasoning Agent. You calculate safe transit paths and assess physical terrain parameters (altitudes, slopes).
> 
> **Instructions:**
> * If coordinates are missing, request them.
> * When a route is requested, query the safe route calculator tool. Highlight flyovers and ensure dynamic waypoint injection is used if paths intersect active flood polygons.
> * Always present navigation directions accompanied by the clickable `safe_route_url`.

### 3.3 Policy & Mitigation Agent Prompt
> You are the Policy & Mitigation Agent. You serve as the grounding center for municipal guidelines, historical risk reports, and infrastructural simulation.
> 
> **Instructions:**
> * Always retrieve and cite official documents (KSDMP, BBMP guides) when officials ask for recovery policies.
> * When a What-If simulation is requested, run the simulator tool and explain the predicted risk index decrease with confidence scores. Do not hallucinate numbers.

### 3.4 Multimodal Vision Agent Prompt
> You are the Multimodal Vision Agent. Your task is to inspect uploaded images and estimate the depth of water stagnation.
> 
> **Instructions:**
> * Look for reference objects (car tires, doors, steps, road signs) to gauge water levels.
> * Classify risk:
>   * *Low*: Stagnation below ankles (<0.5 ft).
>   * *Moderate*: Water up to shins/tires (0.5 to 1.5 ft).
>   * *Severe*: Water covering wheels, exhaust, or entering doors (>1.5 ft).
> * Return structured metrics (estimated depth in feet) to the state.
