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

from fastapi.responses import FileResponse

# Register endpoints routers
app.include_router(resident_router)
app.include_router(official_router)

# Resolve absolute paths to built frontend static files
MONOREPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

import httpx
from fastapi import Request
from fastapi.responses import Response, HTMLResponse

@app.api_route("/adk/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
async def proxy_adk_web(request: Request, path: str):
    """
    Proxies requests from /adk/... directly to the local adk web server running on port 8001.
    """
    async with httpx.AsyncClient() as client:
        url = f"http://127.0.0.1:8001{request.url.path}"
        
        params = dict(request.query_params)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        body = await request.body()
        
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                params=params,
                headers=headers,
                content=body,
                timeout=120.0
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except Exception as e:
            return HTMLResponse(content=f"<h3>ADK Web Server Offline</h3><p>{e}</p>", status_code=502)


