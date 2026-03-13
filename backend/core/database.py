import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client
mongo_client: AsyncIOMotorClient = None


async def connect_db():
    """Initialize Motor client and Beanie ODM."""
    global mongo_client

    # Import all document models here to register them with Beanie
    # Use relative imports (notice the dots)
    from ..models.user import User
    from ..models.study_log import StudyLog
    from ..models.sleep_log import SleepLog
    from ..models.burnout_assessment import BurnoutAssessment
    from ..models.recommendation import Recommendation
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)

    await init_beanie(
        database=mongo_client[settings.MONGODB_DB_NAME],
        document_models=[
            User,
            StudyLog,
            SleepLog,
            BurnoutAssessment,
            Recommendation,
        ],
    )
    logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def disconnect_db():
    """Close MongoDB connection."""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed.")