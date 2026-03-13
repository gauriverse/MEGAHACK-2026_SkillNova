import numpy as np
import joblib
import logging
from typing import Dict, Any, Tuple
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)


class BurnoutPredictor:
    """
    Wraps the trained sklearn model (model.pkl).
    Falls back to a rule-based heuristic when the model file is absent
    (useful during development before ML training is complete).
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
                logger.info(f"ML model loaded from {path}")
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}. Using heuristic fallback.")
        else:
            logger.warning(f"model.pkl not found at {path}. Using heuristic fallback.")

    # ── Feature vector ───────────────────────────────────────────────────────

    def _build_feature_vector(self, features: Dict[str, float]) -> np.ndarray:
        return np.array([[
            features["avg_study_hours_per_day"],
            features["avg_sleep_hours"],
            features["avg_stress_level"],
            features["avg_focus_level"],
            features["avg_breaks_taken"],
            features["avg_productivity_score"],
            features["sleep_consistency_score"],
            features["study_consistency_score"],
            features["days_analyzed"],
        ]])

    # ── Heuristic fallback ───────────────────────────────────────────────────

    def _heuristic_predict(self, features: Dict[str, float]) -> Tuple[float, float, Dict]:
        score = 0.0
        risk_factors = {}

        # Sleep deprivation
        sleep = features["avg_sleep_hours"]
        delta = 0.30 if sleep < 5 else 0.20 if sleep < 6 else 0.10 if sleep < 7 else 0.0
        score += delta
        risk_factors["sleep_deprivation"] = round(delta, 3)

        # Over-studying
        study = features["avg_study_hours_per_day"]
        delta = 0.25 if study > 10 else 0.15 if study > 8 else 0.05 if study > 6 else 0.0
        score += delta
        risk_factors["overwork"] = round(delta, 3)

        # High stress
        delta = round(max(0.0, (features["avg_stress_level"] - 5) / 10), 3)
        score += delta
        risk_factors["high_stress"] = delta

        # Low focus
        delta = round(max(0.0, (2 - features["avg_focus_level"]) * 0.08), 3)
        score += delta
        risk_factors["low_focus"] = delta

        # Sleep inconsistency
        delta = round((1 - features["sleep_consistency_score"]) * 0.15, 3)
        score += delta
        risk_factors["sleep_inconsistency"] = delta

        # Insufficient breaks
        breaks = features["avg_breaks_taken"]
        delta = 0.10 if breaks < 1 else 0.05 if breaks < 2 else 0.0
        score += delta
        risk_factors["insufficient_breaks"] = round(delta, 3)

        return round(min(1.0, score), 4), 0.72, risk_factors

    # ── Public API ───────────────────────────────────────────────────────────

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        if self.model_loaded:
            try:
                X = self._build_feature_vector(features)
                burnout_score = float(self.model.predict_proba(X)[0][1])
                confidence = float(np.max(self.model.predict_proba(X)))
                risk_factors = self._get_feature_importances()
            except Exception as e:
                logger.error(f"Model prediction failed: {e}. Using heuristic.")
                burnout_score, confidence, risk_factors = self._heuristic_predict(features)
        else:
            burnout_score, confidence, risk_factors = self._heuristic_predict(features)

        return {
            "burnout_score": burnout_score,
            "burnout_risk": self._score_to_risk(burnout_score),
            "confidence": confidence,
            "risk_factors": risk_factors,
        }

    def _score_to_risk(self, score: float) -> str:
        if score < 0.25:  return "low"
        if score < 0.50:  return "moderate"
        if score < 0.75:  return "high"
        return "critical"

    def _get_feature_importances(self) -> Dict[str, float]:
        names = [
            "avg_study_hours_per_day", "avg_sleep_hours", "avg_stress_level",
            "avg_focus_level", "avg_breaks_taken", "avg_productivity_score",
            "sleep_consistency_score", "study_consistency_score", "days_analyzed",
        ]
        try:
            return {n: round(float(i), 4) for n, i in zip(names, self.model.feature_importances_)}
        except AttributeError:
            return {}


burnout_predictor = BurnoutPredictor()