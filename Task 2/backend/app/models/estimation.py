"""Estimation Schemas"""
from pydantic import BaseModel, Field

class EstimateData(BaseModel):
    """Rich payload containing the mathematical estimates."""
    distance: float = Field(..., description="Distance from camera in metres")
    angle: float = Field(..., description="Horizontal viewing angle in degrees")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Estimation confidence (0-1)")
    face_width_px: float = Field(..., description="Pixel width used for estimation")
    focal_length: float = Field(..., description="Focal length used for estimation")
    fps: float = Field(..., ge=0.0, description="Processing FPS")
    timestamp: str = Field(..., description="ISO 8601 timestamp of estimation")

