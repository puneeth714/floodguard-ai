import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google.adk.cli.fast_api import get_fast_api_app

from app.api.resident import router as resident_router
from app.api.official import router as official_router

# Resolve absolute paths to built frontend static files and agents directory
MONOREPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
agents_directory = os.path.join(MONOREPO_ROOT, "backend", "app", "agents")

# Initialize FastAPI app using ADK's native factory with Web UI enabled!
app = get_fast_api_app(
    agents_dir=agents_directory,
    web=True,
    allow_origins=["*"]
)

# Surgically remove ADK's default redirect route at "/" so we can serve our Resident frontend there!
app.router.routes = [r for r in app.router.routes if r.path != "/"]

# Register endpoints routers
app.include_router(resident_router)
app.include_router(official_router)

RESIDENT_DIST = os.path.join(MONOREPO_ROOT, "frontend-resident", "dist")
OFFICIAL_DIST = os.path.join(MONOREPO_ROOT, "frontend-official", "dist")

# Serve dynamic media uploads
UPLOAD_DIR = os.path.join(MONOREPO_ROOT, "backend", "app", "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# Serve built frontend JS/CSS assets
if os.path.exists(RESIDENT_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(RESIDENT_DIST, "assets")), name="resident-assets")
if os.path.exists(OFFICIAL_DIST):
    app.mount("/official/assets", StaticFiles(directory=os.path.join(OFFICIAL_DIST, "assets")), name="official-assets")

# Serve main application entrypoints
@app.get("/official")
@app.get("/official/")
def serve_official():
    index_path = os.path.join(OFFICIAL_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "error", "message": "Official frontend built files not found."}

@app.get("/favicon.svg")
def serve_favicon():
    fav_path = os.path.join(RESIDENT_DIST, "favicon.svg")
    if os.path.exists(fav_path):
        return FileResponse(fav_path)
    return {"status": "error", "message": "Favicon not found."}

@app.get("/")
def serve_resident():
    index_path = os.path.join(RESIDENT_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "online",
        "service": "FloodGuard AI Backend API Services (Resident build not found)",
        "version": "1.0.0"
    }
