"""
CrediFlow Vercel Serverless Entry Point
- Imports backend.app.main FastAPI app
- On any import failure, serves a minimal diagnostic JSON on ALL routes
"""
import os
import sys
import traceback

# Ensure the project root is on sys.path so that `backend.*` is importable
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

_import_error = None
_import_tb = None

try:
    from backend.app.main import app
    handler = app
except Exception as _e:
    _import_error = _e
    _import_tb = traceback.format_exc()

    # Build a minimal diagnostic FastAPI app that does NOT re-import anything heavy
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse

        app = FastAPI()

        @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def diagnostic_handler(full_path: str):
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(_import_error),
                    "type": type(_import_error).__name__,
                    "traceback": _import_tb,
                    "python_version": sys.version,
                    "sys_path": sys.path[:5],
                }
            )
        handler = app
    except Exception as _fe:
        # FastAPI itself is missing — use raw ASGI
        _fastapi_tb = traceback.format_exc()
        import json

        async def handler(scope, receive, send):
            if scope["type"] == "http":
                body = json.dumps({
                    "fatal": "FastAPI not available",
                    "import_error": str(_import_error),
                    "fastapi_error": str(_fe),
                    "traceback": _fastapi_tb,
                    "python_version": sys.version,
                }).encode()
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({"type": "http.response.body", "body": body})
