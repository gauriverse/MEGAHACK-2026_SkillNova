from fastapi  import APIRouter, HTTPException
from datetime import datetime, timezone

from backend.schemas.schemas       import BurnoutAnalysisRequest, BurnoutAnalysisResponse
from backend.services              import burnout_predictor
from backend.services.logic        import (
    preprocess_request,
    generate_recommendations,
    get_top_risk_factors,
)

router = APIRouter(prefix="/api/burnout", tags=["Burnout Analysis"])


@router.post("/analyze", response_model=BurnoutAnalysisResponse)
async def analyze_burnout(request: BurnoutAnalysisRequest):
    """
    Analyze burnout risk from student habit inputs.

    1. Validate input (Pydantic handles this automatically)
    2. Preprocess request → ML feature dict
    3. Run prediction
    4. Generate recommendations
    5. Return structured response
    """
    try:
        # Step 1 — Preprocess frontend payload → model features
        features = preprocess_request(request)

        # Step 2 — Run ML prediction
        result = burnout_predictor.predict(features)

        # Step 3 — Generate personalized recommendations
        recommendations = generate_recommendations(
            features, result["burnout_risk"]
        )

        # Step 4 — Get top risk factors (human-readable)
        top_risk_factors = get_top_risk_factors(
            features, result["feature_importances"]
        )

        return BurnoutAnalysisResponse(
            burnout_risk      = result["burnout_risk"],
            confidence_scores = result["confidence_scores"],
            symptom_count     = len(request.symptoms),
            top_risk_factors  = top_risk_factors,
            recommendations   = recommendations,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if the ML model is loaded and ready."""
    try:
        burnout_predictor._load_model()
        return {
            "status"   : "ok",
            "model"    : "burnout_model.joblib",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run: python3 ml-model/src/train.py"
        )