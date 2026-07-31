"""Tracker Models"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any
import numpy as np

from app.models.detection import FaceDetection
from app.models.estimation import EstimateData


class TrackerStatus(str, Enum):
    """Possible states of the tracking engine."""
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    NO_CAMERA = "NO_CAMERA"
    NO_FACE = "NO_FACE"
    NOT_CALIBRATED = "NOT_CALIBRATED"
    ERROR = "ERROR"


@dataclass
class TrackerState:
    """
    Thread-safe snapshot of the current system state.
    Used by API endpoints and streams to avoid blocking the main loop.
    """
    status: TrackerStatus
    timestamp: str
    fps: float
    frame: Optional[np.ndarray] = None
    detection: Optional[FaceDetection] = None
    estimate: Optional[EstimateData] = None
    error_message: Optional[str] = None
    # ML posture fields (populated after ML pipeline runs)
    posture: Optional[str] = None
    posture_confidence: Optional[float] = None
    posture_recommendations: Optional[list] = None
    posture_source: Optional[str] = None
    model_type: Optional[str] = None
    model_version: Optional[str] = None
    latency_ms: Optional[float] = None


from pydantic import BaseModel, Field
from typing import List

class TrackerResponse(BaseModel):
    """API-friendly serialization of the TrackerState (excluding the raw numpy frame)."""
    status: TrackerStatus
    timestamp: str
    fps: float
    detection: Optional[FaceDetection] = None
    estimate: Optional[EstimateData] = None
    error_message: Optional[str] = None
    # ML posture output (None when no model artefact exists or no face detected)
    posture: Optional[str] = Field(default=None, description="Predicted posture class")
    posture_confidence: Optional[float] = Field(default=None, description="Confidence [0,1]")
    posture_recommendations: Optional[List[str]] = Field(default=None, description="Actionable advice")
    posture_source: Optional[str] = Field(default=None, description="'model' | 'heuristic'")
    model_type: Optional[str] = Field(default=None, description="Type of underlying model (e.g. xgboost)")
    model_version: Optional[str] = Field(default=None, description="Model artefact version")
    latency_ms: Optional[float] = Field(default=None, description="Inference latency in ms")

    @classmethod
    def from_state(cls, state: TrackerState) -> "TrackerResponse":
        return cls(
            status=state.status,
            timestamp=state.timestamp,
            fps=state.fps,
            detection=state.detection,
            estimate=state.estimate,
            error_message=state.error_message,
            posture=state.posture,
            posture_confidence=state.posture_confidence,
            posture_recommendations=state.posture_recommendations,
            posture_source=state.posture_source,
            model_type=state.model_type,
            model_version=state.model_version,
            latency_ms=state.latency_ms,
        )
