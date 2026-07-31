"""
posture_labels.py — Canonical posture class definitions
========================================================

Single source-of-truth for label names, indices, and human-readable
descriptions used by both the training pipeline and the inference API.
"""

from enum import IntEnum
from typing import Dict, List


class PostureClass(IntEnum):
    """Seven posture categories predicted by the classification model."""
    GOOD_POSTURE      = 0
    LEANING_FORWARD   = 1
    LEANING_BACKWARD  = 2
    LOOKING_DOWN      = 3
    LOOKING_UP        = 4
    HEAD_TILT_LEFT    = 5
    HEAD_TILT_RIGHT   = 6


# Human-readable label strings (used in API responses)
POSTURE_LABELS: Dict[int, str] = {
    PostureClass.GOOD_POSTURE:     "GOOD_POSTURE",
    PostureClass.LEANING_FORWARD:  "LEANING_FORWARD",
    PostureClass.LEANING_BACKWARD: "LEANING_BACKWARD",
    PostureClass.LOOKING_DOWN:     "LOOKING_DOWN",
    PostureClass.LOOKING_UP:       "LOOKING_UP",
    PostureClass.HEAD_TILT_LEFT:   "HEAD_TILT_LEFT",
    PostureClass.HEAD_TILT_RIGHT:  "HEAD_TILT_RIGHT",
}

# Actionable advice surfaced in the API response
POSTURE_RECOMMENDATIONS: Dict[int, List[str]] = {
    PostureClass.GOOD_POSTURE: [
        "Great posture — keep it up!",
    ],
    PostureClass.LEANING_FORWARD: [
        "Move your chair closer or increase font size.",
        "Adjust your monitor to arm's-length distance.",
        "Ensure your screen is at eye level.",
    ],
    PostureClass.LEANING_BACKWARD: [
        "Sit closer to the desk and straighten your back.",
        "Use lumbar support to keep your spine neutral.",
    ],
    PostureClass.LOOKING_DOWN: [
        "Raise your monitor so the top edge is at eye level.",
        "Consider a monitor stand or adjustable arm.",
    ],
    PostureClass.LOOKING_UP: [
        "Lower your monitor so the top edge is at or below eye level.",
    ],
    PostureClass.HEAD_TILT_LEFT: [
        "Level your head — your left shoulder may be raised.",
        "Ensure your keyboard is centred in front of you.",
    ],
    PostureClass.HEAD_TILT_RIGHT: [
        "Level your head — your right shoulder may be raised.",
        "Check that your mouse is within comfortable reach.",
    ],
}

# Ordered list of class names (used as feature-encoder reference order)
CLASS_NAMES: List[str] = [POSTURE_LABELS[i] for i in sorted(POSTURE_LABELS)]

NUM_CLASSES: int = len(PostureClass)
