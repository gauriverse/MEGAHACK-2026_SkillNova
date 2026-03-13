from typing import List, Dict, Any
from datetime import datetime, timezone, date

# ── Task bank — each entry has a trigger lambda and content ──────────────────
TASK_BANK = [
    {
        "category": "breathing",
        "title": "10-Minute Deep Breathing",
        "description": "Box breathing lowers cortisol and resets your nervous system in minutes.",
        "action_steps": [
            "Find a quiet spot and sit comfortably",
            "Inhale for 4s → hold 4s → exhale 4s → hold 4s",
            "Repeat the cycle for 10 minutes using a timer",
            "Notice your shoulders drop and jaw unclench",
        ],
        "duration_minutes": 10,
        "xp_reward": 15,
        "trigger": lambda f: f.get("exhaustion_score", 0) >= 3,
    },
    {
        "category": "hydration",
        "title": "Hydrate: Drink 500 ml of Water Now",
        "description": "Even mild dehydration worsens fatigue and concentration by up to 20%.",
        "action_steps": [
            "Fill a 500 ml bottle or glass right now",
            "Drink it slowly over the next 20 minutes",
            "Set a phone reminder to hydrate every 2 hours",
        ],
        "duration_minutes": 2,
        "xp_reward": 10,
        "trigger": lambda f: True,              # always assigned
    },
    {
        "category": "movement",
        "title": "5-Minute Desk Stretch",
        "description": "Prolonged sitting tightens muscles and reduces blood flow to the brain.",
        "action_steps": [
            "Stand up from your chair now",
            "Roll shoulders backwards 10 times",
            "Stretch neck left and right — 30 s each side",
            "Do 10 slow forward bends to release your lower back",
        ],
        "duration_minutes": 5,
        "xp_reward": 10,
        "trigger": lambda f: f.get("balance_score", 5) <= 3,
    },
    {
        "category": "movement",
        "title": "15-Minute Walk Outside",
        "description": "Sunlight + movement reduce cortisol and physically reset your focus clock.",
        "action_steps": [
            "Put your phone on Do Not Disturb",
            "Walk at a comfortable pace for 15 minutes",
            "Observe surroundings — no earphones this time",
            "Return feeling refreshed, not exhausted",
        ],
        "duration_minutes": 15,
        "xp_reward": 20,
        "trigger": lambda f: f.get("exhaustion_score", 0) >= 4,
    },
    {
        "category": "sleep",
        "title": "Set a Fixed Sleep Alarm for Tonight",
        "description": "Consistent bedtimes are the single biggest lever for reducing burnout.",
        "action_steps": [
            "Decide on a bedtime that gives you 7–8 hours",
            "Set a 'Wind down' alarm 30 min before that time",
            "No screens after that alarm — switch to a book",
        ],
        "duration_minutes": 3,
        "xp_reward": 15,
        "trigger": lambda f: f.get("sleep_hours", 8) < 7,
    },
    {
        "category": "mindfulness",
        "title": "5-Minute Brain Dump Journal",
        "description": "Writing out anxious thoughts clears working memory and lowers exam anxiety.",
        "action_steps": [
            "Open a notebook or notes app",
            "Set a 5-minute timer and write everything on your mind",
            "Don't edit — just dump it all out",
            "Close the notebook. Those thoughts are parked.",
        ],
        "duration_minutes": 5,
        "xp_reward": 15,
        "trigger": lambda f: f.get("anxiety_score", 0) >= 3,
    },
    {
        "category": "mindfulness",
        "title": "Write 3 Wins from Today",
        "description": "Focusing on progress (not gaps) measurably reduces overwhelm.",
        "action_steps": [
            "Write 3 things you accomplished today — however small",
            "For each one, write one sentence on why it matters",
            "Read them back aloud once",
        ],
        "duration_minutes": 5,
        "xp_reward": 10,
        "trigger": lambda f: f.get("overwhelmed_score", 0) >= 3,
    },
    {
        "category": "study",
        "title": "Plan Tomorrow's Study Block",
        "description": "Students with a written plan procrastinate 42% less than those without.",
        "action_steps": [
            "List 3 specific topics you will study tomorrow",
            "Assign a time slot to each (e.g. 9–10 AM: Maths revision)",
            "Set a phone reminder for your first block",
        ],
        "duration_minutes": 10,
        "xp_reward": 15,
        "trigger": lambda f: f.get("procrastination_score", 0) >= 3,
    },
    {
        "category": "break",
        "title": "Take a Full 30-Minute Study Break",
        "description": "Your brain consolidates learning during rest. This is productive, not lazy.",
        "action_steps": [
            "Close all textbooks and study tabs right now",
            "Do anything non-academic for 30 minutes",
            "Return to study with a 2-minute review of what you covered",
        ],
        "duration_minutes": 30,
        "xp_reward": 20,
        "trigger": lambda f: f.get("study_hours", 0) > 8,
    },
    {
        "category": "social",
        "title": "Send One Supportive Message",
        "description": "Social connection is one of the strongest evidence-based burnout shields.",
        "action_steps": [
            "Think of one friend or family member you haven't spoken to this week",
            "Send them a genuine message — even 'Hey, thinking of you'",
            "Notice how giving support also lifts your own mood",
        ],
        "duration_minutes": 5,
        "xp_reward": 10,
        "trigger": lambda f: f.get("overwhelmed_score", 0) >= 4,
    },
]

MAX_TASKS_PER_DAY = 6


async def generate_tasks(
    user_id: str,
    analysis_id: str,
    features: Dict[str, Any],
    assigned_date: date = None,
) -> List:
    """
    Evaluate each task's trigger against the analysis features.
    Insert matching TaskItem documents and return the list (capped at MAX_TASKS_PER_DAY).
    """
    from models.task_item import TaskItem, DailyTaskSummary

    target_date = assigned_date or datetime.now(timezone.utc).date()
    created: List[TaskItem] = []

    for td in TASK_BANK:
        if len(created) >= MAX_TASKS_PER_DAY:
            break
        try:
            if td["trigger"](features):
                task = TaskItem(
                    user_id=user_id,
                    analysis_id=analysis_id,
                    category=td["category"],
                    title=td["title"],
                    description=td["description"],
                    action_steps=td["action_steps"],
                    duration_minutes=td.get("duration_minutes"),
                    xp_reward=td.get("xp_reward", 10),
                    assigned_date=target_date,
                )
                await task.insert()
                created.append(task)
        except Exception:
            continue

    # Initialise daily summary row
    summary = await DailyTaskSummary.find_one(
        DailyTaskSummary.user_id      == user_id,
        DailyTaskSummary.summary_date == target_date,
    )
    if not summary:
        summary = DailyTaskSummary(
            user_id=user_id,
            summary_date=target_date,
            total_tasks=len(created),
        )
    else:
        summary.total_tasks += len(created)
    await summary.save()

    return created