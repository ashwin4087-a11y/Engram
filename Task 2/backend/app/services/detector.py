"""
detector.py — Face Detection Service
====================================

Extracts facial measurements from raw frames using MediaPipe Face Mesh.
"""

import time
from typing import Optional
import cv2
import numpy as np

# We only import mediapipe when starting the service to avoid slow module loads
import mediapipe as mp

from app.exceptions.detector import FaceDetectionError
from app.models.detection import FaceDetection, DetectionResult, BoundingBox
from app.core.settings import settings


class FaceDetectionService:
    """
    Service to manage MediaPipe Face Mesh lifecycle and perform inference.
    """

    def __init__(self, min_detection_confidence: float, max_faces: int):
        self._min_detection_confidence = min_detection_confidence
        self._max_faces = max_faces
        self._face_mesh = None

    def start(self) -> None:
        """Initialize the MediaPipe Face Mesh and Pose models."""
        if self._face_mesh is not None:
            return

        try:
            mp_face_mesh = mp.solutions.face_mesh
            self._face_mesh = mp_face_mesh.FaceMesh(
                max_num_faces=self._max_faces,
                refine_landmarks=False,
                min_detection_confidence=self._min_detection_confidence,
                min_tracking_confidence=self._min_detection_confidence,
            )
            mp_pose = mp.solutions.pose
            self._pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=self._min_detection_confidence,
                min_tracking_confidence=self._min_detection_confidence,
            )
        except Exception as e:
            raise FaceDetectionError(f"Failed to initialize MediaPipe models: {e}")

    def stop(self) -> None:
        """Release MediaPipe resources."""
        if self._face_mesh is not None:
            self._face_mesh.close()
            self._face_mesh = None
        if hasattr(self, '_pose') and self._pose is not None:
            self._pose.close()
            self._pose = None

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect face and extract measurements.
        
        Pipeline: Validate -> BGR to RGB -> MediaPipe -> Extract -> DetectionResult
        """
        start_time = time.perf_counter()

        # 1. Validate
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            raise FaceDetectionError("Invalid frame provided for detection.")

        if self._face_mesh is None:
            raise FaceDetectionError("FaceDetectionService is not started.")

        h, w, _ = frame.shape

        # 2. BGR -> RGB (MediaPipe expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 3. MediaPipe Inference
        try:
            results = self._face_mesh.process(rgb_frame)
            pose_results = self._pose.process(rgb_frame) if hasattr(self, '_pose') and self._pose else None
        except Exception as e:
            raise FaceDetectionError(f"MediaPipe processing failed: {e}")

        # 4. Extract
        if not results.multi_face_landmarks:
            processing_time = (time.perf_counter() - start_time) * 1000
            return DetectionResult(
                detected=False,
                processing_time_ms=processing_time
            )

        # Grab the first face
        face_landmarks = results.multi_face_landmarks[0]
        landmarks = face_landmarks.landmark

        # Get specific landmarks for width measurement
        left_lm = landmarks[settings.LEFT_FACE_EDGE]
        right_lm = landmarks[settings.RIGHT_FACE_EDGE]

        # Calculate bounding box from all landmarks to be robust
        x_coords = [lm.x for lm in landmarks]
        y_coords = [lm.y for lm in landmarks]
        
        norm_x_min, norm_x_max = min(x_coords), max(x_coords)
        norm_y_min, norm_y_max = min(y_coords), max(y_coords)

        bbox = BoundingBox(
            x_min=norm_x_min * w,
            y_min=norm_y_min * h,
            x_max=norm_x_max * w,
            y_max=norm_y_max * h,
            width=(norm_x_max - norm_x_min) * w,
            height=(norm_y_max - norm_y_min) * h,
        )

        # Calculate pixel coordinates for the edges to compute accurate Euclidean pixel width
        left_x, left_y = left_lm.x * w, left_lm.y * h
        right_x, right_y = right_lm.x * w, right_lm.y * h

        face_width_px = np.sqrt((right_x - left_x)**2 + (right_y - left_y)**2)
        
        # Determine center from bbox (more stable than specific central landmarks like nose)
        norm_center_x = (norm_x_min + norm_x_max) / 2.0
        norm_center_y = (norm_y_min + norm_y_max) / 2.0
        
        center_x = norm_center_x * w
        center_y = norm_center_y * h

        # MediaPipe Face Mesh doesn't provide a single confidence score per face,
        # so we default to 1.0 if it passes the min_detection_confidence threshold implicitly
        confidence = 1.0

        detection = FaceDetection(
            center_x=center_x,
            center_y=center_y,
            normalized_center_x=norm_center_x,
            normalized_center_y=norm_center_y,
            face_width_px=face_width_px,
            face_height_px=bbox.height,
            bbox=bbox,
            confidence=confidence,
        )

        processing_time = (time.perf_counter() - start_time) * 1000

        return DetectionResult(
            detected=True,
            detection=detection,
            processing_time_ms=processing_time,
            raw_landmarks=face_landmarks,
            raw_pose_landmarks=pose_results.pose_landmarks if pose_results else None,
        )


# ---------------------------------------------------------------------------
# Singleton Instance
# ---------------------------------------------------------------------------
detector_service = FaceDetectionService(
    min_detection_confidence=settings.MIN_CONFIDENCE,
    max_faces=settings.MAX_FACES,
)
