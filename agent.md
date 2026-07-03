# AI Developer Agent Instructions: FloodGuard AI

This document provides developer guidelines, project context, and instructions for AI coding assistants (like Antigravity) working in this repository.

---

## 🎯 Project Mission
Our goal is to build **FloodGuard AI**, an AI-powered Decision Intelligence Platform for monsoonal urban resilience (using Bengaluru as the baseline scenario). The system utilizes **ADK 2.0** for agent orchestration, **BigQuery** for databases and vector searches, and a dual-frontend **React (Vite) + Vanilla CSS** structure.

---

## 🛠️ Tech Stack & Coding Standards

### 1. Backend (Python + FastAPI)
* **Framework**: FastAPI (python-based, deployed to Google Cloud Run).
* **AI Orchestration**: Google Agent Development Kit (ADK 2.0). All graphs are state-based and non-linear.
* **Database**: `google-cloud-bigquery` for structured data and `BigQuery Vector Search` for RAG.
* **Libraries**: `shapely` and `polyline` for backend geospatial calculations (alternative route filtering).

### 2. Frontend (React + Vanilla CSS)
* **Framework**: React Vite SPA (separate apps for Resident and Official).
* **Styling**: **Vanilla CSS strictly**. Avoid Tailwind CSS unless the user explicitly requests it.
* **Maps**: Google Maps JavaScript API via `@vis.gl/react-google-maps`.
* **Aesthetics**: Premium, dark-themed, glassmorphic visual designs with micro-animations.

---

## 🚦 Development Strategy (Bottom-Up)
Always follow the **bottom-up approach** as defined in `todo.md`:
1. **Data Layer**: Populate BigQuery with low-lying coordinates, stormwater drains, and active flood polygons.
2. **Geospatial & Vision Tools**: Code the standalone Python tools (route polyline checks, elevation lookups, Gemini Vision water depth estimators) and verify them using local tests before binding them to agents.
3. **Agent Graph (ADK 2.0)**: Define state properties and agent node bindings, validating query transitions via local CLI scripts.
4. **FastAPI Controllers**: Implement API routing with SSE (Server-Sent Events) live updates.
5. **Vite Frontends**: Build the user-facing Resident Chat and Official Dashboard screens.

---

## 🤖 Rules for Agent Behaviors
* **Documentation**: Preserve all existing comments and docstrings.
* **No Placeholders**: Never write mock comments like `# TODO: implement this later`. Complete the implementation fully.
* **Self-Verification**: After writing backend tools, run the corresponding script in `backend/tests/` to verify logic.
* **Links**: Always use standard absolute markdown links (`file:///...`) when referencing workspace files or logs.
