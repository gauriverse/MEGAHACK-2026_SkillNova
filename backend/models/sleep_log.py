from beanie import Document
from pydantic import Field, model_validator
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class SleepQuality(str, Enum):
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class SleepLog(Document):
    user_id: str
    sleep_duration_hours: float
    sleep_quality: SleepQuality
    bedtime: datetime
    wake_time: datetime
    interruptions: int = 0
    used_screen_before_bed: bool = False
    energy_level_morning: int                            # 1–10
    sleep_date: datetime
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sleep_logs"
        indexes = [
            [("user_id", 1), ("sleep_date", -1)],
        ]