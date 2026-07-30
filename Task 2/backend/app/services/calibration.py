"""
calibration.py — Camera Calibration Service
===========================================

Performs a robust calibration session by capturing multiple frames,
filtering outliers, and averaging results to compute focal length.
"""

import time
import numpy as np
from datetime import datetime, timezone

from app.services.camera import CameraService
from app.services.detector import FaceDetectionService
from app.services.calibration_storage import CalibrationStorage
from app.models.calibration import CalibrationData, CameraInfo
from app.exceptions.calibration import CalibrationError


class CalibrationService:
    """
    Manages the camera calibration session.
    Computes focal length by capturing a burst of frames,
    rejecting outliers, and averaging the results.
    """
    
    def __init__(
        self, 
        camera: CameraService, 
        detector: FaceDetectionService,
        storage: CalibrationStorage
    ):
        self._camera = camera
        self._detector = detector
        self._storage = storage
        self._target_samples = 30
        self._min_valid_samples = 15
        # We reject samples outside of 1.5 * MAD (Median Absolute Deviation)
        self._mad_multiplier = 1.5

    def calibrate(self, known_distance: float, known_face_width: float) -> CalibrationData:
        """
        Runs a full calibration session.
        
        Args:
            known_distance: Distance from camera to face in metres.
            known_face_width: Real-world face width in metres.
            
        Returns:
            CalibrationData
            
        Raises:
            CalibrationError: If calibration fails due to bad detection or not enough samples.
        """
        pixel_widths = []
        
        # 1. Capture Burst
        for _ in range(self._target_samples):
            try:
                frame_data = self._camera.get_frame()
                result = self._detector.detect(frame_data.frame)
                
                if result.detected and result.detection:
                    pixel_widths.append(result.detection.face_width_px)
            except Exception:
                pass # Ignore occasional capture/detection errors in burst
            
            # Tiny sleep to ensure we don't just capture 30 exactly identical frames instantly
            time.sleep(0.03)
            
        # 2. Validate
        if len(pixel_widths) < self._min_valid_samples:
            raise CalibrationError(
                f"Calibration failed: Found {len(pixel_widths)} valid frames, "
                f"minimum is {self._min_valid_samples}. Please stay still and ensure good lighting."
            )
            
        # 3. Reject Outliers using Median Absolute Deviation (MAD)
        pixel_widths = np.array(pixel_widths)
        median = np.median(pixel_widths)
        mad = np.median(np.abs(pixel_widths - median))
        
        # If MAD is 0 (extremely stable or stuck), we use a small fallback threshold
        threshold = max(self._mad_multiplier * mad, 2.0) 
        
        valid_mask = np.abs(pixel_widths - median) <= threshold
        valid_widths = pixel_widths[valid_mask]
        
        if len(valid_widths) < self._min_valid_samples:
             raise CalibrationError("Calibration failed: Too much movement or instability (too many outliers).")
             
        # 4. Compute Metrics
        average_px = float(np.mean(valid_widths))
        std_dev = float(np.std(valid_widths))
        
        # focal_length = (pixel_width * distance) / real_width
        focal_length = (average_px * known_distance) / known_face_width
        
        # 5. Build Rich Metadata
        # Retrieve camera info safely
        try:
            cam_index = self._camera._camera_index
            cam_res = (self._camera._width, self._camera._height)
        except AttributeError:
            cam_index = 0
            cam_res = (640, 480)
            
        data = CalibrationData(
            camera=CameraInfo(index=cam_index, resolution=cam_res),
            face_width=known_face_width,
            calibration_distance=known_distance,
            average_pixel_width=average_px,
            focal_length=focal_length,
            sample_count=len(valid_widths),
            std_dev=std_dev,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # 6. Save
        self._storage.save(data)
        
        return data

    def get_calibration(self) -> CalibrationData:
        """Retrieves current calibration or raises an error if none exists."""
        data = self._storage.load()
        if not data:
            raise CalibrationError("No calibration data exists.")
        return data
        
    def reset(self) -> None:
        """Deletes current calibration data."""
        self._storage.delete()
