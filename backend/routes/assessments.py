from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List

from models.user import User
from models.burnout_assessment import BurnoutAssessment
from models.recommendation import Recommendation
from schemas import AssessmentRequest, BurnoutAssessmentResponse, RecommendationResponse, PaginatedResponse
from core.security import get_current_user
from services.analytics import aggregate_features
from services.burnout_predictor import burnout_predictor
from services.recommendation_engine import recommendation_engine

router = APIRouter(prefix="/assessments", tags=["Burnout Assessments"])


def _serialize_assessment(a: BurnoutAssessment) -> BurnoutAssessmentResponse:
    return BurnoutAssessmentResponse(
        id=str(a.id),
        user_id=a.user_id,
        burnout_risk=a.burnout_risk.value,
        burnout_score=a.burnout_score,
        confidence=a.confidence,
        avg_study_hours_per_day=a.avg_study_hours_per_day,
        avg_sleep_hours=a.avg_sleep_hours,
        avg_stress_level=a.avg_stress_level,
        avg_focus_level=a.avg_focus_level,
        avg_breaks_taken=a.avg_breaks_taken,
        sleep_consistency_score=a.sleep_consistency_score,
        study_consistency_score=a.study_consistency_score,
        days_analyzed=a.days_analyzed,
        risk_factors=a.risk_factors,
        assessed_at=a.assessed_at,
    )


def _serialize_rec(r: Recommendation) -> RecommendationResponse:
    return RecommendationResponse(
        id=str(r.id),
        user_id=r.user_id,
        assessment_id=r.assessment_id,
        category=r.category.value,
        priority=r.priority.value,
        title=r.title,
        description=r.description,
        action_steps=r.action_steps,
        is_completed=r.is_completed,
        is_dismissed=r.is_dismissed,
        feedback_rating=r.feedback_rating,
        created_at=r.created_at,
        completed_at=r.completed_at,
    )


@router.post("/", response_model=BurnoutAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def run_assessment(
    payload: AssessmentRequest,
    current_user: User = Depends(get_current_user),
):
    """Aggregate logs → run ML model → persist assessment + recommendations."""
    user_id = str(current_user.id)

    features = await aggregate_features(user_id, days=payload.days)
    if not features:
        raise HTTPException(
            status_code=422,
            detail=f"Not enough data for the past {payload.days} days. "
                   "Log at least one study or sleep session first.",
        )

    prediction = burnout_predictor.predict(features)

    assessment = BurnoutAssessment(
        user_id=user_id,
        avg_study_hours_per_day=features["avg_study_hours_per_day"],
        avg_sleep_hours=features["avg_sleep_hours"],
        avg_stress_level=features["avg_stress_level"],
        avg_focus_level=features["avg_focus_level"],
        avg_breaks_taken=features["avg_breaks_taken"],
        avg_productivity_score=features["avg_productivity_score"],
        sleep_consistency_score=features["sleep_consistency_score"],
        study_consistency_score=features["study_consistency_score"],
        days_analyzed=features["days_analyzed"],
        burnout_risk=prediction["burnout_risk"],
        burnout_score=prediction["burnout_score"],
        confidence=prediction["confidence"],
        risk_factors=prediction["risk_factors"],
    )
    await assessment.insert()

    # Generate and persist personalised recommendations
    rec_input = {**features, **prediction}
    for raw in recommendation_engine.generate(rec_input):
        rec = Recommendation(
            user_id=user_id,
            assessment_id=str(assessment.id),
            category=raw["category"],
            priority=raw["priority"],
            title=raw["title"],
            description=raw["description"],
            action_steps=raw["action_steps"],
        )
        await rec.insert()

    return _serialize_assessment(assessment)


@router.get("/", response_model=PaginatedResponse)
async def list_assessments(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    query = BurnoutAssessment.find(BurnoutAssessment.user_id == str(current_user.id))
    total = await query.count()
    items = await query.sort(-BurnoutAssessment.assessed_at).skip((page - 1) * per_page).limit(per_page).to_list()

    return PaginatedResponse(
        items=[_serialize_assessment(a) for a in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/latest", response_model=BurnoutAssessmentResponse)
async def get_latest_assessment(current_user: User = Depends(get_current_user)):
    assessment = await BurnoutAssessment.find(
        BurnoutAssessment.user_id == str(current_user.id)
    ).sort(-BurnoutAssessment.assessed_at).first_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="No assessments yet. Run your first assessment.")
    return _serialize_assessment(assessment)


@router.get("/{assessment_id}", response_model=BurnoutAssessmentResponse)
async def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
):
    a = await BurnoutAssessment.get(assessment_id)
    if not a or a.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Assessment not found")
    return _serialize_assessment(a)


@router.get("/{assessment_id}/recommendations", response_model=List[RecommendationResponse])
async def get_assessment_recommendations(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
):
    a = await BurnoutAssessment.get(assessment_id)
    if not a or a.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Assessment not found")

    recs = await Recommendation.find(
        Recommendation.assessment_id == assessment_id,
        Recommendation.is_dismissed == False,
    ).to_list()

    return [_serialize_rec(r) for r in recs]