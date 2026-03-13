from typing import List, Dict, Any

RECOMMENDATION_BANK = [
    {
        "category": "sleep",
        "title": "Establish a Consistent Sleep Schedule",
        "description": "Irregular sleep disrupts your circadian rhythm, reducing memory consolidation and cognitive performance.",
        "action_steps": [
            "Set a fixed bedtime (e.g. 11 PM) and wake time (e.g. 7 AM)",
            "Enable Do Not Disturb 30 min before bed",
            "Avoid caffeine after 2 PM",
            "Keep your room cool at 18–20°C",
        ],
        "trigger": lambda f: f.get("sleep_consistency_score", 1) < 0.6,
    },
    {
        "category": "sleep",
        "title": "Increase Total Sleep Duration",
        "description": "You are averaging below the recommended 7–9 hours. Chronic sleep deprivation sharply increases burnout risk.",
        "action_steps": [
            "Move bedtime 15 minutes earlier each night until you reach 7+ hours",
            "Avoid all-nighters — one night of poor sleep impairs next-day performance significantly",
            "Take 10–20 min power naps between sessions if needed (not longer)",
        ],
        "trigger": lambda f: f.get("avg_sleep_hours", 8) < 6.5,
    },
    {
        "category": "sleep",
        "title": "Reduce Screen Time Before Bed",
        "description": "Blue light suppresses melatonin production, delaying sleep onset by up to 2 hours.",
        "action_steps": [
            "Stop using phone/laptop 45 minutes before sleep",
            "Enable Night Mode or blue-light filter on all devices",
            "Replace scrolling with reading a physical book or light journaling",
        ],
        "trigger": lambda f: f.get("used_screen_before_bed_rate", 0) > 0.5,
    },
    {
        "category": "study_habits",
        "title": "Apply the Pomodoro Technique",
        "description": "Structured intervals boost focus and prevent mental fatigue during long study sessions.",
        "action_steps": [
            "Study for 25 minutes, then take a strict 5-minute break",
            "After 4 Pomodoros, take a 15–30 min longer break",
            "Use apps like Forest or Be Focused to track intervals",
        ],
        "trigger": lambda f: f.get("avg_focus_level", 2) < 1.5 or f.get("avg_breaks_taken", 3) < 2,
    },
    {
        "category": "study_habits",
        "title": "Reduce Daily Study Hours",
        "description": "Studying more than 6–7 hours/day shows sharply diminishing returns and accelerates burnout.",
        "action_steps": [
            "Cap study sessions at 6 hours per day maximum",
            "Schedule hardest subjects in the morning when focus peaks",
            "Use active recall (flashcards, practice problems) instead of passive re-reading",
        ],
        "trigger": lambda f: f.get("avg_study_hours_per_day", 0) > 7,
    },
    {
        "category": "study_habits",
        "title": "Build a Weekly Study Plan",
        "description": "Unplanned studying leads to inefficiency and last-minute cramming — two major burnout contributors.",
        "action_steps": [
            "Every Sunday, list all upcoming deadlines for the week",
            "Assign each subject a fixed daily slot based on difficulty and deadline",
            "Use Notion or Google Calendar to track your plan",
        ],
        "trigger": lambda f: f.get("study_consistency_score", 1) < 0.6,
    },
    {
        "category": "breaks",
        "title": "Take More Intentional Breaks",
        "description": "You are taking fewer breaks than recommended. Regular breaks restore attention and prevent cognitive overload.",
        "action_steps": [
            "Schedule at least one 10-min break per hour of study",
            "Step away from your desk completely during breaks",
            "Try a short walk outdoors — even 5 minutes boosts mood and alertness",
        ],
        "trigger": lambda f: f.get("avg_breaks_taken", 3) < 1,
    },
    {
        "category": "stress_management",
        "title": "Practice Daily Mindfulness",
        "description": "Even 10 minutes of mindfulness per day measurably reduces cortisol and improves focus.",
        "action_steps": [
            "Try the Headspace or Calm app — start with the free beginner tracks",
            "Practice box breathing (4s inhale, 4s hold, 4s exhale, 4s hold) between sessions",
            "Journal 3 things you're grateful for each evening",
        ],
        "trigger": lambda f: f.get("avg_stress_level", 0) > 6,
    },
    {
        "category": "stress_management",
        "title": "Talk to Someone About Academic Pressure",
        "description": "Social support is one of the strongest protective factors against burnout. You don't have to manage this alone.",
        "action_steps": [
            "Schedule a check-in with a friend, family member, or mentor this week",
            "Visit your university's counseling or well-being center",
            "Join a study group — shared accountability reduces individual stress",
        ],
        "trigger": lambda f: f.get("avg_stress_level", 0) > 7 and f.get("burnout_score", 0) > 0.6,
    },
    {
        "category": "physical_activity",
        "title": "Add 30 Minutes of Physical Activity Daily",
        "description": "Exercise reduces cortisol, improves sleep quality, and boosts neuroplasticity — directly improving learning capacity.",
        "action_steps": [
            "Start with a 20–30 min walk after your study block",
            "Try bodyweight exercises (push-ups, squats) as a study break",
            "Aim for 3 dedicated workout sessions per week minimum",
        ],
        "trigger": lambda f: f.get("burnout_score", 0) > 0.4,
    },
]

PRIORITY_MAP = {
    "critical": "urgent",
    "high": "high",
    "moderate": "medium",
    "low": "low",
}


class RecommendationEngine:

    def generate(self, assessment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        risk = assessment_data.get("burnout_risk", "low")
        priority = PRIORITY_MAP.get(risk, "low")
        results = []

        for rec in RECOMMENDATION_BANK:
            try:
                if rec["trigger"](assessment_data):
                    results.append({
                        "category": rec["category"],
                        "priority": priority,
                        "title": rec["title"],
                        "description": rec["description"],
                        "action_steps": rec["action_steps"],
                    })
            except Exception:
                continue

        # Sort urgent first
        order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        results.sort(key=lambda r: order.get(r["priority"], 99))
        return results[:8]


recommendation_engine = RecommendationEngine()