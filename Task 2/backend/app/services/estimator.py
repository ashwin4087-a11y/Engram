"""
estimator.py — Pure Estimation Service
======================================

Stateless service that computes physical distance and angle
using purely mathematical models. Completely decoupled from
hardware or computer vision dependencies.
"""

from datetime import datetime, timezone
from typing import Tuple

from app.models.detection import FaceDetection
from app.models.calibration import CalibrationData
from app.models.estimation import EstimateData
from app.exceptions.estimation import EstimationError
from app.utils.math_utils import compute_distance, compute_angle


class EstimatorService:
    """
    Stateless estimator. Calculates spatial position based on 
    calibrated focal length and detected face pixel measurements.
    """

    @staticmethod
    def estimate(
        detection: FaceDetection,
        calibration: CalibrationData,
        image_resolution: Tuple[int, int]
    ) -> EstimateData:
        """
        Computes the distance and angle of a detected face.
        
        Args:
            detection: The output from the FaceDetectionService.
            calibration: The current calibration data.
            image_resolution: (width, height) of the source image.
            
        Returns:
            EstimateData containing unrounded distance and angle.
            
        Raises:
            EstimationError: If inputs are invalid or math fails.
        """
        
        # 1. Validation
        if not detection:
            raise EstimationError("Cannot estimate without a valid detection.")
            
        if not calibration:
            raise EstimationError("Cannot estimate without calibration data.")
            
        w_px = detection.face_width_px
        f = calibration.focal_length
        real_width = calibration.face_width
        img_w, _ = image_resolution
        
        if w_px <= 0:
            raise EstimationError(f"Invalid face width in pixels: {w_px}")
        if f <= 0:
            raise EstimationError(f"Invalid focal length: {f}")
        if img_w <= 0:
            raise EstimationError(f"Invalid image width: {img_w}")
            
        image_center_x = img_w / 2.0
        
        # 2. Math Calculations
        try:
            distance = compute_distance(
                focal_length=f, 
                real_width=real_width, 
                pixel_width=w_px
            )
            
            angle = compute_angle(
                face_center_x=detection.center_x, 
                image_center_x=image_center_x, 
                focal_length=f
            )
        except ValueError as e:
            raise EstimationError(f"Mathematical error during estimation: {e}")

        # 3. Calculate Confidence
        # Higher confidence for faces that are larger (closer) and have high detector confidence.
        # We also penalize if the calibration std_dev was very high.
        base_conf = detection.confidence
        
        # Size factor (maxes out around 200px width)
        size_factor = min(w_px / 200.0, 1.0)
        
        # Calibration quality factor (penalize if std_dev > 10px)
        cal_penalty = max(0, (calibration.std_dev - 10) / 100.0)
        
        calculated_confidence = max(0.0, min(1.0, (base_conf * 0.7 + size_factor * 0.3) - cal_penalty))

        # 4. Build Result
        return EstimateData(
            distance=distance,
            angle=angle,
            confidence=calculated_confidence,
            face_width_px=w_px,
            focal_length=f,
            fps=0.0, # Will be set by the orchestrator/tracker
            timestamp=datetime.now(timezone.utc).isoformat()
        )
