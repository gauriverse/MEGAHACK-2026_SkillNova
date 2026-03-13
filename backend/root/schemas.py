from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ══════════════════════════════ AUTH ═════════════════════════════════════════

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
    # Demographics
    age: Optional[int]
    weight: Optional[float]
    gender: Optional[str]
    educational_level: Optional[str]
    # Gamification
    streak_count: int
    xp_points: int
    level: int
    total_tasks_completed: int
    last_activity_date: Optional[date]
    # UI
    theme: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=13, le=100)
    weight: Optional[float] = Field(None, ge=30, le=300)
    gender: Optional[str] = None
    educational_level: Optional[str] = None
    theme: Optional[str] = None                  # "light" | "dark"


# ══════════════════════════════ STUDY LOGS ═══════════════════════════════════

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


# ══════════════════════════════ SLEEP LOGS ═══════════════════════════════════

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


# ══════════════════════ DEEP DIVE ANALYSIS (NEW) ═════════════════════════════

class BurnoutAnalysisRequest(BaseModel):
    """
    4-step Deep Dive intake form → maps directly to ML model features.
    Posted by the frontend after the wizard completes.
    """
    # Step 1 — Demographics
    age: int = Field(..., ge=13, le=100)
    weight: float = Field(..., ge=30, le=300)
    gender: str = Field(..., pattern="^(male|female|other)$")
    educational_level: str = Field(..., pattern="^(school|undergraduate|postgraduate|other)$")

    # Step 2 — Behaviour
    study_hours: float = Field(..., ge=0, le=14, description="Avg study hours per day")
    sleep_hours: float = Field(..., ge=0, le=12, description="Avg sleep hours per day")

    # Step 3 — Vibe scales (1–5)
    overwhelmed_score: int = Field(..., ge=1, le=5)
    motivation_score: int = Field(..., ge=1, le=5)
    exhaustion_score: int = Field(..., ge=1, le=5)
    concentration_score: int = Field(..., ge=1, le=5)
    anxiety_score: int = Field(..., ge=1, le=5)
    balance_score: int = Field(..., ge=1, le=5)
    procrastination_score: int = Field(..., ge=1, le=5)

    # Step 4 — Symptom cloud
    symptoms: List[str] = Field(default=[], description="Selected symptom tag strings")


class BurnoutAnalysisResponse(BaseModel):
    id: str
    user_id: str
    # Demographics
    age: int
    weight: float
    gender: str
    educational_level: str
    # Behaviour
    study_hours: float
    sleep_hours: float
    # Vibe scales
    overwhelmed_score: int
    motivation_score: int
    exhaustion_score: int
    concentration_score: int
    anxiety_score: int
    balance_score: int
    procrastination_score: int
    # Symptoms
    symptoms: List[str]
    symptom_score: int
    # ML output
    burnout_risk: str
    burnout_score: float
    confidence: float
    risk_factors: Optional[Dict[str, Any]]
    assessed_at: datetime


# ══════════════════════════════ TASKS ════════════════════════════════════════

class TaskItemResponse(BaseModel):
    id: str
    user_id: str
    analysis_id: Optional[str]
    category: str
    title: str
    description: str
    action_steps: List[str]
    duration_minutes: Optional[int]
    is_completed: bool
    is_dismissed: bool
    completed_at: Optional[datetime]
    xp_reward: int
    feedback_rating: Optional[int]
    assigned_date: date
    created_at: datetime


class TaskCompleteRequest(BaseModel):
    feedback_rating: Optional[int] = Field(None, ge=1, le=5)


class DailyProgressResponse(BaseModel):
    """Feeds the Live Progress Ring on the dashboard."""
    summary_date: date
    total_tasks: int
    completed_tasks: int
    completion_percentage: float             # 0–100
    all_completed: bool
    xp_earned: int
    streak_count: int                        # current user streak — for the 🔥 header


class TaskCompleteResponse(BaseModel):
    """Returned when a task is marked complete — triggers confetti if all_completed."""
    task: TaskItemResponse
    all_completed: bool                      # frontend checks this for confetti animation
    streak_leveled_up: bool                  # True when streak incremented this action
    level_up: bool                           # True when XP threshold crossed
    new_streak: int
    new_xp: int
    new_level: int
    message: str


# ══════════════════════════════ STREAK ═══════════════════════════════════════

class StreakResponse(BaseModel):
    streak_count: int
    last_activity_date: Optional[date]
    total_tasks_completed: int
    xp_points: int
    level: int


# ══════════════════════════ RECOMMENDATIONS ══════════════════════════════════

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


class RecommendationUpdate(BaseModel):
    is_completed: Optional[bool] = None
    is_dismissed: Optional[bool] = None
    feedback_rating: Optional[int] = Field(None, ge=1, le=5)


# ══════════════════════════════ DASHBOARD ════════════════════════════════════

class DashboardStats(BaseModel):
    # Study & sleep summary (last 7 days)
    total_study_hours_week: float
    avg_sleep_hours_week: float
    avg_stress_level_week: float
    avg_productivity_week: float
    # Latest burnout
    burnout_risk: Optional[str]
    burnout_score: Optional[float]
    # Gamification
    streak_count: int
    xp_points: int
    level: int
    # Today's Action Center progress
    today_progress: Optional[DailyProgressResponse]
    # Related data
    recent_analyses: List[BurnoutAnalysisResponse]
    active_tasks: List[TaskItemResponse]
    active_recommendations: List[RecommendationResponse]


# ══════════════════════════════ COMMON ═══════════════════════════════════════

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


class MessageResponse(BaseModel):
    message: str
    success: bool = True