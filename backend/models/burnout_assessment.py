from beanie import Document
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class BurnoutRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class BurnoutAssessment(Document):
    user_id: str

    # Aggregated input features
    avg_study_hours_per_day: float
    avg_sleep_hours: float
    avg_stress_level: float
    avg_focus_level: float                               # 0 (low) – 2 (high) encoded
    avg_breaks_taken: float
    avg_productivity_score: Optional[float] = None
    sleep_consistency_score: float                       # 0–1
    study_consistency_score: float                       # 0–1
    days_analyzed: int

    # ML output
    burnout_risk: BurnoutRisk
    burnout_score: float                                 # 0.0–1.0
    confidence: float
    risk_factors: Optional[Dict[str, Any]] = None

    notes: Optional[str] = None
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "burnout_assessments"
        indexes = [
            [("user_id", 1), ("assessed_at", -1)],
        ]