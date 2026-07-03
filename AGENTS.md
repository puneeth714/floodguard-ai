# FloodGuard AI — Agent Instructions

This document provides standardized instructions, environment details, custom project requirements, and guardrails for AI coding agents (such as Gemini, Cursor, or Aider) working in this repository.

---

## Overview
FloodGuard AI is a predictive, AI-powered Decision Intelligence Platform designed for urban monsoon flood resilience. It features a FastAPI backend running a graph-based multi-agent system (ADK 2.0) and two separate React (Vite) frontend applications (Resident Chat and Official Dashboard).

---

## Custom Project Requirements

### 1. Multi-Agent Architecture (ADK 2.0 Graph)
The backend must run a non-linear, state-based graph to orchestrate specialized agents via a shared `ConversationState`:
* **Orchestrator Agent**: Inspects inputs, maintains thread history, and routes execution through the graph.
* **Geospatial Reasoning Agent**: Resolves coordinates, fetches elevations, performs route polygon intersections, and generates waypoint deep-links.
* **Policy & Mitigation Agent**: Grounded via BigQuery Vector Search on disaster guidelines (KSDMP, BBMP) and executes what-if database simulations.
* **Multimodal Vision Agent**: Uses Gemini 3.5 Flash Vision to estimate flood depth from compound photos.

### 2. BigQuery Data Strategy (Unified RAG & Database)
* **Single Database Engine**: Use Google BigQuery for both structured transactional logs, analytical tables, and vector embeddings (avoid pgvector/AlloyDB to minimize latency and infrastructure overhead).
* **Vector Tables**: Store document chunks (PDF guidelines) and community report embeddings directly in BigQuery tables using `BigQuery Vector Search`.

### 3. Dual UI Frontends
* **Resident Application (Mobile-first chat)**:
  * Sleek dark-mode interface with quick-clickable template questions.
  * **Demo Profile Switcher**: Header selector to switch between Rajesh (HSR Layout), Radha (Sector 4), and Anonymous (UUID stored in `localStorage`).
  * Clickable route response buttons that redirect to native Google Maps.
* **Official Command Center (Desktop split-screen)**:
  * **Left Panel**: Interactive map using `@vis.gl/react-google-maps` displaying FVI heatmaps, active flash SOS pins, water pumps, and stormwater drains.
  * **Right Panel**: Conversational sidebar chat for What-If scenarios and downloading markdown brief reports.
  * **Real-time Synchronization**: A Server-Sent Events (SSE) or WebSocket route `/api/official/live-sos-feed` to stream new resident SOS updates directly onto the map.

### 4. Custom Algorithms
* **Flood Vulnerability Index (FVI)**:
  $$V = (w_{elev} \times \Delta E) + (w_{slope} \times S) + (w_{rain} \times R) + (w_{drain} \times D)$$
  * Calculated in BigQuery; values over a critical threshold are marked as active flood zone polygons.
* **Waypoint Navigation Injection**:
  * Decode Google Maps alternative polylines, check intersections with flood polygons using `shapely` (Turf.js frontend equivalent), and filter out blocked paths.
  * If all routes are blocked, calculate a safe detour coordinate and inject it as a waypoint query parameter in the universal Google Maps link format:
    `https://www.google.com/maps/dir/?api=1&origin={lat,lng}&destination={lat,lng}&waypoints={safe_lat,safe_lng}&travelmode=driving`

---

## Build & Run

### Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Resident Frontend Setup (React Vite)
```bash
cd frontend-resident
npm install
npm run dev
```

### Official Frontend Setup (React Vite)
```bash
cd frontend-official
npm install
npm run dev
```

---

## Testing
To run the backend unit tests for tools and agent routing, execute the following from the `/backend` directory:
```bash
python -m unittest discover tests/
```

---

## Project Structure
* `/backend/app/agents/`: Multi-agent definitions, ADK 2.0 graph states, and prompts.
* `/backend/app/tools/`: Integration files for weather, elevation, routing, and vision.
* `/backend/app/db/`: BigQuery and vector search client connections.
* `/backend/scripts/`: Sandbox and mock database seeding operations.
* `/frontend-resident/`: Sleek, mobile-first chat UI and SOS upload handlers.
* `/frontend-official/`: Desktop dashboard split-screen featuring Google Maps JS API and admin console.
* `/docs/`: Main specs, system design specifications, and demo constraints documents.

---

## Code Style
* **Backend**: Standard Python type hints, Pydantic v2 schemas for request validations, and async route definitions.
* **Frontend**: React hooks, modular components, and **Vanilla CSS strictly** for all styling.
* **Database**: Explicit SQL queries utilizing parameter bindings for BigQuery interactions.

---

## Boundaries

### ✓ Always Do:
* Stage modifications and write standalone tests under `backend/tests/` to verify spatial formulas.
* Maintain clean comments and keep existing docstrings intact.
* Use absolute file links using the `file://` scheme when referencing files (e.g. `[main.py](file:///home/puneeth/programmes/genai_apac/cohort2/backend/app/main.py)`).
* Use the **bottom-up approach** (Data $\rightarrow$ Tools $\rightarrow$ Graph $\rightarrow$ API $\rightarrow$ Frontend) when building new features.

### ⚠️ Ask First:
* Before adding new third-party dependencies to `requirements.txt` or `package.json`.
* Before modifying the database schemas in BigQuery.
* Before restructuring the agent graph topology.

### ❌ Never Do:
* **Never use Tailwind CSS** unless the user explicitly requests it.
* Never leave placeholders (e.g., `# TODO`, `// implement later`) in code. Implement tasks fully.
* Never write code files or temporary test scripts outside the workspace directory.
