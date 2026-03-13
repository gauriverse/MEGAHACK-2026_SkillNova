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
    analysis_router,
    tasks_router,
    recommendations_router,
    dashboard_router,
)
from utils.exceptions import validation_exception_handler, generic_exception_handler

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await connect_db()
    yield
    await disconnect_db()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "SkillNova backend — FastAPI + MongoDB + ML. "
        "4-step Deep Dive analysis, interactive task cards, "
        "streak gamification, and burnout risk prediction."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

PREFIX = "/api/v1"

app.include_router(auth_router,            prefix=PREFIX)   # /api/v1/auth
app.include_router(study_logs_router,      prefix=PREFIX)   # /api/v1/study-logs
app.include_router(sleep_logs_router,      prefix=PREFIX)   # /api/v1/sleep-logs
app.include_router(analysis_router,        prefix=PREFIX)   # /api/v1/analysis  ← NEW
app.include_router(tasks_router,           prefix=PREFIX)   # /api/v1/tasks     ← NEW
app.include_router(recommendations_router, prefix=PREFIX)   # /api/v1/recommendations
app.include_router(dashboard_router,       prefix=PREFIX)   # /api/v1/dashboard


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)