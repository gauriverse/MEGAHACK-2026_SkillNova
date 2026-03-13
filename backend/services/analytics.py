from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import numpy as np

from models.study_log import StudyLog, FocusLevel
from models.sleep_log import SleepLog

FOCUS_ENCODING = {FocusLevel.LOW: 0, FocusLevel.MEDIUM: 1, FocusLevel.HIGH: 2}


async def aggregate_features(user_id: str, days: int = 7) -> Optional[Dict[str, Any]]:
    """
    Fetch raw logs from MongoDB and aggregate into ML feature vector.
    Returns None if not enough data.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Fetch study logs
    study_logs = await StudyLog.find(
        StudyLog.user_id == user_id,
        StudyLog.study_date >= since,
    ).to_list()

    # Fetch sleep logs
    sleep_logs = await SleepLog.find(
        SleepLog.user_id == user_id,
        SleepLog.sleep_date >= since,
    ).to_list()

    if not study_logs and not sleep_logs:
        return None

    # ── Study features ───────────────────────────────────────────────────────
    if study_logs:
        daily_study: Dict[str, float] = {}
        for log in study_logs:
            day_key = log.study_date.date().isoformat()
            daily_study[day_key] = daily_study.get(day_key, 0) + log.duration_minutes / 60

        avg_study_hours_per_day = float(np.mean(list(daily_study.values())))
        study_std = float(np.std(list(daily_study.values()))) if len(daily_study) > 1 else 0.0
        study_consistency_score = float(
            max(0.0, 1.0 - (study_std / max(avg_study_hours_per_day, 0.1)))
        )
        avg_stress_level = float(np.mean([log.stress_level for log in study_logs]))
        avg_focus_level = float(np.mean([FOCUS_ENCODING[log.focus_level] for log in study_logs]))
        avg_breaks_taken = float(np.mean([log.breaks_taken for log in study_logs]))
        prod = [log.productivity_score for log in study_logs if log.productivity_score is not None]
        avg_productivity_score = float(np.mean(prod)) if prod else 0.5
    else:
        avg_study_hours_per_day = 0.0
        study_consistency_score = 0.5
        avg_stress_level = 5.0
        avg_focus_level = 1.0
        avg_breaks_taken = 1.0
        avg_productivity_score = 0.5

    # ── Sleep features ───────────────────────────────────────────────────────
    if sleep_logs:
        hours = [log.sleep_duration_hours for log in sleep_logs]
        avg_sleep_hours = float(np.mean(hours))
        sleep_std = float(np.std(hours)) if len(hours) > 1 else 0.0
        sleep_consistency_score = float(max(0.0, 1.0 - sleep_std / 2.0))
        used_screen_rate = float(
            sum(1 for log in sleep_logs if log.used_screen_before_bed) / len(sleep_logs)
        )
    else:
        avg_sleep_hours = 7.0
        sleep_consistency_score = 0.5
        used_screen_rate = 0.0

    days_analyzed = max(
        len({log.study_date.date() for log in study_logs}),
        len({log.sleep_date.date() for log in sleep_logs}),
    )

    return {
        "avg_study_hours_per_day": round(avg_study_hours_per_day, 2),
        "avg_sleep_hours": round(avg_sleep_hours, 2),
        "avg_stress_level": round(avg_stress_level, 2),
        "avg_focus_level": round(avg_focus_level, 2),
        "avg_breaks_taken": round(avg_breaks_taken, 2),
        "avg_productivity_score": round(avg_productivity_score, 2),
        "sleep_consistency_score": round(sleep_consistency_score, 4),
        "study_consistency_score": round(study_consistency_score, 4),
        "used_screen_before_bed_rate": round(used_screen_rate, 4),
        "days_analyzed": days_analyzed,
    }


async def get_streak(user_id: str) -> int:
    """Count consecutive days the user logged any study session."""
    logs = await StudyLog.find(
        StudyLog.user_id == user_id,
    ).sort(-StudyLog.study_date).to_list()

    seen_dates = sorted({log.study_date.date() for log in logs}, reverse=True)

    streak = 0
    today = datetime.now(timezone.utc).date()
    for i, d in enumerate(seen_dates):
        if d == today - timedelta(days=i):
            streak += 1
        else:
            break
    return streak