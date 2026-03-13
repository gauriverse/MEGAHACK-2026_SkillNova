import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import connect_db, disconnect_db


from routes.auth import router as auth_router
from routes.tasks import router as tasks_router
from routes.assessments import router as assessments_router

# -- Logging Setup --
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -- Lifespan for Database Connection --
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SkillNova API...")
    await connect_db()
    yield
    await disconnect_db()
    logger.info("Shutdown complete.")
    
# -- App Initialization --
app = FastAPI(
    title="SkillNova API",
    description="AI-powered student burnout prediction and productivity tracking",
    version="1.0.0",
    lifespan=lifespan
)

# -- CORS Setup --
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Register Routers --
# This connects your individual route files to the main app
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(assessments_router, prefix="/api/v1/assessments", tags=["Assessments"])

@app.get("/")
async def root():
    return {"message": "SkillNova API is running 🚀"}

# -- Dev Runner --
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)