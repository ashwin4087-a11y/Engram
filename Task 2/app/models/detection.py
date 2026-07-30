"""
detection.py — Face Detection Schemas
=====================================

Schemas for the face detection service.
"""

from pydantic import BaseModel, Field


class FaceDetection(BaseModel):
    """
    Result of a single face detection.

    Attributes:
        center_x:      X-coordinate of the face center (pixels).
        center_y:      Y-coordinate of the face center (pixels).
        face_width_px: Width of the face measured between landmarks (pixels).
        confidence:    MediaPipe detection confidence (0-1).
    """

    center_x: float = Field(..., description="Face center X in pixels")
    center_y: float = Field(..., description="Face center Y in pixels")
    face_width_px: float = Field(..., gt=0, description="Face width in pixels")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
