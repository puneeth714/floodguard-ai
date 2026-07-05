# FloodGuard AI: Bottom-Up Project TODO List & Submission Roadmap

This document outlines the modular tasks, timelines, and verification steps required to build **FloodGuard AI** for the GenAI APAC Hackathon using a **Bottom-Up Development Approach** (validating core data and tools before building agent logic, APIs, and user interfaces).

---

## 📅 High-Level Bottom-Up Roadmap
* **Step 1 (Day 1)**: Database & Mock Data Seeding (BigQuery + Local Sandbox)
* **Step 2 (Day 1-2)**: Core Python Utility Tools & Spatial Calculations (Shapely, Polyline)
* **Step 3 (Day 2)**: ADK 2.0 Graph Flow & Agent Logic
* **Step 4 (Day 2)**: FastAPI API Controllers & Event Streams
* **Step 5 (Day 3)**: Frontends (Vite React Apps & Map Dashboards)
* **Step 6 (Day 4 - July 6)**: Cloud Deployment, Pitch Deck, Video Demo, and Submission

---

## 🛠️ Modular Bottom-Up Phases

### Step 1: Database Layer & Mock Data Seeding (Day 1)
*Goal: Initialize data storage schemas and populate mock datasets in BigQuery (or a local developer sandbox database) to supply inputs to our tools.*
- [x] **1.1 Directory Initialization**
  - [x] Create monorepo directory layout:
    - `/backend` (FastAPI + Python ADK Code)
    - `/frontend-resident` (Resident Chat React SPA)
    - `/frontend-official` (Official Dashboard React SPA)
  - [x] Verify `AGENTS.md` is initialized at the root containing all custom requirements (ADK 2.0 graph routing, BigQuery RAG setup, waypoint injection, FVI scoring, resident/official APIs).
- [x] **1.2 Database Schema Creation**
  - [x] Initialize BigQuery dataset `floodguard_db` (or sandbox alternative).
  - [x] Create table schemas:
    - `vulnerability_grids`: Columns for Latitude, Longitude, Altitude, Slope, and Baseline Drainage.
    - `drainage_network`: Points of BBMP stormwater drains with `blocked`/`cleared` status.
    - `active_sos`: Real-time distress logs (session_id, coordinates, depth, photo_url, timestamp, status).
- [x] **1.3 Mock Data Insertion & Validation**
  - [x] Write Python seeding script `/backend/scripts/seed_mock_data.py` to:
    - Ingest BBMP low-lying KML/CSV coordinates.
    - Define and pre-seed active flood polygons (Silk Board and Bellandur coordinates).
    - Cache altitude values for 100+ key grid coordinates in Bengaluru.
  - [x] **Verification**: Run raw SQL queries to confirm datasets are active and retrievable.
- [x] **1.4 Google Cloud Storage Integration**
  - [x] Set up GCS Bucket `floodguard-assets-501409` (configured local directory storage fallback for sandbox).
  - [x] Implement GCS file handler wrapper/fallback to upload/download binary image files (user uploads & Places photos).

---

### Step 2: Core Python Utility Tools & Spatial Calculations (Day 1 - 2)
*Goal: Write and unit-test the low-level functions that perform mathematical, geospatial, and vision actions before putting them into AI agents.*
- [x] **2.1 Spatial Route Filtering**
  - [x] Write route avoidance logic:
    - Receive source and destination coordinates.
    - Decode polyline paths returned by Google Maps Routes API into standard coordinate lists.
    - Use `shapely` to perform intersection checks between decoded paths and active flood polygons.
    - Filter out blocked routes and calculate detours using safe intermediate waypoint injection.
- [x] **2.2 Weather & Elevation Adapters**
  - [x] Write `get_weather_telemetry` to fetch hourly precipitation (with mock telemetry overrides).
  - [x] Write `get_elevation_profile` to resolve terrain altitudes using cache fallbacks.
- [x] **2.3 Gemini Vision Analyzer**
  - [x] Write image processor to send user-uploaded photos to Gemini 3.5 Flash Vision to classify water depth and hazard severity.

- [x] **2.4 Hydrological Simulator**
  - [x] Write parametric calculation logic to predict FVI reduction when pumps/drains are modified.
  - [x] **Verification**: Run standalone Python test script `/backend/tests/test_tools.py` to verify routes avoid the mock Silk Board flood polygon and return correct waypoint deep-links.

---

