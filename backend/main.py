"""
Burnout Predictor – FastAPI Backend
Uses plain pymongo (sync) via run_in_executor — no motor dependency needed.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib, json, os, numpy as np
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
from concurrent.futures import ThreadPoolExecutor
import asyncio
import uvicorn

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Student Burnout Predictor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MongoDB (plain sync pymongo) ──────────────────────────────────────────────
MONGO_URL  = os.getenv("MONGO_URL", "mongodb://localhost:27017")
_client    = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
_db        = _client["burnout_db"]
students   : Collection = _db["students"]
predictions: Collection = _db["predictions"]

_executor = ThreadPoolExecutor(max_workers=4)

async def run(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, fn, *args)

# ── ML Artifacts ──────────────────────────────────────────────────────────────
ML_DIR = os.path.join(os.path.dirname(__file__), "..", "ml-model")
model  = joblib.load(os.path.join(ML_DIR, "burnout_model.pkl"))
scaler = joblib.load(os.path.join(ML_DIR, "scaler.pkl"))
with open(os.path.join(ML_DIR, "model_meta.json")) as f:
    meta = json.load(f)
FEATURES = meta["features"]

# ── Schema ────────────────────────────────────────────────────────────────────
class StudentInput(BaseModel):
    name:                    str
    email:                   str
    age:                     int   = Field(ge=15, le=35)
    study_hours_per_day:     float = Field(ge=0,  le=16)
    sleep_hours:             float = Field(ge=2,  le=12)
    break_frequency:         int   = Field(ge=0,  le=10)
    study_consistency_score: float = Field(ge=0,  le=10)
    days_studied_per_week:   int   = Field(ge=0,  le=7)
    assignment_load:         float = Field(ge=1,  le=10)
    exam_frequency:          int   = Field(ge=0,  le=10)
    deadline_stress:         float = Field(ge=0,  le=10)
    gpa_pressure:            float = Field(ge=0,  le=4)
    extracurricular_hours:   float = Field(ge=0,  le=20)
    mood_score:              float = Field(ge=1,  le=10)
    focus_level:             float = Field(ge=1,  le=10)
    social_interaction_hrs:  float = Field(ge=0,  le=12)
    physical_activity_hrs:   float = Field(ge=0,  le=8)
    screen_time_non_study:   float = Field(ge=0,  le=16)
    fatigue_level:           float = Field(ge=1,  le=10)
    motivation_score:        float = Field(ge=1,  le=10)
    anxiety_score:           float = Field(ge=1,  le=10)
    concentration_difficulty:float = Field(ge=1,  le=10)
    procrastination_score:   float = Field(ge=1,  le=10)


def serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


def get_recommendations(data: dict, burnout: bool, prob: float) -> list:
    recs = []

    if data["sleep_hours"] < 7:
        recs.append({
            "category": "Sleep", "priority": "high", "icon": "🌙",
            "title": "Improve Sleep Duration",
            "description": f"You're sleeping {data['sleep_hours']:.1f}h. Target 7-9 hours.",
            "action": "Set a consistent bedtime and avoid screens 30 min before sleep."
        })
    if data["study_hours_per_day"] > 8:
        recs.append({
            "category": "Study Habits", "priority": "high", "icon": "📚",
            "title": "Reduce Excessive Study Hours",
            "description": f"Studying {data['study_hours_per_day']:.1f}h/day accelerates fatigue.",
            "action": "Cap study at 6-8h using time-blocking. Quality beats quantity."
        })
    if data["break_frequency"] < 2:
        recs.append({
            "category": "Study Habits", "priority": "medium", "icon": "⏱️",
            "title": "Take Regular Breaks",
            "description": "Too few breaks increase mental fatigue rapidly.",
            "action": "Try Pomodoro: 25 min study → 5 min break."
        })
    if data["physical_activity_hrs"] < 1:
        recs.append({
            "category": "Wellness", "priority": "medium", "icon": "🏃",
            "title": "Add Daily Physical Activity",
            "description": "Low activity correlates with higher stress.",
            "action": "Add a 30-minute walk or workout daily."
        })
    if data["anxiety_score"] > 6:
        recs.append({
            "category": "Mental Health", "priority": "high", "icon": "🧘",
            "title": "Manage Anxiety Levels",
            "description": f"Anxiety score {data['anxiety_score']:.1f}/10 is elevated.",
            "action": "Practice 4-7-8 breathing or 10-min daily meditation."
        })
    if data["social_interaction_hrs"] < 1:
        recs.append({
            "category": "Social", "priority": "low", "icon": "👥",
            "title": "Increase Social Connection",
            "description": "Social isolation amplifies burnout.",
            "action": "Schedule at least 1 hour of social activity per day."
        })
    if data["motivation_score"] < 4:
        recs.append({
            "category": "Motivation", "priority": "high", "icon": "🎯",
            "title": "Rebuild Intrinsic Motivation",
            "description": f"Motivation {data['motivation_score']:.1f}/10 is an early burnout signal.",
            "action": "Break goals into micro-tasks and celebrate small wins."
        })
    if data["screen_time_non_study"] > 6:
        recs.append({
            "category": "Digital Wellness", "priority": "medium", "icon": "📵",
            "title": "Reduce Non-Study Screen Time",
            "description": f"{data['screen_time_non_study']:.1f}h recreational screen time drains energy.",
            "action": "Set app timers. Replace 1h of scrolling with reading."
        })
    if data["study_consistency_score"] < 5:
        recs.append({
            "category": "Study Habits", "priority": "medium", "icon": "📅",
            "title": "Build a Consistent Study Schedule",
            "description": "Irregular patterns increase cognitive load.",
            "action": "Fix 2-3 daily study blocks. Consistency reduces decision fatigue."
        })
    if not recs:
        recs.append({
            "category": "General", "priority": "low", "icon": "✅",
            "title": "Maintain Your Healthy Habits",
            "description": "Your patterns look healthy. Keep it up!",
            "action": "Continue self-assessments every 2 weeks."
        })
    return recs


# ── Helper lambdas for thread executor ───────────────────────────────────────
def _find_one(col, query):       return col.find_one(query)
def _insert_one(col, doc):       return col.insert_one(doc)
def _update_one(col, q, update): return col.update_one(q, update)
def _count(col, query):          return col.count_documents(query)
def _find_many(col, query, sort_field, sort_dir, skip, limit):
    return list(col.find(query).sort(sort_field, sort_dir).skip(skip).limit(limit))
def _aggregate(col, pipeline):  return list(col.aggregate(pipeline))


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "Burnout Predictor API", "version": "1.0.0",
            "model_accuracy": meta["accuracy"]}


@app.post("/predict")
async def predict(data: StudentInput):
    vec   = np.array([[getattr(data, f) for f in FEATURES]])
    vec_s = scaler.transform(vec)
    pred  = int(model.predict(vec_s)[0])
    prob  = float(model.predict_proba(vec_s)[0][1])

    risk_level = (
        "Critical" if prob > 0.75 else
        "High"     if prob > 0.55 else
        "Moderate" if prob > 0.35 else
        "Low"
    )

    recs   = get_recommendations(data.model_dump(), pred == 1, prob)
    record = {
        **data.model_dump(),
        "burnout_predicted":   pred == 1,
        "burnout_probability": round(prob * 100, 2),
        "risk_level":          risk_level,
        "recommendations":     recs,
        "created_at":          datetime.now(timezone.utc).isoformat()
    }

    existing = await run(_find_one, students, {"email": data.email})
    if existing:
        await run(_update_one, students, {"email": data.email}, {"$set": record})
        student_id = str(existing["_id"])
    else:
        res = await run(_insert_one, students, record)
        student_id = str(res.inserted_id)

    pred_record = {**record, "student_id": student_id}
    await run(_insert_one, predictions, pred_record)

    return {
        "student_id":          student_id,
        "burnout_predicted":   pred == 1,
        "burnout_probability": round(prob * 100, 2),
        "risk_level":          risk_level,
        "recommendations":     recs
    }


@app.get("/students")
async def get_students(skip: int = 0, limit: int = 50):
    from pymongo import DESCENDING
    docs  = await run(_find_many, students, {}, "created_at", -1, skip, limit)
    total = await run(_count, students, {})
    return {"students": [serialize(d) for d in docs], "total": total}


@app.get("/students/{student_id}")
async def get_student(student_id: str):
    doc = await run(_find_one, students, {"_id": ObjectId(student_id)})
    if not doc:
        raise HTTPException(404, "Student not found")
    return serialize(doc)


@app.get("/dashboard-stats")
async def dashboard_stats():
    total          = await run(_count, students, {})
    burnout_count  = await run(_count, students, {"burnout_predicted": True})
    critical_count = await run(_count, students, {"risk_level": "Critical"})
    high_count     = await run(_count, students, {"risk_level": "High"})
    moderate_count = await run(_count, students, {"risk_level": "Moderate"})
    low_count      = await run(_count, students, {"risk_level": "Low"})

    pipeline = [{"$group": {
        "_id": None,
        "avg_sleep":       {"$avg": "$sleep_hours"},
        "avg_study":       {"$avg": "$study_hours_per_day"},
        "avg_anxiety":     {"$avg": "$anxiety_score"},
        "avg_motivation":  {"$avg": "$motivation_score"},
        "avg_burnout_prob":{"$avg": "$burnout_probability"}
    }}]
    agg  = await run(_aggregate, students, pipeline)
    avgs = agg[0] if agg else {}

    return {
        "total_students":    total,
        "burnout_count":     burnout_count,
        "burnout_rate":      round(burnout_count / total * 100, 1) if total else 0,
        "risk_distribution": {
            "critical": critical_count,
            "high":     high_count,
            "moderate": moderate_count,
            "low":      low_count
        },
        "averages": {
            "sleep":        round(avgs.get("avg_sleep", 0), 2),
            "study_hours":  round(avgs.get("avg_study", 0), 2),
            "anxiety":      round(avgs.get("avg_anxiety", 0), 2),
            "motivation":   round(avgs.get("avg_motivation", 0), 2),
            "burnout_prob": round(avgs.get("avg_burnout_prob", 0), 2)
        },
        "model_accuracy":      meta["accuracy"],
        "feature_importances": meta["importances"]
    }


@app.get("/prediction-history/{email}")
async def prediction_history(email: str):
    docs = await run(_find_many, predictions, {"email": email}, "created_at", -1, 0, 20)
    return {"history": [serialize(d) for d in docs]}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)