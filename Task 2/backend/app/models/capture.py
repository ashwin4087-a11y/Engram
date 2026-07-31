from pydantic import BaseModel, Field
from typing import Optional


class CaptureMetadata(BaseModel):
    timestamp: str
    distance: Optional[str] = None
    angle: Optional[str] = None
    confidence: Optional[str] = None
    fps: Optional[str] = None


class CaptureResponse(BaseModel):
    success: bool = True
    capture_id: str = Field(..., description="Unique capture identifier")
    path: str = Field(..., description="Filesystem path to stored image")
    metadata: CaptureMetadata
