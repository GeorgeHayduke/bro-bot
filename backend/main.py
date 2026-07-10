from pathlib import Path

import redis as redis_lib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.config import settings
from backend.database import SessionLocal
from backend.api import api_router

app = FastAPI(
    title=settings.api_title,
    description="Machine Learning Model Management Platform",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "static"
FRONTEND_DIR = BASE_DIR / "frontend"

# Static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# API routes
app.include_router(api_router)


# ── Health ──

@app.get("/health")
async def health_check():
    checks = {"api": "healthy"}

    # Database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
        db.close()
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    # Redis
    try:
        r = redis_lib.from_url(settings.redis_url)
        r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


@app.get("/api/version")
async def get_version():
    return {"version": settings.api_version, "status": "active"}


# ── Frontend ──

@app.get("/")
async def serve_frontend():
    frontend_path = FRONTEND_DIR / "index.html"
    if frontend_path.exists():
        return FileResponse(str(frontend_path), media_type="text/html")
    return {"error": "Frontend not found", "hint": f"Expected at {frontend_path}"}


@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    if full_path.startswith(("api/", "static/", "docs", "redoc")) or full_path == "openapi.json":
        return {"error": "Not found"}
    frontend_path = FRONTEND_DIR / "index.html"
    if frontend_path.exists():
        return FileResponse(str(frontend_path), media_type="text/html")
    return {"error": "Frontend not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
