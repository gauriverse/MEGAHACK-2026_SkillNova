from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime, timezone

from models.user import User
from models.recommendation import Recommendation
from backend.schemas.schemas import RecommendationResponse, RecommendationUpdate, PaginatedResponse
from core.security import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def _serialize(r: Recommendation) -> RecommendationResponse:
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


@router.get("/", response_model=PaginatedResponse)
async def list_recommendations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    dismissed: Optional[bool] = Query(False),
    current_user: User = Depends(get_current_user),
):
    query = Recommendation.find(Recommendation.user_id == str(current_user.id))

    if category:
        query = query.find({"category": category})
    if priority:
        query = query.find({"priority": priority})
    if completed is not None:
        query = query.find({"is_completed": completed})
    if dismissed is not None:
        query = query.find({"is_dismissed": dismissed})

    total = await query.count()
    items = await query.sort(-Recommendation.created_at).skip((page - 1) * per_page).limit(per_page).to_list()

    return PaginatedResponse(
        items=[_serialize(r) for r in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/active", response_model=List[RecommendationResponse])
async def get_active_recommendations(current_user: User = Depends(get_current_user)):
    """Non-dismissed, non-completed recommendations sorted by priority."""
    recs = await Recommendation.find(
        Recommendation.user_id == str(current_user.id),
        Recommendation.is_completed == False,
        Recommendation.is_dismissed == False,
    ).to_list()

    recs.sort(key=lambda r: PRIORITY_ORDER.get(r.priority.value, 99))
    return [_serialize(r) for r in recs]


@router.get("/{rec_id}", response_model=RecommendationResponse)
async def get_recommendation(
    rec_id: str,
    current_user: User = Depends(get_current_user),
):
    r = await Recommendation.get(rec_id)
    if not r or r.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return _serialize(r)


@router.patch("/{rec_id}", response_model=RecommendationResponse)
async def update_recommendation(
    rec_id: str,
    payload: RecommendationUpdate,
    current_user: User = Depends(get_current_user),
):
    r = await Recommendation.get(rec_id)
    if not r or r.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Recommendation not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(r, field, value)

    if payload.is_completed is True and not r.completed_at:
        r.completed_at = datetime.now(timezone.utc)

    await r.save()
    return _serialize(r)


@router.post("/{rec_id}/complete", response_model=RecommendationResponse)
async def complete_recommendation(
    rec_id: str,
    current_user: User = Depends(get_current_user),
):
    r = await Recommendation.get(rec_id)
    if not r or r.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Recommendation not found")

    r.is_completed = True
    r.completed_at = datetime.now(timezone.utc)
    await r.save()
    return _serialize(r)


@router.post("/{rec_id}/dismiss", response_model=RecommendationResponse)
async def dismiss_recommendation(
    rec_id: str,
    current_user: User = Depends(get_current_user),
):
    r = await Recommendation.get(rec_id)
    if not r or r.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Recommendation not found")

    r.is_dismissed = True
    await r.save()
    return _serialize(r)