from beanie import Document, Link
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class FocusLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SubjectDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class StudyLog(Document):
    user_id: str                                         # stores User PK as string
    subject: str
    duration_minutes: int                                # minutes
    focus_level: FocusLevel
    breaks_taken: int = 0
    difficulty: SubjectDifficulty = SubjectDifficulty.MEDIUM
    stress_level: int                                    # 1–10
    productivity_score: Optional[float] = None           # 0.0–1.0
    notes: Optional[str] = None
    study_date: datetime
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "study_logs"
        indexes = [
            [("user_id", 1), ("study_date", -1)],       # compound index for fast user queries
        ]