"""Face Detection Schemas"""
from typing import Any, Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    """2D Bounding box for a detected face."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    width: float
    height: float


class FaceDetection(BaseModel):
    """
    Detailed measurements for a single face detection.
    """
    center_x: float = Field(..., description="Face center X in pixels")
    center_y: float = Field(..., description="Face center Y in pixels")
    normalized_center_x: float = Field(..., description="Normalized center X (0-1)")
    normalized_center_y: float = Field(..., description="Normalized center Y (0-1)")
    
    face_width_px: float = Field(..., gt=0, description="Face width in pixels")
    face_height_px: float = Field(..., gt=0, description="Face height in pixels")
    
    bbox: BoundingBox = Field(..., description="Face bounding box")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class DetectionResult(BaseModel):
    """
    Rich result object returned by the FaceDetectionService.
    """
    detected: bool = Field(..., description="True if a face was found")
    detection: Optional[FaceDetection] = Field(default=None, description="Detection details if found")
    processing_time_ms: float = Field(..., description="Inference time in milliseconds")
    # Raw MediaPipe NormalizedLandmarkList — NOT serialised to JSON, used by ML pipeline only.
    raw_landmarks: Optional[Any] = Field(default=None, exclude=True, description="Raw MediaPipe landmarks (not serialised)")
    raw_pose_landmarks: Optional[Any] = Field(default=None, exclude=True, description="Raw MediaPipe pose landmarks (not serialised)")
