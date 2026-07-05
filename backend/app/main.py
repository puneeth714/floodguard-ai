import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.resident import router as resident_router
from app.api.official import router as official_router

app = FastAPI(
    title="FloodGuard AI API Gateway",
    description="Decision Intelligence Platform for Urban Monsoon Flood Resilience",
    version="1.0.0"
)

# Configure CORS for both Resident React App and Official React Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints routers
app.include_router(resident_router)
app.include_router(official_router)

# Mount the static directory to serve uploaded resident photos (e.g. SOS images)
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "FloodGuard AI Backend API Services",
        "version": "1.0.0"
    }
