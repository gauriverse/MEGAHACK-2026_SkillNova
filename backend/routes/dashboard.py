from fastapi import APIRouter, Depends
from datetime import datetime, timedelta, timezone
from typing import List

from models.user import User
from models.study_log import StudyLog
from models.sleep_log import SleepLog
from models.burnout_assessment import BurnoutAssessment
from models.recommendation import Recommendation
from schemas import DashboardStats, BurnoutAssessmentResponse, RecommendationResponse
from core.security import get_current_user
from services.analytics import get_streak

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _serialize_assessment(a: BurnoutAssessment) -> BurnoutAssessmentResponse:
    return BurnoutAssessmentResponse(
        id=str(a.id), user_id=a.user_id,
        burnout_risk=a.burnout_risk.value, burnout_score=a.burnout_score,
        confidence=a.confidence,
        avg_study_hours_per_day=a.avg_study_hours_per_day,
        avg_sleep_hours=a.avg_sleep_hours, avg_stress_level=a.avg_stress_level,
        avg_focus_level=a.avg_focus_level, avg_breaks_taken=a.avg_breaks_taken,
        sleep_consistency_score=a.sleep_consistency_score,
        study_consistency_score=a.study_consistency_score,
        days_analyzed=a.days_analyzed, risk_factors=a.risk_factors,
        assessed_at=a.assessed_at,
    )


def _serialize_rec(r: Recommendation) -> RecommendationResponse:
    return RecommendationResponse(
        id=str(r.id), user_id=r.user_id, assessment_id=r.assessment_id,
        category=r.category.value, priority=r.priority.value,
        title=r.title, description=r.description, action_steps=r.action_steps,
        is_completed=r.is_completed, is_dismissed=r.is_dismissed,
        feedback_rating=r.feedback_rating, created_at=r.created_at,
        completed_at=r.completed_at,
    )


@router.get("/", response_model=DashboardStats)
async def get_dashboard(current_user: User = Depends(get_current_user)):
    user_id = str(current_user.id)
    since_7d = datetime.now(timezone.utc) - timedelta(days=7)

    # ── Study stats ──────────────────────────────────────────────────────────
    study_logs = await StudyLog.find(
        StudyLog.user_id == user_id,
        StudyLog.study_date >= since_7d,
    ).to_list()

    total_study_hours_week = round(sum(l.duration_minutes for l in study_logs) / 60, 2)
    avg_stress = round(sum(l.stress_level for l in study_logs) / len(study_logs), 2) if study_logs else 0.0
    prod_scores = [l.productivity_score for l in study_logs if l.productivity_score is not None]
    avg_productivity = round(sum(prod_scores) / len(prod_scores), 2) if prod_scores else 0.0

    # ── Sleep stats ──────────────────────────────────────────────────────────
    sleep_logs = await SleepLog.find(
        SleepLog.user_id == user_id,
        SleepLog.sleep_date >= since_7d,
    ).to_list()

    avg_sleep = round(sum(l.sleep_duration_hours for l in sleep_logs) / len(sleep_logs), 2) if sleep_logs else 0.0

    # ── Latest assessments ───────────────────────────────────────────────────
    recent_assessments = await BurnoutAssessment.find(
        BurnoutAssessment.user_id == user_id
    ).sort(-BurnoutAssessment.assessed_at).limit(3).to_list()

    latest = recent_assessments[0] if recent_assessments else None

    # ── Active recommendations ───────────────────────────────────────────────
    active_recs = await Recommendation.find(
        Recommendation.user_id == user_id,
        Recommendation.is_completed == False,
        Recommendation.is_dismissed == False,
    ).sort(-Recommendation.created_at).limit(5).to_list()

    streak = await get_streak(user_id)

    return DashboardStats(
        total_study_hours_week=total_study_hours_week,
        avg_sleep_hours_week=avg_sleep,
        avg_stress_level_week=avg_stress,
        avg_productivity_week=avg_productivity,
        burnout_risk=latest.burnout_risk.value if latest else None,
        burnout_score=latest.burnout_score if latest else None,
        streak_days=streak,
        recent_assessments=[_serialize_assessment(a) for a in recent_assessments],
        active_recommendations=[_serialize_rec(r) for r in active_recs],
    )


@router.get("/trends")
async def get_trends(current_user: User = Depends(get_current_user)):
    """30-day time-series data for charts."""
    user_id = str(current_user.id)
    since_30d = datetime.now(timezone.utc) - timedelta(days=30)

    study_logs = await StudyLog.find(
        StudyLog.user_id == user_id,
        StudyLog.study_date >= since_30d,
    ).sort(StudyLog.study_date).to_list()

    sleep_logs = await SleepLog.find(
        SleepLog.user_id == user_id,
        SleepLog.sleep_date >= since_30d,
    ).sort(SleepLog.sleep_date).to_list()

    assessments = await BurnoutAssessment.find(
        BurnoutAssessment.user_id == user_id,
        BurnoutAssessment.assessed_at >= since_30d,
    ).sort(BurnoutAssessment.assessed_at).to_list()

    return {
        "study_trend": [
            {
                "date": l.study_date.date().isoformat(),
                "duration_hours": round(l.duration_minutes / 60, 2),
                "stress_level": l.stress_level,
                "focus_level": l.focus_level.value,
            }
            for l in study_logs
        ],
        "sleep_trend": [
            {
                "date": l.sleep_date.date().isoformat(),
                "duration_hours": l.sleep_duration_hours,
                "quality": l.sleep_quality.value,
                "energy_morning": l.energy_level_morning,
            }
            for l in sleep_logs
        ],
        "burnout_trend": [
            {
                "date": a.assessed_at.date().isoformat(),
                "burnout_score": a.burnout_score,
                "burnout_risk": a.burnout_risk.value,
            }
            for a in assessments
        ],
    }