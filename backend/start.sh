#!/bin/sh
# Start the ADK Web UI server in the background, bound locally on port 8001
adk web --port 8001 --host 127.0.0.1 --url_prefix /adk app/agents &

# Wait briefly for ADK to boot
sleep 2

# Launch the main FastAPI application gateway in the foreground
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
