from beanie import Document
from pydantic import Field
from typing import Optional, List
from datetime import datetime, timezone, date
from enum import Enum


class TaskCategory(str, Enum):
    BREATHING = "breathing"
    HYDRATION = "hydration"
    MOVEMENT = "movement"
    SLEEP = "sleep"
    STUDY = "study"
    MINDFULNESS = "mindfulness"
    NUTRITION = "nutrition"
    SOCIAL = "social"
    BREAK = "break"


class TaskItem(Document):
    """
    One interactive task card shown in the Action Center.
    Persisted so progress survives page refresh.

    Collection: task_items
    """
    user_id: str
    analysis_id: Optional[str] = None       # linked BurnoutAnalysis

    # Task content
    category: TaskCategory
    title: str
    description: str
    action_steps: List[str] = []
    duration_minutes: Optional[int] = None

    # Completion state
    is_completed: bool = False
    is_dismissed: bool = False
    completed_at: Optional[datetime] = None

    # Gamification
    xp_reward: int = 10
    feedback_rating: Optional[int] = None   # 1–5 stars

    # Date context (for streak grouping)
    assigned_date: date = Field(default_factory=lambda: datetime.now(timezone.utc).date())
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "task_items"
        indexes = [
            [("user_id", 1), ("assigned_date", -1)],
            [("user_id", 1), ("is_completed", 1)],
            [("analysis_id", 1)],
        ]


class DailyTaskSummary(Document):
    """
    Aggregated per-day completion status.
    Streak logic reads from this — updated every time a task is completed.

    Collection: daily_task_summaries
    """
    user_id: str
    summary_date: date
    total_tasks: int = 0
    completed_tasks: int = 0
    all_completed: bool = False              # True when completed == total
    xp_earned: int = 0
    streak_counted: bool = False             # prevents double-incrementing streak
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "daily_task_summaries"
        indexes = [
            [("user_id", 1), ("summary_date", -1)],
        ]