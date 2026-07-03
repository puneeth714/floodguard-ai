# FloodGuard AI — Agent Instructions

This document provides standardized instructions, environment details, and guardrails for AI coding agents (such as Gemini, Cursor, or Aider) working in this repository.

---

## Overview
FloodGuard AI is a predictive, AI-powered Decision Intelligence Platform designed for urban monsoon flood resilience. It features a FastAPI backend running a graph-based multi-agent system (ADK 2.0) and two separate React (Vite) frontend applications (Resident Chat and Official Dashboard).

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
