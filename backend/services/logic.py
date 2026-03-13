from datetime  import datetime, timezone, timedelta
from typing    import List, Optional
import numpy   as np


# ─────────────────────────────────────────────────────────────────────────────
# STREAK LOGIC  (exact spec implementation)
# ─────────────────────────────────────────────────────────────────────────────

def update_streak(user) -> dict:
    """
    Update a user's activity streak.

    Rules (from spec):
      - If user was active YESTERDAY → increment streak
      - If user missed a day (last activity < yesterday) → reset to 1
      - If user was active TODAY already → no change

    Parameters
    ----------
    user : any object with .last_activity_date (date) and .streak_count (int)

    Returns
    -------
    dict with updated streak_count, last_activity_date, streak_updated, message
    """
    today     = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)

    streak_updated = False
    message        = ""

    if user.last_activity_date == today:
        # Already logged today — no change
        message = f"Already active today. Streak: {user.streak_count} 🔥"

    elif user.last_activity_date == yesterday:
        # Active yesterday → continue streak
        user.streak_count     += 1
        user.last_activity_date = today
        streak_updated          = True
        message = f"Streak extended to {user.streak_count} days! 🔥"

    else:
        # Missed one or more days → reset
        user.streak_count       = 1
        user.last_activity_date = today
        streak_updated          = True
        message = "Streak reset. Starting fresh — you've got this! 💪"

    return {
        "streak_count"      : user.streak_count,
        "last_activity_date": str(user.last_activity_date),
        "streak_updated"    : streak_updated,
        "message"           : message,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE PREPROCESSING
# Converts BurnoutAnalysisRequest (frontend payload) → ML feature dict
# ─────────────────────────────────────────────────────────────────────────────

# Maps frontend string values to ML integer encodings
GENDER_MAP = {"male": 0, "female": 1, "other": 2}
EDU_MAP    = {
    "high_school": 1,
    "undergrad"  : 2,
    "postgrad"   : 3,
    "phd"        : 4,
}

def preprocess_request(request) -> dict:
    """
    Convert a BurnoutAnalysisRequest into the exact feature dict
    the ML model expects.

    Feature order must match training:
        age, weight, gender, edu_level, study_hours, sleep_hours,
        overwhelmed_freq, motivation_level, mental_exhaustion,
        concentration_diff, exam_anxiety, schedule_balance,
        procrastination, symptom_score

    Parameters
    ----------
    request : BurnoutAnalysisRequest

    Returns
    -------
    dict of {feature_name: value} ready for model.predict()
    """
    return {
        "age"               : request.age,
        "weight"            : request.weight,
        "gender"            : GENDER_MAP[request.gender.value],
        "edu_level"         : EDU_MAP[request.educational_level.value],
        "study_hours"       : request.study_hours,
        "sleep_hours"       : request.sleep_hours,
        "overwhelmed_freq"  : request.overwhelmed_score,
        "motivation_level"  : request.motivation_score,
        "mental_exhaustion" : request.exhaustion_score,
        "concentration_diff": request.concentration_score,
        "exam_anxiety"      : request.anxiety_score,
        "schedule_balance"  : request.balance_score,
        "procrastination"   : request.procrastination_score,
        "symptom_score"     : len(request.symptoms),   # count of checked symptoms
    }


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATION ENGINE
# Returns personalized suggestions based on prediction + input values
# ─────────────────────────────────────────────────────────────────────────────

def generate_recommendations(features: dict, burnout_risk: str) -> List[str]:
    """
    Generate personalized recommendations based on risk level and features.

    Parameters
    ----------
    features    : preprocessed feature dict
    burnout_risk: "Low", "Medium", or "High"

    Returns
    -------
    List of recommendation strings (max 5)
    """
    recs = []

    # Sleep
    if features["sleep_hours"] < 6:
        recs.append("🛏️ Critical: You're sleeping under 6 hours. "
                    "Aim for 7–9 hours — sleep is your #1 recovery tool.")
    elif features["sleep_hours"] < 7:
        recs.append("🛏️ Try to add 30–60 minutes to your sleep window.")

    # Study hours
    if features["study_hours"] > 10:
        recs.append("📚 You're studying 10+ hours/day. "
                    "Quality beats quantity — cap sessions at 8 hrs with breaks.")
    elif features["study_hours"] > 8:
        recs.append("📚 Consider the Pomodoro technique: "
                    "25 min focused study + 5 min break.")

    # Mental exhaustion
    if features["mental_exhaustion"] >= 4:
        recs.append("🧠 High mental exhaustion detected. "
                    "Schedule at least one full rest day per week.")

    # Motivation
    if features["motivation_level"] <= 2:
        recs.append("💪 Low motivation is a warning sign. "
                    "Break goals into smaller wins and celebrate progress.")

    # Schedule balance
    if features["schedule_balance"] <= 2:
        recs.append("🗓️ Your schedule feels chaotic. "
                    "Time-block your day — even 30 min planning saves hours.")

    # Exam anxiety
    if features["exam_anxiety"] >= 4:
        recs.append("😰 High exam anxiety. "
                    "Try mock tests under timed conditions to reduce fear.")

    # Symptoms
    if features["symptom_score"] >= 4:
        recs.append("🏥 You're experiencing multiple symptoms. "
                    "Consider speaking to a counselor or student support.")

    # High risk specific
    if burnout_risk == "High":
        recs.insert(0, "🚨 HIGH BURNOUT RISK: Please prioritize rest immediately. "
                       "Speak to someone you trust about how you're feeling.")

    return recs[:5]   # return top 5


def get_top_risk_factors(features: dict, importances: dict) -> List[str]:
    """
    Return top 3 features most contributing to this student's risk,
    with human-readable labels.
    """
    READABLE = {
        "sleep_hours"       : f"Low sleep ({features['sleep_hours']:.1f} hrs)",
        "study_hours"       : f"High study load ({features['study_hours']:.1f} hrs/day)",
        "motivation_level"  : f"Low motivation (score: {features['motivation_level']}/5)",
        "mental_exhaustion" : f"Mental exhaustion (score: {features['mental_exhaustion']}/5)",
        "exam_anxiety"      : f"Exam anxiety (score: {features['exam_anxiety']}/5)",
        "schedule_balance"  : f"Poor schedule balance (score: {features['schedule_balance']}/5)",
        "symptom_score"     : f"{features['symptom_score']} symptoms reported",
        "overwhelmed_freq"  : f"Feeling overwhelmed (score: {features['overwhelmed_freq']}/5)",
        "procrastination"   : f"Procrastination (score: {features['procrastination']}/5)",
    }

    sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    top3 = [READABLE.get(feat, feat) for feat, _ in sorted_features[:3]]
    return top3