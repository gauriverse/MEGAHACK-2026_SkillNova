from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from datetime import datetime

from models.user import User
from models.sleep_log import SleepLog
from schemas import SleepLogCreate, SleepLogResponse, PaginatedResponse
from core.security import get_current_user

router = APIRouter(prefix="/sleep-logs", tags=["Sleep Logs"])


def _serialize(log: SleepLog) -> SleepLogResponse:
    return SleepLogResponse(
        id=str(log.id),
        user_id=log.user_id,
        sleep_duration_hours=log.sleep_duration_hours,
        sleep_quality=log.sleep_quality.value,
        bedtime=log.bedtime,
        wake_time=log.wake_time,
        interruptions=log.interruptions,
        used_screen_before_bed=log.used_screen_before_bed,
        energy_level_morning=log.energy_level_morning,
        sleep_date=log.sleep_date,
        logged_at=log.logged_at,
    )


@router.post("/", response_model=SleepLogResponse, status_code=status.HTTP_201_CREATED)
async def create_sleep_log(
    payload: SleepLogCreate,
    current_user: User = Depends(get_current_user),
):
    log = SleepLog(
        user_id=str(current_user.id),
        sleep_duration_hours=payload.sleep_duration_hours,
        sleep_quality=payload.sleep_quality.value,
        bedtime=payload.bedtime,
        wake_time=payload.wake_time,
        interruptions=payload.interruptions,
        used_screen_before_bed=payload.used_screen_before_bed,
        energy_level_morning=payload.energy_level_morning,
        sleep_date=payload.sleep_date,
    )
    await log.insert()
    return _serialize(log)


@router.get("/", response_model=PaginatedResponse)
async def list_sleep_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
):
    query = SleepLog.find(SleepLog.user_id == str(current_user.id))

    if from_date:
        query = query.find(SleepLog.sleep_date >= from_date)
    if to_date:
        query = query.find(SleepLog.sleep_date <= to_date)

    total = await query.count()
    logs = await query.sort(-SleepLog.sleep_date).skip((page - 1) * per_page).limit(per_page).to_list()

    return PaginatedResponse(
        items=[_serialize(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/{log_id}", response_model=SleepLogResponse)
async def get_sleep_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
):
    log = await SleepLog.get(log_id)
    if not log or log.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Sleep log not found")
    return _serialize(log)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sleep_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
):
    log = await SleepLog.get(log_id)
    if not log or log.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Sleep log not found")
    await log.delete()