from datetime import date, timedelta
from ..models.user import User

async def complete_task(user: User):
    """Updates the user's streak and task count."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    if user.last_activity_date == yesterday:
        user.streak_count += 1
    elif user.last_activity_date != today:
        user.streak_count = 1
    
    user.last_activity_date = today
    user.total_tasks_completed += 1
    await user.save()
    return user.streak_count

async def get_daily_progress(user: User):
    """Calculates progress for the circular ring."""
    # For hackathon logic: assume 3 tasks per day goal
    goal = 3
    progress = (user.total_tasks_completed % goal) / goal
    return min(progress * 100, 100)

async def compute_level(user: User):
    """Calculates user level based on total tasks."""
    return (user.total_tasks_completed // 10) + 1