"""
predict.py — Posture Classifier Inference
==========================================

Loads the trained XGBoost model once at import time (or on first call) and
exposes a single function:

    result = predict_posture(feature_vector)

Design decisions
----------------
* **XGBoost** was chosen over Random Forest / LightGBM / MLP because:
  - Inference on a 12-feature vector is <1 ms (much faster than MLP warm-up).
  - Handles missing / noisy features gracefully without imputation.
  - Does NOT require GPU for real-time single-sample inference.
  - Native probability output via predict_proba — no sigmoid calibration needed.
  - Serialises to a single binary file (<1 MB); fits in the 300 MB budget.

* The model file is loaded lazily the first time predict_posture() is called,
  so the module is safe to import before the model artefact exists (training
  can happen later).

* If the model is absent, the classifier falls back to a heuristic rule-based
  predictor so the API is never broken.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

import numpy as np

from app.ml.models.posture_labels import (
    POSTURE_LABELS,
    POSTURE_RECOMMENDATIONS,
    PostureClass,
    NUM_CLASSES,
)
from app.ml.preprocessing.feature_extractor import NUM_FEATURES

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model artefact path
# ---------------------------------------------------------------------------
_MODEL_DIR  = Path(__file__).parent.parent / "models" / "artefacts"
_MODEL_PATH = _MODEL_DIR / "posture_classifier.ubj"   # XGBoost universal binary
_SCALER_PATH = _MODEL_DIR / "feature_scaler.npz"     # StandardScaler params

# ---------------------------------------------------------------------------
# Inference result dataclass (lightweight, no Pydantic at inference time)
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field


import json

@dataclass
class PosturePrediction:
    """Result of a single posture inference pass."""
    posture: str                    # e.g. "LEANING_FORWARD"
    posture_id: int                 # PostureClass integer
    confidence: float               # probability of predicted class [0,1]
    probabilities: dict             # {class_name: probability}
    recommendations: list           # actionable advice strings
    latency_ms: float               # wall-clock inference time
    source: str = "model"           # "model" | "heuristic" | "fallback"
    model_type: str = "xgboost"
    model_version: str = "unknown"


# ---------------------------------------------------------------------------
# Heuristic fallback (no trained model required)
# ---------------------------------------------------------------------------

def _heuristic_predict(features: np.ndarray) -> PosturePrediction:
    """
    Rule-based posture classification used when no trained model is available.
    """
    yaw   = features[0]
    pitch = features[1]
    roll  = features[2]
    torso = features[5]
    face_size = features[7]

    # Priority order matters (first matching rule wins)
    if abs(roll) > 12.0:
        cls = PostureClass.HEAD_TILT_LEFT if roll > 0 else PostureClass.HEAD_TILT_RIGHT
        conf = min(0.55 + abs(roll) / 90.0, 0.90)
    elif pitch > 10.0:
        cls  = PostureClass.LOOKING_UP
        conf = min(0.55 + pitch / 45.0, 0.90)
    elif pitch < -10.0:
        cls  = PostureClass.LOOKING_DOWN
        conf = min(0.55 + abs(pitch) / 45.0, 0.90)
    elif torso > 10.0 or face_size > 0.25:
        cls  = PostureClass.LEANING_FORWARD
        conf = min(0.55 + max(torso/45.0, face_size), 0.90)
    elif torso < -5.0 or face_size < 0.05:
        cls  = PostureClass.LEANING_BACKWARD
        conf = 0.60
    elif abs(yaw) > 20.0:
        cls = PostureClass.HEAD_TILT_LEFT if yaw > 0 else PostureClass.HEAD_TILT_RIGHT
        conf = min(0.50 + abs(yaw) / 90.0, 0.85)
    else:
        cls  = PostureClass.GOOD_POSTURE
        conf = 0.70

    probs = {POSTURE_LABELS[i]: 0.0 for i in range(NUM_CLASSES)}
    probs[POSTURE_LABELS[int(cls)]] = conf

    return PosturePrediction(
        posture=POSTURE_LABELS[int(cls)],
        posture_id=int(cls),
        confidence=conf,
        probabilities=probs,
        recommendations=POSTURE_RECOMMENDATIONS[int(cls)],
        latency_ms=0.0,
        source="heuristic",
        model_type="heuristic",
        model_version="v1.0.0-heuristic",
    )


# ---------------------------------------------------------------------------
# XGBoost-based classifier
# ---------------------------------------------------------------------------

class _PostureClassifier:
    """Singleton wrapper around the XGBoost booster."""

    def __init__(self) -> None:
        self._booster = None
        self._scaler_mean: Optional[np.ndarray] = None
        self._scaler_std:  Optional[np.ndarray] = None
        self._loaded = False
        self._model_version = "unknown"

    # ------------------------------------------------------------------
    def _load(self) -> bool:
        """Attempt to load the model artefact. Returns True on success."""
        if self._loaded:
            return self._booster is not None

        try:
            import xgboost as xgb  # type: ignore

            if not _MODEL_PATH.exists():
                log.warning(
                    "Posture model artefact not found at %s — "
                    "using heuristic fallback. Run training to create it.",
                    _MODEL_PATH,
                )
                self._loaded = True   # don't retry on every frame
                return False

            self._booster = xgb.Booster()
            self._booster.load_model(str(_MODEL_PATH))
            log.info("Loaded posture classifier from %s", _MODEL_PATH)

            # Load scaler params if they exist
            if _SCALER_PATH.exists():
                scaler_data = np.load(str(_SCALER_PATH))
                self._scaler_mean = scaler_data["mean"]
                self._scaler_std  = scaler_data["std"]
                log.info("Loaded feature scaler from %s", _SCALER_PATH)

            meta_path = _MODEL_DIR / "metadata.json"
            if meta_path.exists():
                with open(meta_path, "r") as fh:
                    meta = json.load(fh)
                    self._model_version = meta.get("model_version", "unknown")
                    log.info("Loaded model metadata: %s", self._model_version)

            self._loaded = True
            return True

        except ImportError:
            log.warning("xgboost not installed — using heuristic fallback.")
            self._loaded = True
            return False
        except Exception as exc:
            log.error("Failed to load posture classifier: %s", exc)
            self._loaded = True
            return False

    # ------------------------------------------------------------------
    def _scale(self, features: np.ndarray) -> np.ndarray:
        """Apply StandardScaler normalisation if scaler params are available."""
        if self._scaler_mean is not None and self._scaler_std is not None:
            return (features - self._scaler_mean) / (self._scaler_std + 1e-8)
        return features

    # ------------------------------------------------------------------
    def predict(self, features: np.ndarray) -> PosturePrediction:
        """
        Run inference on a single feature vector.

        Parameters
        ----------
        features : np.ndarray, shape (NUM_FEATURES,)

        Returns
        -------
        PosturePrediction
        """
        t0 = time.perf_counter()

        if features is None or len(features) != NUM_FEATURES:
            log.debug("Invalid feature vector; returning GOOD_POSTURE fallback.")
            return _heuristic_predict(np.zeros(NUM_FEATURES, dtype=np.float32))

        available = self._load()
        if not available:
            result = _heuristic_predict(features)
            result.latency_ms = (time.perf_counter() - t0) * 1000
            return result

        try:
            import xgboost as xgb  # type: ignore

            scaled = self._scale(features).reshape(1, -1)
            dmatrix = xgb.DMatrix(scaled)

            # predict_proba equivalent: returns shape (1, NUM_CLASSES)
            raw_probs = self._booster.predict(dmatrix)
            if raw_probs.ndim == 1:
                # Binary output — shouldn't happen with multi:softprob
                probs = raw_probs
            else:
                probs = raw_probs[0]

            predicted_idx = int(np.argmax(probs))
            confidence    = float(probs[predicted_idx])

            prob_dict = {
                POSTURE_LABELS[i]: float(probs[i])
                for i in range(min(len(probs), NUM_CLASSES))
            }

            latency_ms = (time.perf_counter() - t0) * 1000

            return PosturePrediction(
                posture=POSTURE_LABELS[predicted_idx],
                posture_id=predicted_idx,
                confidence=confidence,
                probabilities=prob_dict,
                recommendations=POSTURE_RECOMMENDATIONS[predicted_idx],
                latency_ms=latency_ms,
                source="model",
                model_type="xgboost",
                model_version=self._model_version,
            )

        except Exception as exc:
            log.error("XGBoost inference error: %s — falling back to heuristic.", exc)
            result = _heuristic_predict(features)
            result.latency_ms = (time.perf_counter() - t0) * 1000
            return result


# ---------------------------------------------------------------------------
# Module-level singleton (loaded lazily)
# ---------------------------------------------------------------------------
_classifier = _PostureClassifier()


def predict_posture(features: np.ndarray) -> PosturePrediction:
    """
    Public inference function.

    Parameters
    ----------
    features : np.ndarray, shape (12,)
        Feature vector produced by PostureFeatureExtractor.extract().

    Returns
    -------
    PosturePrediction
        Contains posture label, confidence, per-class probabilities,
        actionable recommendations, and inference latency.
    """
    return _classifier.predict(features)


def get_model_status() -> dict:
    """Return a status dict indicating whether the model is loaded."""
    return {
        "model_loaded": _classifier._booster is not None,
        "model_path": str(_MODEL_PATH),
        "scaler_loaded": _classifier._scaler_mean is not None,
        "source": "model" if _classifier._booster is not None else "heuristic",
    }
