"""
CrediFlow Vercel Serverless Entry Point
True deferred loading: the full backend is imported on the FIRST HTTP request,
not at module load time. This prevents Vercel cold-start crashes from heavy packages.
"""
import os
import sys
import traceback

# Ensure the project root is on sys.path so that `backend.*` is importable
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Cache of the loaded application (None = not yet loaded, Exception = failed)
_app_cache = None
_app_error = None
_app_tb = None


def _load_app():
    """Import and cache the full FastAPI application. Called once on first request."""
    global _app_cache, _app_error, _app_tb
    if _app_cache is not None or _app_error is not None:
        return
    try:
        from backend.app.main import app as _app
        _app_cache = _app
    except Exception as e:
        _app_error = e
        _app_tb = traceback.format_exc()


async def handler(scope, receive, send):
    """ASGI handler — loads the app on first call, then proxies all requests."""
    if scope["type"] not in ("http", "lifespan"):
        return

    _load_app()

    if _app_cache is not None:
        # Successfully loaded — proxy to the real app
        await _app_cache(scope, receive, send)
    else:
        # Import failed — return diagnostic JSON
        if scope["type"] == "http":
            import json
            body = json.dumps({
                "error": str(_app_error),
                "type": type(_app_error).__name__ if _app_error else "Unknown",
                "traceback": _app_tb or "No traceback",
                "python_version": sys.version,
                "sys_path": sys.path[:6],
                "repo_root": REPO_ROOT,
            }).encode()
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"access-control-allow-origin", b"*"],
                ],
            })
            await send({"type": "http.response.body", "body": body})


# Vercel also looks for `app` as the handler name
app = handler

