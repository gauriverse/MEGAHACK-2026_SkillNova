from beanie import Document
from pydantic import Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


class RecommendationCategory(str, Enum):
    SLEEP = "sleep"
    STUDY_HABITS = "study_habits"
    BREAKS = "breaks"
    STRESS_MANAGEMENT = "stress_management"
    PHYSICAL_ACTIVITY = "physical_activity"
    MINDFULNESS = "mindfulness"


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Recommendation(Document):
    user_id: str
    assessment_id: Optional[str] = None                 # linked assessment

    category: RecommendationCategory
    priority: RecommendationPriority
    title: str
    description: str
    action_steps: Optional[List[str]] = None            # list of step strings

    is_completed: bool = False
    is_dismissed: bool = False
    feedback_rating: Optional[int] = None               # 1–5

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "recommendations"
        indexes = [
            [("user_id", 1), ("is_completed", 1), ("is_dismissed", 1)],
            [("assessment_id", 1)],
        ]