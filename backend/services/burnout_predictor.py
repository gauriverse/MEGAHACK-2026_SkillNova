import numpy as np
import joblib
import logging
from typing import Dict, Any
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)

# ── Encoding maps (must match ML training script) ────────────────────────────
GENDER_ENCODING   = {"male": 0, "female": 1, "other": 2}
EDU_ENCODING      = {"school": 1, "undergraduate": 2, "postgraduate": 3, "other": 4}

# Exact feature order used during training
FEATURE_NAMES = [
    "age", "weight", "gender_encoded", "edu_level_encoded",
    "study_hours", "sleep_hours",
    "overwhelmed_score", "motivation_score", "exhaustion_score",
    "concentration_score", "anxiety_score", "balance_score",
    "procrastination_score", "symptom_score",
]


class BurnoutPredictor:
    """
    Wraps burnout_model.joblib — a scikit-learn Pipeline(StandardScaler + RandomForest).
    Output classes: ["low", "medium", "high"]  (3-class)
    Falls back to rule-based heuristic when model file is missing.
    """

    def __init__(self):
        self.model = None
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        path = Path(settings.MODEL_PATH)
        if path.exists():
            try:
                self.model = joblib.load(path)
                self.model_loaded = True
                logger.info(f"✅ ML model loaded from {path}")
            except Exception as e:
                logger.warning(f"⚠️  Model load failed: {e}. Using heuristic.")
        else:
            logger.warning(f"⚠️  Model not found at {path}. Using heuristic fallback.")

    def _build_vector(self, f: Dict[str, Any]) -> np.ndarray:
        return np.array([[
            f["age"],
            f["weight"],
            GENDER_ENCODING.get(f["gender"], 2),
            EDU_ENCODING.get(f["educational_level"], 1),
            f["study_hours"],
            f["sleep_hours"],
            f["overwhelmed_score"],
            f["motivation_score"],
            f["exhaustion_score"],
            f["concentration_score"],
            f["anxiety_score"],
            f["balance_score"],
            f["procrastination_score"],
            f["symptom_score"],
        ]])

    # ── Rule-based fallback — mirrors ML training label logic exactly ─────────
    def _heuristic(self, f: Dict[str, Any]) -> Dict[str, Any]:
        study     = f["study_hours"]
        sleep     = f["sleep_hours"]
        exhaustion = f["exhaustion_score"]
        balance   = f["balance_score"]
        anxiety   = f["anxiety_score"]
        motivation = f["motivation_score"]
        symptom   = f["symptom_score"]

        # Mirror training label rules
        if study > 10 and sleep < 5 and exhaustion >= 4:
            risk, score = "high",   0.85
        elif balance < 3 or anxiety >= 4:
            risk, score = "medium", 0.55
        elif sleep > 7 and motivation >= 4:
            risk, score = "low",    0.15
        else:
            # Weighted continuous score for edge cases
            s = 0.0
            s += max(0, (7  - sleep)   * 0.06)
            s += max(0, (study - 6)    * 0.04)
            s += max(0, (exhaustion-3) * 0.08)
            s += max(0, (5-motivation) * 0.06)
            s += max(0, (anxiety-3)    * 0.07)
            s += max(0, (3-balance)    * 0.06)
            s += symptom               * 0.04
            score = float(np.clip(s, 0.01, 0.99))
            risk  = "high" if score >= 0.65 else "medium" if score >= 0.35 else "low"

        risk_factors = {
            "sleep_deprivation":      round(max(0, (7   - sleep)    * 0.06), 3),
            "overwork":               round(max(0, (study - 6)      * 0.04), 3),
            "mental_exhaustion":      round((exhaustion - 1)        * 0.06, 3),
            "low_motivation":         round((5 - motivation)        * 0.05, 3),
            "exam_anxiety":           round((anxiety - 1)           * 0.05, 3),
            "poor_schedule_balance":  round((5 - balance)           * 0.04, 3),
            "symptom_burden":         round(symptom                 * 0.04, 3),
        }
        return {"burnout_score": score, "burnout_risk": risk,
                "confidence": 0.70, "risk_factors": risk_factors}

    def _get_importances(self) -> Dict[str, float]:
        try:
            clf = getattr(self.model, "named_steps", {}).get("clf") or self.model
            return {n: round(float(i), 4)
                    for n, i in zip(FEATURE_NAMES, clf.feature_importances_)}
        except Exception:
            return {}

    # ── Public API ────────────────────────────────────────────────────────────
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        if self.model_loaded:
            try:
                X      = self._build_vector(features)
                proba  = self.model.predict_proba(X)[0]    # [p_low, p_med, p_high]
                labels = ["low", "medium", "high"]
                idx    = int(np.argmax(proba))
                return {
                    "burnout_risk":  labels[idx],
                    "burnout_score": round(float(proba[2]), 4),  # p(high) as score
                    "confidence":    round(float(np.max(proba)), 4),
                    "risk_factors":  self._get_importances(),
                }
            except Exception as e:
                logger.error(f"Model predict failed: {e}. Falling back to heuristic.")
        return self._heuristic(features)


burnout_predictor = BurnoutPredictor()