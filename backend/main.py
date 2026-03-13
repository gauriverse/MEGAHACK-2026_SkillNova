import sys
import os
from pathlib import Path

# This finds the 'backend' folder and adds it to Python's search list
sys.path.append(str(Path(__file__).parent))

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from core.config import settings
from core.database import connect_db, disconnect_db
from routes import (
    auth_router,
    study_logs_router,
    sleep_logs_router,
    assessments_router,
    recommendations_router,
    dashboard_router,
)
from utils.exceptions import validation_exception_handler, generic_exception_handler

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: connect / disconnect MongoDB ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Burnout Predictor API…")
    await connect_db()
    yield
    await disconnect_db()
    logger.info("Shutdown complete.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Burnout Predictor API",
    description=(
        "FastAPI + MongoDB backend that analyses student study patterns "
        "and sleep data to predict burnout risk using ML and deliver "
        "personalised well-being recommendations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Routers (all under /api/v1) ───────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth_router,            prefix=PREFIX)
app.include_router(study_logs_router,      prefix=PREFIX)
app.include_router(sleep_logs_router,      prefix=PREFIX)
app.include_router(assessments_router,     prefix=PREFIX)
app.include_router(recommendations_router, prefix=PREFIX)
app.include_router(dashboard_router,       prefix=PREFIX)


# ── Health & root ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}


@app.get("/", tags=["Root"])
async def root():
    return {"message": "AI Burnout Predictor API", "docs": "/docs", "health": "/health"}


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )