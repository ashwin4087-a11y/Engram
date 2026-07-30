"""
camera.py — Camera Service
===========================

Manages the lifecycle of the webcam hardware.
Ensures thread-safe access and proper startup/shutdown.
"""

import time
import threading
from typing import Optional
import cv2
import numpy as np

from app.exceptions.camera import CameraError
from app.models.camera import FrameData
from app.core.settings import settings


class CameraService:
    """
    Thread-safe service to manage webcam lifecycle and frame capture.
    Hardware initialization is deferred to start(), not __init__.
    """

    def __init__(self, camera_index: int, width: int, height: int):
        self._camera_index = camera_index
        self._width = width
        self._height = height
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Initialize the camera hardware."""
        with self._lock:
            if self._cap is not None:
                return  # Already started

            self._cap = cv2.VideoCapture(self._camera_index)
            if not self._cap.isOpened():
                self._cap = None
                raise CameraError(f"Failed to open camera at index {self._camera_index}")

            # Request specific resolution (OpenCV treats this as a hint)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

            # Warmup read to ensure hardware is fully ready
            success, _ = self._cap.read()
            if not success:
                self._cap.release()
                self._cap = None
                raise CameraError("Camera opened, but failed to read initial frame.")

    def stop(self) -> None:
        """Release the camera hardware safely. Safe to call multiple times."""
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None

    def get_frame(self) -> FrameData:
        """
        Capture the latest frame from the webcam.
        
        Returns:
            FrameData containing the image array and timestamp.
            
        Raises:
            CameraError: If camera is not started or read fails.
        """
        with self._lock:
            if self._cap is None:
                raise CameraError("Cannot capture frame: Camera is not started.")

            success, frame = self._cap.read()
            if not success:
                raise CameraError("Failed to capture frame from camera.")
            
            timestamp = time.time()
            
            return FrameData(frame=frame, timestamp=timestamp)


# ---------------------------------------------------------------------------
# Singleton Instance
# ---------------------------------------------------------------------------
# Created once for the application lifetime.
camera_service = CameraService(
    camera_index=settings.CAMERA_INDEX,
    width=settings.CAMERA_WIDTH,
    height=settings.CAMERA_HEIGHT,
)
