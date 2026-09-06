"""
CrediFlow Main FastAPI Application
Serves the compliance engine API and integrates with the frontend dashboard.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response

from .api.routes import router as api_router

app = FastAPI(
    title="CrediFlow API",
    description="Deterministic GST ITC Compliance & Multi-Agent Resolution Engine under Rule 60 CGST",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount static frontend directory if built
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))

def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def _get_media_type(path: str) -> str:
    p = path.lower()
    if p.endswith(".html"):
        return "text/html"
    elif p.endswith(".js") or p.endswith(".mjs"):
        return "application/javascript"
    elif p.endswith(".css"):
        return "text/css"
    elif p.endswith(".png"):
        return "image/png"
    elif p.endswith(".jpg") or p.endswith(".jpeg"):
        return "image/jpeg"
    elif p.endswith(".svg"):
        return "image/svg+xml"
    elif p.endswith(".json"):
        return "application/json"
    return "text/plain"

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        try:
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        except Exception:
            pass

    @app.get("/", response_class=HTMLResponse)
    async def serve_root():
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return HTMLResponse(content=_read_bytes(index_file).decode("utf-8"))
        return HTMLResponse(content="<h1>CrediFlow API Online</h1>")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return Response(content=_read_bytes(file_path), media_type=_get_media_type(file_path))
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return HTMLResponse(content=_read_bytes(index_file).decode("utf-8"))
        return HTMLResponse(content="<h1>CrediFlow API Online</h1>")
else:
    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(content="<h1>CrediFlow API Online</h1><p>Frontend not compiled</p>")
