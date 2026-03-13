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



from pydantic import BaseModel, Field, field_validator
from typing   import List, Optional
from enum     import Enum
 
 
# ── Enums ──────────────────────────────────────────────────────────────────
class GenderEnum(str, Enum):
    male   = "male"
    female = "female"
    other  = "other"
 
class EducationLevel(str, Enum):
    high_school = "high_school"   # edu_level = 1
    undergrad   = "undergrad"     # edu_level = 2
    postgrad    = "postgrad"      # edu_level = 3
    phd         = "phd"           # edu_level = 4
 
class BurnoutRisk(str, Enum):
    low    = "Low"
    medium = "Medium"
    high   = "High"
 
 
# ── Request Model ──────────────────────────────────────────────────────────
class BurnoutAnalysisRequest(BaseModel):
    """
    What the frontend sends to POST /api/burnout/analyze
    All fields match the ML model's 14 input features.
    """
 
    # Demographics
    age:               int   = Field(..., ge=13, le=100,
                                     description="Student age (13–100)")
    weight:            float = Field(..., ge=30,
                                     description="Weight in kg (≥30)")
    gender:            GenderEnum
    educational_level: EducationLevel
 
    # Behavioral
    study_hours:  float = Field(..., ge=0, le=24,
                                description="Average study hours per day")
    sleep_hours:  float = Field(..., ge=0, le=24,
                                description="Average sleep hours per day")
 
    # 1–5 Vibe Scales
    overwhelmed_score:    int = Field(..., ge=1, le=5,
                                      description="How often they feel overwhelmed (1=never, 5=always)")
    motivation_score:     int = Field(..., ge=1, le=5,
                                      description="Current motivation level (1=very low, 5=very high)")
    exhaustion_score:     int = Field(..., ge=1, le=5,
                                      description="Mental exhaustion level (1=none, 5=severe)")
    concentration_score:  int = Field(..., ge=1, le=5,
                                      description="Difficulty concentrating (1=easy, 5=very hard)")
    anxiety_score:        int = Field(..., ge=1, le=5,
                                      description="Exam anxiety level (1=none, 5=severe)")
    balance_score:        int = Field(..., ge=1, le=5,
                                      description="Schedule balance (1=chaotic, 5=very balanced)")
    procrastination_score:int = Field(..., ge=1, le=5,
                                      description="Procrastination frequency (1=never, 5=always)")
 
    # Checkboxes — list of selected symptom strings
    symptoms: List[str] = Field(
        default=[],
        description="List of selected burnout symptoms from checklist"
    )
 
    @field_validator("symptoms")
    @classmethod
    def validate_symptoms(cls, v):
        VALID_SYMPTOMS = {
            "headaches", "irritability", "insomnia",
            "appetite_changes", "difficulty_focusing",
            "social_withdrawal", "physical_fatigue", "emotional_numbness"
        }
        for symptom in v:
            if symptom not in VALID_SYMPTOMS:
                raise ValueError(f"Invalid symptom: '{symptom}'. "
                                 f"Valid options: {sorted(VALID_SYMPTOMS)}")
        return v
 
    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 21,
                "weight": 65.0,
                "gender": "female",
                "educational_level": "undergrad",
                "study_hours": 11.0,
                "sleep_hours": 4.5,
                "overwhelmed_score": 5,
                "motivation_score": 1,
                "exhaustion_score": 5,
                "concentration_score": 4,
                "anxiety_score": 5,
                "balance_score": 1,
                "procrastination_score": 4,
                "symptoms": ["insomnia", "headaches", "social_withdrawal"]
            }
        }
    }
 
 
# ── Response Models ────────────────────────────────────────────────────────
class BurnoutAnalysisResponse(BaseModel):
    """What the API returns after prediction."""
    burnout_risk:        BurnoutRisk
    confidence_scores:   dict              # {"Low": 0.1, "Medium": 0.3, "High": 0.6}
    symptom_count:       int
    top_risk_factors:    List[str]         # top 3 features driving the prediction
    recommendations:     List[str]         # personalized suggestions
    streak_updated:      bool   = False
    current_streak:      int    = 0
 
 
class StreakResponse(BaseModel):
    """Response after updating a user's streak."""
    streak_count:      int
    last_activity_date: str
    streak_updated:    bool
    message:           str