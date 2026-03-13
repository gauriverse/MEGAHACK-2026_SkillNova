from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, date


# Use TWO dots to go out of 'routes' and into 'models'
from ..models.user import User
from ..models.task_item import TaskItem

# Use TWO dots to go out of 'routes' and into 'schemas'
from ..schemas import (
    TaskItemResponse, TaskCompleteRequest, TaskCompleteResponse,
    DailyProgressResponse, StreakResponse
)

# Use TWO dots to go out of 'routes' and into 'core'
from ..core.security import get_current_user
from ..services.streak_service import complete_task, get_daily_progress, compute_level
router = APIRouter(prefix="/tasks", tags=["Tasks & Streak"])


def _st(t: TaskItem) -> TaskItemResponse:
    return TaskItemResponse(
        id=str(t.id), user_id=t.user_id, analysis_id=t.analysis_id,
        category=t.category.value if hasattr(t.category, "value") else t.category,
        title=t.title, description=t.description,
        action_steps=t.action_steps, duration_minutes=t.duration_minutes,
        is_completed=t.is_completed, is_dismissed=t.is_dismissed,
        completed_at=t.completed_at, xp_reward=t.xp_reward,
        feedback_rating=t.feedback_rating,
        assigned_date=t.assigned_date, created_at=t.created_at,
    )


# ── Today's tasks (feeds Action Center cards) ─────────────────────────────────
@router.get("/today", response_model=List[TaskItemResponse])
async def today_tasks(current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date()
    tasks = await TaskItem.find(
        TaskItem.user_id       == str(current_user.id),
        TaskItem.assigned_date == today,
        TaskItem.is_dismissed  == False,
    ).to_list()
    return [_st(t) for t in tasks]


# ── Live Progress Ring ────────────────────────────────────────────────────────
@router.get("/progress", response_model=DailyProgressResponse)
async def progress(
    for_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
):
    data = await get_daily_progress(str(current_user.id), for_date)
    return DailyProgressResponse(**data, streak_count=current_user.streak_count)


# ── Header streak flame ───────────────────────────────────────────────────────
@router.get("/streak", response_model=StreakResponse)
async def streak(current_user: User = Depends(get_current_user)):
    return StreakResponse(
        streak_count=current_user.streak_count,
        last_activity_date=current_user.last_activity_date,
        total_tasks_completed=current_user.total_tasks_completed,
        xp_points=current_user.xp_points,
        level=compute_level(current_user.xp_points),
    )


# ── Mark task complete (triggers confetti when all_completed = True) ──────────
@router.post("/{task_id}/complete", response_model=TaskCompleteResponse)
async def complete(
    task_id: str,
    payload: TaskCompleteRequest,
    current_user: User = Depends(get_current_user),
):
    task = await TaskItem.get(task_id)
    if not task or task.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Task not found")

    res = await complete_task(task, current_user, payload.feedback_rating)
    user = res["user"]

    return TaskCompleteResponse(
        task=_st(res["task"]),
        all_completed=res["all_completed"],
        streak_leveled_up=res["streak_leveled_up"],
        level_up=res["level_up"],
        new_streak=user.streak_count,
        new_xp=user.xp_points,
        new_level=compute_level(user.xp_points),
        message=(
            "🎉 All tasks done! Streak updated! Keep it up!"
            if res["streak_leveled_up"]
            else "✅ Task completed! Great work!"
        ),
    )


# ── Dismiss task ──────────────────────────────────────────────────────────────
@router.post("/{task_id}/dismiss", response_model=TaskItemResponse)
async def dismiss(task_id: str, current_user: User = Depends(get_current_user)):
    task = await TaskItem.get(task_id)
    if not task or task.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_dismissed = True
    await task.save()
    return _st(task)


# ── All tasks paginated ───────────────────────────────────────────────────────
@router.get("/", response_model=List[TaskItemResponse])
async def list_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    completed: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
):
    q = TaskItem.find(TaskItem.user_id == str(current_user.id))
    if completed is not None:
        q = q.find({"is_completed": completed})
    tasks = await q.sort(-TaskItem.assigned_date)\
                   .skip((page - 1) * per_page).limit(per_page).to_list()
    return [_st(t) for t in tasks]