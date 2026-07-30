"""
calibration.py — Calibration Schemas
====================================

Schemas for the camera calibration service.
"""

from typing import List

from pydantic import BaseModel, Field


class CalibrationSample(BaseModel):
    """A single calibration measurement."""
    distance: float = Field(..., gt=0, description="Known distance in metres")
    face_width_px: float = Field(..., gt=0, description="Detected face width px")
    focal_length: float = Field(..., gt=0, description="Computed focal length px")


class CalibrationRequest(BaseModel):
    """Body for POST /calibrate."""
    known_distance: float = Field(..., gt=0, description="Known distance in metres")
    known_face_width: float = Field(
        default=0.15, gt=0, description="Real face width in metres"
    )


class CalibrationData(BaseModel):
    """Payload for calibration response."""
    focal_length: float = Field(..., description="Averaged focal length px")
    face_width: float = Field(..., description="Face width constant m")
    num_samples: int = Field(..., ge=1, description="Number of samples")


class CalibrationStatusData(CalibrationData):
    """Payload for calibration status including samples."""
    samples: List[CalibrationSample] = Field(default_factory=list)