### Step 3: ADK 2.0 Graph Flow & Agent Orchestration (Day 2)
*Goal: Integrate the functional tools into specialized agents and build the non-linear ADK 2.0 state machine graph.*
- [x] **3.1 Graph State Definition**
  - [x] Define the shared `ConversationState` structure (thread history, coordinates, detected depth, FVI risk score, and current route links).
- [x] **3.2 Agent Node Bindings**
  - [x] Bind tools to the specialized agents:
    - `GeospatialAgent` $\rightarrow$ Elevation, Routing, Waypoint compilation.
    - `PolicyAgent` $\rightarrow$ Guideline PDF search, What-if SQL simulations.
    - `VisionAgent` (Pending: Vennela) $\rightarrow$ Gemini Vision image analysis.
- [x] **3.3 Graph Flow Implementation**
  - [x] Design the cyclic flow routing in `/backend/app/agents/graph.py`.
  - [x] Set up Orchestrator conditions to sequentially execute multiple agent nodes when inputs require multi-step reasoning.
  - [x] **Verification**: Run test script `/backend/tests/test_agents.py` via command line to verify chat output and agent transitions.


---

### Step 4: FastAPI Web Controllers & Event Streams (Day 2)
*Goal: Expose the ADK 2.0 graph and database summaries as secure, role-separated API endpoints.*
- [x] **4.1 Resident APIs**
  - [x] Expose `POST /api/resident/chat` (receives session_id, history, and location).
  - [x] Expose `POST /api/resident/upload-sos` (logs image bytes and flags active SOS points).
- [x] **4.2 Official APIs**
  - [x] Expose `POST /api/official/chat` (administrative RAG and simulations).
  - [x] Expose `GET /api/official/dashboard-summary` (JSON of active alerts, pumps, and drains).
  - [x] Expose `GET /api/official/live-sos-feed` using Server-Sent Events (SSE) to stream active SOS uploads from residents.
  - [x] **Verification**: Run FastAPI API tests (`tests/test_api.py`) to verify all controller routes return correct JSON payloads and streaming responses.


---

### Step 5: Frontend Development & API Integration (Day 3)
*Goal: Build user interfaces for Residents (chat & SOS) and Officials (maps JS & dashboards) and connect them to the FastAPI backend.*
- [ ] **5.1 Resident Chat Application**
  - [ ] Initialize React Vite SPA, design dark UI style guidelines.
  - [ ] Implement Resident Profile Switcher (Rajesh/Radha/Anonymous coordinates).
  - [ ] Implement "Mock Simulation" toggle header switch to force heavy rain and detour mock checks.
  - [ ] Connect chat panel to `/api/resident/chat` and SOS button to `/api/resident/upload-sos`.
- [ ] **5.2 Official command center Dashboard**
  - [ ] Initialize React Vite SPA, build desktop split-screen interface.
  - [ ] Implement "Mock Simulation" toggle header switch to bypass active cloud calls.
  - [ ] Map panel: Integrate `@vis.gl/react-google-maps`, add heatmap layer (FVI), dynamic markers (active alert pins with photo models), and pre-seeded flood polygons.
  - [ ] Chat panel: Add sidebar console connected to `/api/official/chat` for What-If queries.
  - [ ] Real-time integration: Connect maps state to SSE feed to animate incoming alerts.

---

### Step 6: Integration, Cloud Deployment & Submission (Day 4 - July 6)
*Goal: End-to-end testing of the user journeys, deploying the platform, and compiling submission materials.*
- [ ] **6.1 End-to-End Integration Testing**
  - [ ] Walk through the narrative: Rajesh requests checklists $\rightarrow$ Rajesh navigates safely $\rightarrow$ Radha uploads flood photo $\rightarrow$ Alert streams to Official dashboard $\rightarrow$ Official runs what-if simulation.
- [ ] **6.2 Google Cloud Run Deployment**
  - [ ] Package FastAPI into a Docker container, deploy to Cloud Run.
  - [ ] Deploy frontends (Resident & Official) to Vercel/Netlify.
  - [ ] Migrate local image storage to GCS bucket upload (switch from local uploads static folder).

- [ ] **6.3 Pitch & Presentation Materials**
  - [ ] Compile Presentation slides (GCP Architecture, ADK 2.0 Graph, Spatial detour math).
  - [ ] Record a 5-minute screencast demonstrating the Rajesh/Radha story.
  - [ ] Finalize code cleanup, write `README.md` setup guidelines, and upload to the hackathon submission portal before July 6, 11:59 PM IST.
