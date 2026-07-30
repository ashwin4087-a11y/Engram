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


from pydantic import BaseModel, Field

class TrackerResponse(BaseModel):
    """API-friendly serialization of the TrackerState (excluding the raw numpy frame)."""
    status: TrackerStatus
    timestamp: str
    fps: float
    detection: Optional[FaceDetection] = None
    estimate: Optional[EstimateData] = None
    error_message: Optional[str] = None

    @classmethod
    def from_state(cls, state: TrackerState) -> "TrackerResponse":
        return cls(
            status=state.status,
            timestamp=state.timestamp,
            fps=state.fps,
            detection=state.detection,
            estimate=state.estimate,
            error_message=state.error_message
        )
