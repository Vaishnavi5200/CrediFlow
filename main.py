"""
Root entrypoint for Vercel / Cloud deployments.
Exports FastAPI `app` from backend.app.main.
"""
from backend.app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
