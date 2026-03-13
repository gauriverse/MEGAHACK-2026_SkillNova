from fastapi import APIRouter, Depends, HTTPException, Query, status

from models.user import User
from models.burnout_analysis import BurnoutAnalysis
from models.recommendation import Recommendation
from schemas import BurnoutAnalysisRequest, BurnoutAnalysisResponse, PaginatedResponse
from core.security import get_current_user
from services.burnout_predictor import burnout_predictor
from services.task_generator import generate_tasks
from services.recommendation_engine import recommendation_engine

router = APIRouter(prefix="/analysis", tags=["Deep Dive Analysis"])


def _serialize(a: BurnoutAnalysis) -> BurnoutAnalysisResponse:
    return BurnoutAnalysisResponse(
        id=str(a.id), user_id=a.user_id,
        age=a.age, weight=a.weight, gender=a.gender,
        educational_level=a.educational_level,
        study_hours=a.study_hours, sleep_hours=a.sleep_hours,
        overwhelmed_score=a.overwhelmed_score, motivation_score=a.motivation_score,
        exhaustion_score=a.exhaustion_score, concentration_score=a.concentration_score,
        anxiety_score=a.anxiety_score, balance_score=a.balance_score,
        procrastination_score=a.procrastination_score,
        symptoms=a.symptoms, symptom_score=a.symptom_score,
        burnout_risk=a.burnout_risk.value, burnout_score=a.burnout_score,
        confidence=a.confidence, risk_factors=a.risk_factors,
        assessed_at=a.assessed_at,
    )


@router.post("/", response_model=BurnoutAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def run_deep_dive(
    payload: BurnoutAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Core endpoint called after the 4-step wizard completes.
    1. Runs ML prediction
    2. Persists BurnoutAnalysis document
    3. Generates TaskItem cards (Action Center)
    4. Generates text Recommendations
    """
    user_id      = str(current_user.id)
    symptom_score = min(len(payload.symptoms), 7)

    features = {
        "age": payload.age, "weight": payload.weight,
        "gender": payload.gender, "educational_level": payload.educational_level,
        "study_hours": payload.study_hours, "sleep_hours": payload.sleep_hours,
        "overwhelmed_score": payload.overwhelmed_score,
        "motivation_score": payload.motivation_score,
        "exhaustion_score": payload.exhaustion_score,
        "concentration_score": payload.concentration_score,
        "anxiety_score": payload.anxiety_score,
        "balance_score": payload.balance_score,
        "procrastination_score": payload.procrastination_score,
        "symptom_score": symptom_score,
    }

    prediction = burnout_predictor.predict(features)

    # Persist demographics on the user object (convenience)
    current_user.age               = payload.age
    current_user.weight            = payload.weight
    current_user.gender            = payload.gender
    current_user.educational_level = payload.educational_level
    await current_user.save()

    # Persist analysis
    analysis = BurnoutAnalysis(
        user_id=user_id,
        age=payload.age, weight=payload.weight,
        gender=payload.gender, educational_level=payload.educational_level,
        study_hours=payload.study_hours, sleep_hours=payload.sleep_hours,
        overwhelmed_score=payload.overwhelmed_score,
        motivation_score=payload.motivation_score,
        exhaustion_score=payload.exhaustion_score,
        concentration_score=payload.concentration_score,
        anxiety_score=payload.anxiety_score,
        balance_score=payload.balance_score,
        procrastination_score=payload.procrastination_score,
        symptoms=payload.symptoms, symptom_score=symptom_score,
        burnout_risk=prediction["burnout_risk"],
        burnout_score=prediction["burnout_score"],
        confidence=prediction["confidence"],
        risk_factors=prediction["risk_factors"],
    )
    await analysis.insert()
    analysis_id = str(analysis.id)

    # Generate task cards for Action Center
    await generate_tasks(user_id, analysis_id, {**features, **prediction})

    # Generate text recommendations
    for raw in recommendation_engine.generate({**features, **prediction}):
        await Recommendation(
            user_id=user_id, assessment_id=analysis_id,
            category=raw["category"], priority=raw["priority"],
            title=raw["title"], description=raw["description"],
            action_steps=raw["action_steps"],
        ).insert()

    return _serialize(analysis)


@router.get("/", response_model=PaginatedResponse)
async def list_analyses(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    q     = BurnoutAnalysis.find(BurnoutAnalysis.user_id == str(current_user.id))
    total = await q.count()
    items = await q.sort(-BurnoutAnalysis.assessed_at)\
                   .skip((page - 1) * per_page).limit(per_page).to_list()
    return PaginatedResponse(
        items=[_serialize(a) for a in items], total=total,
        page=page, per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.get("/latest", response_model=BurnoutAnalysisResponse)
async def get_latest(current_user: User = Depends(get_current_user)):
    a = await BurnoutAnalysis.find(
        BurnoutAnalysis.user_id == str(current_user.id)
    ).sort(-BurnoutAnalysis.assessed_at).first_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="No analysis found. Complete the Deep Dive first.")
    return _serialize(a)


@router.get("/{analysis_id}", response_model=BurnoutAnalysisResponse)
async def get_analysis(analysis_id: str, current_user: User = Depends(get_current_user)):
    a = await BurnoutAnalysis.get(analysis_id)
    if not a or a.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _serialize(a)