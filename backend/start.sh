#!/bin/sh
# Launch the main FastAPI application gateway serving ADK Web UI and our frontend dashboards
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
