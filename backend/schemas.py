from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ─────────────────────────────── AUTH ────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────── STUDY LOGS ──────────────────────────────────

class FocusLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SubjectDifficultyEnum(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class StudyLogCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    duration_minutes: int = Field(..., ge=5, le=720)
    focus_level: FocusLevelEnum
    breaks_taken: int = Field(default=0, ge=0)
    difficulty: SubjectDifficultyEnum = SubjectDifficultyEnum.MEDIUM
    stress_level: int = Field(..., ge=1, le=10)
    productivity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None
    study_date: datetime


class StudyLogUpdate(BaseModel):
    subject: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=720)
    focus_level: Optional[FocusLevelEnum] = None
    breaks_taken: Optional[int] = Field(None, ge=0)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    productivity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None


class StudyLogResponse(BaseModel):
    id: str
    user_id: str
    subject: str
    duration_minutes: int
    focus_level: str
    breaks_taken: int
    difficulty: str
    stress_level: int
    productivity_score: Optional[float]
    notes: Optional[str]
    study_date: datetime
    logged_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────── SLEEP LOGS ──────────────────────────────────

class SleepQualityEnum(str, Enum):
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class SleepLogCreate(BaseModel):
    sleep_duration_hours: float = Field(..., ge=0.5, le=24.0)
    sleep_quality: SleepQualityEnum
    bedtime: datetime
    wake_time: datetime
    interruptions: int = Field(default=0, ge=0)
    used_screen_before_bed: bool = False
    energy_level_morning: int = Field(..., ge=1, le=10)
    sleep_date: datetime

    @field_validator("wake_time")
    @classmethod
    def wake_after_bed(cls, v, info):
        if "bedtime" in info.data and v <= info.data["bedtime"]:
            raise ValueError("wake_time must be after bedtime")
        return v


class SleepLogResponse(BaseModel):
    id: str
    user_id: str
    sleep_duration_hours: float
    sleep_quality: str
    bedtime: datetime
    wake_time: datetime
    interruptions: int
    used_screen_before_bed: bool
    energy_level_morning: int
    sleep_date: datetime
    logged_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────── ASSESSMENTS ─────────────────────────────────

class AssessmentRequest(BaseModel):
    days: int = Field(default=7, ge=3, le=30)


class BurnoutAssessmentResponse(BaseModel):
    id: str
    user_id: str
    burnout_risk: str
    burnout_score: float
    confidence: float
    avg_study_hours_per_day: float
    avg_sleep_hours: float
    avg_stress_level: float
    avg_focus_level: float
    avg_breaks_taken: float
    sleep_consistency_score: float
    study_consistency_score: float
    days_analyzed: int
    risk_factors: Optional[Dict[str, Any]]
    assessed_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────── RECOMMENDATIONS ─────────────────────────────

class RecommendationResponse(BaseModel):
    id: str
    user_id: str
    assessment_id: Optional[str]
    category: str
    priority: str
    title: str
    description: str
    action_steps: Optional[List[str]]
    is_completed: bool
    is_dismissed: bool
    feedback_rating: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class RecommendationUpdate(BaseModel):
    is_completed: Optional[bool] = None
    is_dismissed: Optional[bool] = None
    feedback_rating: Optional[int] = Field(None, ge=1, le=5)


# ─────────────────────────────── DASHBOARD ───────────────────────────────────

class DashboardStats(BaseModel):
    total_study_hours_week: float
    avg_sleep_hours_week: float
    avg_stress_level_week: float
    avg_productivity_week: float
    burnout_risk: Optional[str]
    burnout_score: Optional[float]
    streak_days: int
    recent_assessments: List[BurnoutAssessmentResponse]
    active_recommendations: List[RecommendationResponse]


# ─────────────────────────────── COMMON ──────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


class MessageResponse(BaseModel):
    message: str
    success: bool = True