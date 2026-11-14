"""Main FastAPI application entrypoint."""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router, ws_router
from app.config import settings
from app.services.monitoring_service import get_monitoring_service

STATIC_DASHBOARD_FILE = Path(__file__).resolve().parent / "static" / "dashboard.html"
FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_format = "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    logger.info("Initializing %s v%s", settings.APP_NAME, settings.APP_VERSION)
    monitoring_service = get_monitoring_service()
    await monitoring_service.start()
    yield
    logger.info("Shutting down %s", settings.APP_NAME)
    await monitoring_service.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time system telemetry and metrics engine powered by FastAPI and psutil.",
    lifespan=lifespan,
)

# Enable CORS for local dashboards and cross-origin tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(api_router)
app.include_router(ws_router)

# Mount React static assets if built
if (FRONTEND_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="assets")


@app.get("/dashboard", response_class=HTMLResponse, summary="Interactive Real-Time Dashboard")
async def dashboard():
    """Serve the real-time visual system monitoring dashboard (Day 3 React or Day 1 fallback)."""
    dist_index = FRONTEND_DIST_DIR / "index.html"
    if dist_index.exists():
        return HTMLResponse(content=dist_index.read_text(encoding="utf-8"))
    if STATIC_DASHBOARD_FILE.exists():
        return HTMLResponse(content=STATIC_DASHBOARD_FILE.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>Dashboard file not found</h2>", status_code=404)


@app.get("/", summary="Root landing and dashboard")
async def root(request: Request):
    """Serve dashboard to browsers, or JSON API directory to programmatic clients."""
    accept_header = request.headers.get("accept", "")
    dist_index = FRONTEND_DIST_DIR / "index.html"
    if "text/html" in accept_header:
        if dist_index.exists():
            return HTMLResponse(content=dist_index.read_text(encoding="utf-8"))
        if STATIC_DASHBOARD_FILE.exists():
            return HTMLResponse(content=STATIC_DASHBOARD_FILE.read_text(encoding="utf-8"))

    return JSONResponse(
        content={
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "dashboard": "/dashboard",
            "docs": "/docs",
            "endpoints": {
                "health": "/api/health",
                "current_metrics": "/api/metrics/current",
                "history": "/api/metrics/history",
                "processes": "/api/processes",
                "system_info": "/api/system/info",
                "websocket_stream": "/ws/metrics",
                "predict_cpu": "/api/predictions/cpu",
                "predict_memory": "/api/predictions/memory",
                "predict_summary": "/api/predictions/summary",
                "anomalies": "/api/anomalies",
                "risk": "/api/risk",
                "ai_insights_query": "/api/insights/query",
                "ai_insights_summary": "/api/insights/summary",
            },
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
