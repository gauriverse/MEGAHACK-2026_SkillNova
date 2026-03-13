from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from datetime import datetime, timezone
from beanie import PydanticObjectId

from models.user import User
from models.study_log import StudyLog
from backend.schemas.schemas import StudyLogCreate, StudyLogUpdate, StudyLogResponse, PaginatedResponse
from core.security import get_current_user

router = APIRouter(prefix="/study-logs", tags=["Study Logs"])


def _serialize(log: StudyLog) -> StudyLogResponse:
    return StudyLogResponse(
        id=str(log.id),
        user_id=log.user_id,
        subject=log.subject,
        duration_minutes=log.duration_minutes,
        focus_level=log.focus_level.value,
        breaks_taken=log.breaks_taken,
        difficulty=log.difficulty.value,
        stress_level=log.stress_level,
        productivity_score=log.productivity_score,
        notes=log.notes,
        study_date=log.study_date,
        logged_at=log.logged_at,
    )


@router.post("/", response_model=StudyLogResponse, status_code=status.HTTP_201_CREATED)
async def create_study_log(
    payload: StudyLogCreate,
    current_user: User = Depends(get_current_user),
):
    log = StudyLog(
        user_id=str(current_user.id),
        subject=payload.subject,
        duration_minutes=payload.duration_minutes,
        focus_level=payload.focus_level.value,
        breaks_taken=payload.breaks_taken,
        difficulty=payload.difficulty.value,
        stress_level=payload.stress_level,
        productivity_score=payload.productivity_score,
        notes=payload.notes,
        study_date=payload.study_date,
    )
    await log.insert()
    return _serialize(log)


@router.get("/", response_model=PaginatedResponse)
async def list_study_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    subject: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
):
    query = StudyLog.find(StudyLog.user_id == str(current_user.id))

    if subject:
        query = query.find({"subject": {"$regex": subject, "$options": "i"}})
    if from_date:
        query = query.find(StudyLog.study_date >= from_date)
    if to_date:
        query = query.find(StudyLog.study_date <= to_date)

    total = await query.count()
    logs = await query.sort(-StudyLog.study_date).skip((page - 1) * per_page).limit(per_page).to_list()

    return PaginatedResponse(
        items=[_serialize(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/{log_id}", response_model=StudyLogResponse)
async def get_study_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
):
    log = await StudyLog.get(log_id)
    if not log or log.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Study log not found")
    return _serialize(log)


@router.patch("/{log_id}", response_model=StudyLogResponse)
async def update_study_log(
    log_id: str,
    payload: StudyLogUpdate,
    current_user: User = Depends(get_current_user),
):
    log = await StudyLog.get(log_id)
    if not log or log.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Study log not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(log, field, value.value if hasattr(value, "value") else value)

    await log.save()
    return _serialize(log)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
):
    log = await StudyLog.get(log_id)
    if not log or log.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Study log not found")
    await log.delete()