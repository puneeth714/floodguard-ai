# Product Specification Document: FloodGuard AI

---

## 1. Product Overview & Problem Statement
Every monsoon season, rapidly developing urban hubs in APAC—most notably Bengaluru—face intense monsoonal cloudbursts. Rapid precipitation loads overwhelm municipal drainage channels, creating localized stagnation hotspots (waterlogging), gridlocking traffic, damaging property, and threatening lives. 

Traditional disaster response is **reactive**: citizens only learn of waterlogging once they get stuck, and municipal officials react blindly based on delayed citizen calls rather than real-time telemetry.

**FloodGuard AI** is a predictive, AI-powered Decision Intelligence Platform designed to shift flood management from reactive chaos to proactive resilience. 

---

## 2. Key Value Propositions
*   **Persona-Aware Intelligence**: Tailored interfaces and role-based agent safety guidelines for Residents (evacuation-focused) and Officials (management-focused).
*   **Predictive Decision Models**: Combines topography (altitude sinks) and dynamic weather radar coordinates to compute a localized Flood Vulnerability Index (FVI).
*   **Bi-Directional Action Loop**: Residents submit multimodal distress telemetry (stranded count, medical needs), which instantly populate the official dashboard, allowing officials to dispatch help and push real-time status updates back to residents.

---

## 3. Core Feature Specification

### 3.1 Resident Portal (Mobile-First Web SPA)
*   **Demo Persona Selector**: Dropdown to switch between Rajesh (high-risk Sector 4), Radha (low-risk Sector 2), and Anonymous. Anonymous users are assigned a persistent session UUID cached in `localStorage`.
*   **GPS Telemetry Sync & Geocoding**: Automatically updates the welcome interface and logs coordinates. Resolves raw GPS telemetry into street addresses using reverse geocoding.
*   **Safe Navigation Waypoint Bypass**: Detects when standard navigation paths cross active flood polygons. Avoids waterlogging by calculating intermediate detour coordinates, rendering a styled TURN-BY-TURN navigation button that opens Google Maps directly.
*   **Emergency SOS Broadcast**: Residents can upload a flood photo, input the number of stranded people, and describe special medical needs.

### 3.2 Official Command Console (Desktop Web Split-Screen)
*   **Left-Panel Map Dashboard**: Uses the Google Maps JS API to visualize:
    *   *FVI Heatmap Layer*: Visualizes grid-cell flood vulnerability.
    *   *Stopped/Active Water Pumps*: Plotting pump stations, flow capacities, and toggles to start/stop pumps.
    *   *Blocked/Cleared Storm Drains*: Indicating municipal blockages.
    *   *Weather Radar circles*: Highlighting rainfall intensity.
    *   *Real-time SOS Distress Pins*: Categorized by severity, displaying resident photos, stranded counts, and medical needs.
*   **Right-Panel Conversational Console**:
    *   *What-If Simulation Engine*: Run conversational simulations (e.g. *"What happens if we desilt these 3 drains?"*) to see FVI changes update on the map in real-time.
    *   *Disaster RAG guidelines search*: Query official BBMP/KSDMP procedures.
    *   *PDF Briefing Generator*: Download compiled incident briefings directly as Markdown files.

---

## 4. Architectural & Agent Integration
The platform runs a graph-based multi-agent system (ADK 2.0) serving:
*   **Orchestrator Agent**: Manages context, tracks roles, and handles node transitions.
*   **Geospatial Reasoning Agent**: Resolves telemetry, checks routes, and calculates waypoints.
*   **Policy & Mitigation Agent**: Connects to BigQuery Vector Search and ML models to run desilting/pump simulations.
*   **Multimodal Vision Agent**: Estimates flood water depth (cm) and severity from uploaded images.

All entity state records are logged in BigQuery using an append-only architecture, ensuring zero database streaming buffer conflicts.
