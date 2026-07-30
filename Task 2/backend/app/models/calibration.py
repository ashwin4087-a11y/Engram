"""Calibration Schemas"""
from typing import Optional, Tuple
from pydantic import BaseModel, Field


class CalibrationRequest(BaseModel):
    """Body for POST /calibrate."""
    known_distance: float = Field(..., gt=0, description="Known distance in metres")
    known_face_width: float = Field(default=0.15, gt=0, description="Real face width in metres")


class CameraInfo(BaseModel):
    """Camera metadata for calibration log."""
    index: int
    resolution: Tuple[int, int]


class CalibrationData(BaseModel):
    """Rich payload for calibration response and storage."""
    camera: CameraInfo
    face_width: float = Field(..., description="Real face width used (m)")
    calibration_distance: float = Field(..., description="Distance used (m)")
    average_pixel_width: float = Field(..., description="Averaged pixel width across valid samples")
    focal_length: float = Field(..., description="Computed focal length (px)")
    sample_count: int = Field(..., description="Number of valid samples used")
    std_dev: float = Field(..., description="Standard deviation of pixel measurements")
    timestamp: str = Field(..., description="ISO 8601 timestamp of calibration")


class CalibrationStatusData(BaseModel):
    """Payload for GET /calibration status."""
    calibrated: bool = Field(..., description="Whether calibration exists")
    data: Optional[CalibrationData] = Field(default=None, description="Calibration details if calibrated")

