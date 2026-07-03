# FloodGuard AI: Predictive Community Disaster Resilience Platform

FloodGuard AI is a predictive, AI-powered Decision Intelligence Platform designed to transition urban disaster management from reactive response to proactive resilience. Built for the GenAI APAC Hackathon, the platform integrates digital elevation models, real-time weather telemetrics, and citizen feedback to deliver actionable safety guidance for residents and command-center analytics for city officials.

---

## 🚀 Key Features

* **For Residents (Mobile & Web)**
  * **Conversational Safety Assistant**: Query local flood risks and receive custom safety checklists.
  * **Dynamic Waypoint Routing**: Recommends safe paths avoiding flooded locations and flyovers, opening directly in native Google Maps with pre-computed waypoint detours.
  * **Multimodal SOS Reporting**: Upload photos of localized flooding to instantly calculate water depth and trigger prioritized rescue signals.

* **For Officials & RWAs (Desktop Dashboard)**
  * **Interactive Command Center**: Real-time Google Maps interface showing active SOS pins, water depths, and drainage networks.
  * **Flood Vulnerability Index Heatmap**: Dynamic terrain analysis displaying relative elevation sinks and precipitation loading.
  * **What-If Hydrological Simulator**: Conversational panel to simulate clearing stormwater drains or deploying pumps.

---

## 🛠️ Technology Stack

* **AI Layer**: Google Agent Development Kit (ADK 2.0), Gemini 3.5 Flash, Gemini 3.5 Flash Vision.
* **Database & RAG**: Google BigQuery, BigQuery Vector Search (grounding PDF guidelines & unstructured feeds).
* **Backend API**: Python FastAPI on Google Cloud Run.
* **Frontends**: Two isolated React SPAs (Vite) styled with Vanilla CSS and using `@vis.gl/react-google-maps`.
* **Geospatial Processing**: Turf.js (frontend) and Shapely (backend polyline intersection checking).

---

## 📂 Folder Structure

```
├── AGENTS.md                          # AI Agent guidelines & custom specs
├── backend/                           # FastAPI Backend
│   ├── app/
│   │   ├── agents/                    # ADK 2.0 Graph & Prompts
│   │   ├── db/                        # BigQuery connectors
│   │   └── tools/                     # Routing, Vision, Weather APIs
│   ├── scripts/                       # Database seeding scripts
│   └── tests/                         # Agent & Tool unit tests
├── frontend-resident/                 # Resident Chat SPA
├── frontend-official/                 # Official Dashboard SPA
├── docs/                              # System Specs & Guidelines
│   ├── system_design_spec.md          # Main Architectural Specification
│   └── demo_constraints.md            # Hackathon assumptions & overrides
├── todo.md                            # Bottom-up project checklist
└── README.md                          # Project Overview (This file)
```

---

## 🚀 Quick Start (Development Sandbox)

### 1. Run the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Run the Resident Frontend
```bash
cd frontend-resident
npm install
npm run dev
```

### 3. Run the Official Frontend
```bash
cd frontend-official
npm install
npm run dev
```
