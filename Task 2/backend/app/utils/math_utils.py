"""
math_utils.py — Pure Mathematics for Estimation
===============================================

Isolates all geometrical calculations from the service layer.
Units:
- distance: meters
- angle: degrees
- face_width: meters
- focal_length: pixels
- w_px: pixels
"""

import math

def compute_distance(focal_length: float, real_width: float, pixel_width: float) -> float:
    """
    Computes distance using the pinhole camera model.
    Z = (f * W) / w_px
    """
    if pixel_width <= 0:
        raise ValueError("Pixel width must be greater than 0.")
    return (focal_length * real_width) / pixel_width


def compute_angle(face_center_x: float, image_center_x: float, focal_length: float) -> float:
    """
    Computes horizontal viewing angle in degrees.
    θ = atan((x - c_x) / f)
    """
    if focal_length <= 0:
        raise ValueError("Focal length must be greater than 0.")
        
    angle_rad = math.atan((face_center_x - image_center_x) / focal_length)
    angle_deg = math.degrees(angle_rad)
    return angle_deg
