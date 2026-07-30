"""
estimation.py — Estimation Schemas
==================================

Schemas for the distance and angle estimator.
"""

from pydantic import BaseModel, Field


class EstimateData(BaseModel):
    """
    Payload for distance and angle estimation.

    Attributes:
        distance:   Estimated distance from camera to face (metres).
        angle:      Horizontal deviation from optical axis (degrees).
        confidence: Heuristic confidence score (0-1).
        fps:        Frames-per-second of the processing pipeline.
    """

    distance: float = Field(..., description="Distance in metres")
    angle: float = Field(..., description="Horizontal angle in degrees")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence 0-1")
    fps: float = Field(..., ge=0.0, description="Processing FPS")
