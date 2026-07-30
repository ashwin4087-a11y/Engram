"""
drawing.py — OpenCV Drawing Utilities
=====================================

Modular drawing functions to overlay metrics, bounding boxes, 
and system information onto frames. Independent of CV detection logic.
"""

from typing import Optional, Dict, Any
import cv2
import numpy as np

from app.models.detection import FaceDetection
from app.core.settings import settings


def draw_bbox(frame: np.ndarray, detection: FaceDetection, color=(0, 255, 0)) -> None:
    """Draws the bounding box of the detected face."""
    x_min, y_min = int(detection.bbox.x_min), int(detection.bbox.y_min)
    x_max, y_max = int(detection.bbox.x_max), int(detection.bbox.y_max)
    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)


def draw_center(frame: np.ndarray, detection: FaceDetection, color=(0, 0, 255)) -> None:
    """Draws a point at the center of the face."""
    cx, cy = int(detection.center_x), int(detection.center_y)
    cv2.circle(frame, (cx, cy), radius=4, color=color, thickness=-1)


def draw_width_line(frame: np.ndarray, detection: FaceDetection, color=(255, 0, 0)) -> None:
    """Draws a horizontal line representing the face width."""
    cx, cy = int(detection.center_x), int(detection.center_y)
    half_width = int(detection.face_width_px / 2)
    cv2.line(
        frame,
        (cx - half_width, cy),
        (cx + half_width, cy),
        color,
        thickness=2
    )


def draw_text_line(frame: np.ndarray, text: str, x: int, y: int, color=(0, 255, 0), scale=0.6) -> None:
    """Helper to draw a single line of text."""
    cv2.putText(
        frame, 
        text, 
        (x, y), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        scale, 
        color, 
        2
    )


def draw_measurements(frame: np.ndarray, detection: FaceDetection, distance: float = None, angle: float = None) -> None:
    """Draws real-time measurements related to the face."""
    x_min, y_min = int(detection.bbox.x_min), int(detection.bbox.y_min)
    
    lines = [
        f"Width: {detection.face_width_px:.1f} px",
        f"Conf: {detection.confidence * 100:.1f}%"
    ]
    
    if distance is not None:
        lines.append(f"Dist: {distance:.2f} m")
    else:
        lines.append("Dist: --")
        
    if angle is not None:
        lines.append(f"Angle: {angle:.1f} deg")
    else:
        lines.append("Angle: --")
        
    for i, line in enumerate(lines):
        draw_text_line(frame, line, x_min, y_min - 10 - (len(lines) - 1 - i) * 20, scale=0.5)


def draw_system_info(frame: np.ndarray, metrics: Dict[str, Any], is_calibrated: bool) -> None:
    """Draws system-level information (FPS, calibration status) in the corner."""
    margin = 20
    y_offset = 30
    
    # Draw Calibration Status
    cal_text = "Calibration: READY" if is_calibrated else "Calibration: NOT CALIBRATED"
    cal_color = (0, 255, 0) if is_calibrated else (0, 0, 255)
    draw_text_line(frame, cal_text, margin, y_offset, color=cal_color)
    
    # Draw metrics
    y_offset += 25
    if "fps" in metrics:
        draw_text_line(frame, f"FPS: {metrics['fps']:.1f}", margin, y_offset, color=(255, 255, 0))
    
    y_offset += 20
    if "inference_ms" in metrics:
        draw_text_line(frame, f"Inference: {metrics['inference_ms']:.1f} ms", margin, y_offset, color=(255, 255, 0), scale=0.5)


def apply_overlays(
    frame: np.ndarray,
    mode: str,
    detection: Optional[FaceDetection],
    metrics: Dict[str, Any],
    is_calibrated: bool,
    distance: float = None,
    angle: float = None
) -> np.ndarray:
    """
    Applies the requested visualization layers based on the selected mode.
    
    Modes:
        - full: everything
        - bbox: just bbox and center
        - measurements: text only
        - none/raw: no overlays
    """
    if mode == "none" or mode == "raw":
        return frame

    annotated = frame.copy()
    
    # Global Info
    draw_system_info(annotated, metrics, is_calibrated)

    if detection:
        if mode in ("full", "bbox"):
            draw_bbox(annotated, detection)
            draw_center(annotated, detection)
            
        if mode == "full":
            draw_width_line(annotated, detection)
            
        if mode in ("full", "measurements"):
            draw_measurements(annotated, detection, distance, angle)

    return annotated
