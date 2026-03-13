
import joblib
import numpy  as np
import pandas as pd
import json
import os
from typing import List

# ── Paths ──────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE, "ml-model", "models", "burnout_model.joblib")
META_PATH  = os.path.join(BASE, "ml-model", "models", "model_metadata.json")

# ── Feature order must EXACTLY match training ──────────────────────────────
FEATURES = [
    "age", "weight", "gender", "edu_level",
    "study_hours", "sleep_hours",
    "overwhelmed_freq", "motivation_level", "mental_exhaustion",
    "concentration_diff", "exam_anxiety", "schedule_balance",
    "procrastination", "symptom_score",
]

# ── Load model once at startup (not on every request) ─────────────────────
_model    = None
_metadata = None

def _load_model():
    global _model, _metadata
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                f"Run: python3 ml-model/src/train.py"
            )
        _model = joblib.load(MODEL_PATH)
        with open(META_PATH) as f:
            _metadata = json.load(f)
    return _model, _metadata


def predict(features: dict) -> dict:
    """
    Run burnout prediction on preprocessed feature dict.

    Parameters
    ----------
    features : dict with all 14 keys from FEATURES list

    Returns
    -------
    dict:
        burnout_risk       : str  — "Low" / "Medium" / "High"
        confidence_scores  : dict — per-class probabilities
        top_risk_factors   : dict — feature importances
    """
    model, metadata = _load_model()

    # Build DataFrame in exact feature order (same as training)
    X = pd.DataFrame([{f: features[f] for f in FEATURES}])

    # Predict
    pred_encoded = model.predict(X)[0]
    pred_proba   = model.predict_proba(X)[0]

    # Decode label (0=High, 1=Low, 2=Medium — LabelEncoder alphabetical)
    label_map    = metadata["label_encoder"]   # {"0": "High", "1": "Low", "2": "Medium"}
    burnout_risk = label_map[str(pred_encoded)]

    # Confidence scores per class
    confidence = {
        label_map[str(i)]: round(float(p), 4)
        for i, p in enumerate(pred_proba)
    }

    # Feature importances from Random Forest
    rf = model.named_steps["classifier"]
    importances = {
        feat: round(float(imp), 4)
        for feat, imp in zip(FEATURES, rf.feature_importances_)
    }

    return {
        "burnout_risk"     : burnout_risk,
        "confidence_scores": confidence,
        "feature_importances": importances,
    }