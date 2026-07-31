"""
feature_extractor.py — MediaPipe → Feature Vector
==================================================

Converts raw MediaPipe Face Mesh (and optional Pose) landmarks into a
normalised, fixed-length numerical feature vector consumed by the posture
classifier.

Design goals
------------
* Pure NumPy — no ML framework dependency.
* Deterministic: same landmark input → same vector every time.
* <1 ms execution on a modern CPU (benchmarked on 478-landmark face mesh).

Feature vector layout (FEATURE_NAMES mirrors index order)
----------------------------------------------------------
 0  head_yaw          (degrees) — left/right head rotation
 1  head_pitch        (degrees) — up/down head tilt
 2  head_roll         (degrees) — ear-to-shoulder tilt
 3  eye_level_ratio   — (left_eye_y + right_eye_y) / 2 normalised 0-1
 4  eye_horizontal_diff — asymmetry between left and right eye heights
 5  nose_eye_dist     — vertical dist nose-tip to eye midpoint (normalised)
 6  face_aspect_ratio — face_width / face_height
 7  face_size_ratio   — bbox_area / frame_area  (proxy for forward lean)
 8  chin_forehead_ratio — chin_y relative to forehead_y (pitch proxy)
 9  left_eye_aspect   — left eye openness
10  right_eye_aspect  — right eye openness
11  mouth_openness    — mouth height / width ratio
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# MediaPipe Face Mesh landmark indices (478-point model)
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
# ---------------------------------------------------------------------------

# Outer face contour (cheekbone edges)
_LEFT_FACE_EDGE  = 234   # same as settings.LEFT_FACE_EDGE
_RIGHT_FACE_EDGE = 454   # same as settings.RIGHT_FACE_EDGE

# Eye landmarks (6-point EAR model per eye)
_LEFT_EYE_TOP    = 386
_LEFT_EYE_BOTTOM = 374
_LEFT_EYE_LEFT   = 263
_LEFT_EYE_RIGHT  = 362

_RIGHT_EYE_TOP    = 159
_RIGHT_EYE_BOTTOM = 145
_RIGHT_EYE_LEFT   = 133
_RIGHT_EYE_RIGHT  = 33

# Face cardinal points
_NOSE_TIP       = 4
_CHIN           = 152
_FOREHEAD       = 10
_LEFT_MOUTH     = 61
_RIGHT_MOUTH    = 291
_TOP_MOUTH      = 13
_BOTTOM_MOUTH   = 14

# Head pose reference points (used with solvePnP-style heuristics)
_LEFT_EAR       = 234
_RIGHT_EAR      = 454

# ---------------------------------------------------------------------------
# Feature names (index-matched to the output vector)
# ---------------------------------------------------------------------------
FEATURE_NAMES: List[str] = [
    "head_yaw",
    "head_pitch",
    "head_roll",
    "shoulder_angle",
    "neck_angle",
    "torso_inclination",
    "spine_orientation",
    "face_size_ratio",
    "inter_eye_dist",
    "eye_level_ratio",
    "eye_horizontal_diff",
    "nose_eye_dist",
    "face_aspect_ratio",
    "chin_forehead_ratio",
    "left_eye_aspect",
    "right_eye_aspect",
    "mouth_openness",
]

NUM_FEATURES: int = len(FEATURE_NAMES)


# ---------------------------------------------------------------------------
# Helper geometry functions
# ---------------------------------------------------------------------------

def _lm(landmarks, idx: int) -> np.ndarray:
    """Return (x, y, z) as a NumPy array for landmark index *idx*."""
    lm = landmarks[idx]
    return np.array([lm.x, lm.y, lm.z], dtype=np.float32)


def _dist2d(a: np.ndarray, b: np.ndarray) -> float:
    """Euclidean distance in the XY plane."""
    return float(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


def _eye_aspect_ratio(top: np.ndarray, bottom: np.ndarray,
                      left: np.ndarray, right: np.ndarray) -> float:
    """Eye Aspect Ratio (EAR) — Soukupová & Čech 2016."""
    vertical   = _dist2d(top, bottom)
    horizontal = _dist2d(left, right)
    if horizontal < 1e-6:
        return 0.0
    return vertical / horizontal


def _angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    """Angle in degrees between two 3-D vectors."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    cos_theta = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(math.degrees(math.acos(cos_theta)))


# ---------------------------------------------------------------------------
# Head-pose estimation from face-mesh landmarks (lightweight, no PnP)
# ---------------------------------------------------------------------------

def _estimate_head_pose(landmarks) -> Tuple[float, float, float]:
    """
    Estimate (yaw, pitch, roll) in degrees from Face Mesh landmarks.

    Strategy
    --------
    All coordinates are in normalised image space (x, y ∈ [0,1]; z is depth
    relative to nose, negative = towards camera).

    Yaw   — angle between the ear-to-ear vector and the image horizontal axis.
             Left-ear closer to camera (positive z) → head turned left.
    Pitch — vertical displacement of nose relative to the eye midpoint,
             normalised by face height.  Positive = looking up.
    Roll  — angle of the eye-to-eye vector with respect to the horizontal.
             Positive = right ear lower (head tilts left).
    """
    left_ear  = _lm(landmarks, _LEFT_FACE_EDGE)
    right_ear = _lm(landmarks, _RIGHT_FACE_EDGE)
    nose      = _lm(landmarks, _NOSE_TIP)
    chin      = _lm(landmarks, _CHIN)
    forehead  = _lm(landmarks, _FOREHEAD)
    l_eye_r   = _lm(landmarks, _LEFT_EYE_RIGHT)   # inner left eye corner
    r_eye_l   = _lm(landmarks, _RIGHT_EYE_LEFT)   # inner right eye corner

    eye_mid = (l_eye_r + r_eye_l) / 2.0
    face_height = _dist2d(forehead, chin)

    # --- Yaw ---
    # z difference between ears: if left ear is further from camera (more
    # negative z in MediaPipe space) the person is turned right and vice-versa.
    yaw = float((right_ear[2] - left_ear[2]) * 90.0)   # scale to ~[-90,90]

    # --- Pitch ---
    # Positive = nose above eye midpoint (looking up).
    vert_diff = eye_mid[1] - nose[1]   # image y: 0=top, 1=bottom
    face_h    = max(face_height, 1e-6)
    pitch     = float(math.degrees(math.atan2(vert_diff, face_h / 2.0)))

    # --- Roll ---
    dx = r_eye_l[0] - l_eye_r[0]
    dy = r_eye_l[1] - l_eye_r[1]
    roll = float(math.degrees(math.atan2(dy, dx + 1e-9)))

    return yaw, pitch, roll


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class PostureFeatureExtractor:
    """
    Stateless transformer: MediaPipe landmarks → fixed-length float32 vector.

    Usage
    -----
    extractor = PostureFeatureExtractor()
    vector    = extractor.extract(face_landmarks, frame_shape=(480, 640))

    Parameters
    ----------
    face_landmarks : mediapipe.framework.formats.landmark_pb2.NormalizedLandmarkList
        The `face_landmarks` object returned by ``FaceMesh.process()``.
    frame_shape : (height, width)
        Used to compute face-size-to-frame-area ratio.

    Returns
    -------
    np.ndarray, shape (NUM_FEATURES,), dtype float32
        Feature vector ready for classifier input.
        Returns a zero vector if landmark extraction fails.
    """

    def extract(
        self,
        face_landmarks,
        pose_landmarks=None,
        frame_shape: Tuple[int, int] = (480, 640),
    ) -> np.ndarray:
        """Extract and return a normalised feature vector."""
        try:
            return self._extract(face_landmarks, pose_landmarks, frame_shape)
        except Exception:
            # Return safe zeros so inference stays non-blocking
            return np.zeros(NUM_FEATURES, dtype=np.float32)

    def _extract(
        self,
        face_landmarks,
        pose_landmarks,
        frame_shape: Tuple[int, int],
    ) -> np.ndarray:
        lm = face_landmarks.landmark
        h, w = frame_shape

        # ── Head pose ──────────────────────────────────────────────────────
        yaw, pitch, roll = _estimate_head_pose(lm)

        # ── Eye landmarks ──────────────────────────────────────────────────
        l_top    = _lm(lm, _LEFT_EYE_TOP)
        l_bot    = _lm(lm, _LEFT_EYE_BOTTOM)
        l_left   = _lm(lm, _LEFT_EYE_LEFT)
        l_right  = _lm(lm, _LEFT_EYE_RIGHT)

        r_top    = _lm(lm, _RIGHT_EYE_TOP)
        r_bot    = _lm(lm, _RIGHT_EYE_BOTTOM)
        r_left   = _lm(lm, _RIGHT_EYE_LEFT)
        r_right  = _lm(lm, _RIGHT_EYE_RIGHT)

        left_ear_val  = _eye_aspect_ratio(l_top, l_bot, l_left, l_right)
        right_ear_val = _eye_aspect_ratio(r_top, r_bot, r_left, r_right)

        # Eye level ratio — average normalised y of eye centres
        left_eye_centre_y  = (l_top[1] + l_bot[1]) / 2.0
        right_eye_centre_y = (r_top[1] + r_bot[1]) / 2.0
        eye_level_ratio    = float((left_eye_centre_y + right_eye_centre_y) / 2.0)

        # Horizontal eye asymmetry
        eye_horizontal_diff = float(abs(left_eye_centre_y - right_eye_centre_y))

        # ── Nose / face geometry ───────────────────────────────────────────
        nose      = _lm(lm, _NOSE_TIP)
        chin      = _lm(lm, _CHIN)
        forehead  = _lm(lm, _FOREHEAD)
        left_edge = _lm(lm, _LEFT_FACE_EDGE)
        right_edge= _lm(lm, _RIGHT_FACE_EDGE)

        eye_mid_y    = eye_level_ratio
        nose_eye_dist = float(abs(nose[1] - eye_mid_y))

        face_width  = _dist2d(left_edge, right_edge)
        face_height = _dist2d(forehead, chin)
        face_aspect_ratio = float(face_width / max(face_height, 1e-6))

        # Face size relative to frame (proxy for forward lean)
        bbox_area  = face_width * face_height * (w * h)
        frame_area = float(w * h)
        face_size_ratio = float(bbox_area / max(frame_area, 1.0))

        # Chin / forehead vertical positioning (pitch proxy)
        chin_forehead_ratio = float(
            (chin[1] - forehead[1]) / max(face_height, 1e-6)
        )

        # ── Mouth ──────────────────────────────────────────────────────────
        top_lip    = _lm(lm, _TOP_MOUTH)
        bot_lip    = _lm(lm, _BOTTOM_MOUTH)
        left_mouth = _lm(lm, _LEFT_MOUTH)
        right_mouth= _lm(lm, _RIGHT_MOUTH)

        mouth_v    = _dist2d(top_lip, bot_lip)
        mouth_h    = _dist2d(left_mouth, right_mouth)
        mouth_openness = float(mouth_v / max(mouth_h, 1e-6))

        # Inter-eye distance
        l_eye_r   = _lm(lm, _LEFT_EYE_RIGHT)
        r_eye_l   = _lm(lm, _RIGHT_EYE_LEFT)
        inter_eye_dist = _dist2d(l_eye_r, r_eye_l)

        # ── Pose geometry ──────────────────────────────────────────────────
        shoulder_angle = 0.0
        neck_angle = 0.0
        torso_inclination = 0.0
        spine_orientation = 0.0
        
        if pose_landmarks:
            plm = pose_landmarks.landmark
            l_sh = _lm(plm, 11)
            r_sh = _lm(plm, 12)
            l_hip = _lm(plm, 23)
            r_hip = _lm(plm, 24)
            p_nose = _lm(plm, 0)
            
            # Shoulder angle (roll)
            dx_sh = r_sh[0] - l_sh[0]
            dy_sh = r_sh[1] - l_sh[1]
            shoulder_angle = float(math.degrees(math.atan2(dy_sh, dx_sh + 1e-9)))
            
            # Midpoints
            mid_sh = (l_sh + r_sh) / 2.0
            mid_hip = (l_hip + r_hip) / 2.0
            
            # Neck angle (pitch/yaw proxy)
            dx_neck = p_nose[0] - mid_sh[0]
            dy_neck = p_nose[1] - mid_sh[1]
            neck_angle = float(math.degrees(math.atan2(dy_neck, dx_neck + 1e-9)))
            
            # Torso inclination (lean forward/back proxy)
            dz_torso = mid_sh[2] - mid_hip[2]
            dy_torso = max(mid_hip[1] - mid_sh[1], 1e-6)
            torso_inclination = float(math.degrees(math.atan2(dz_torso, dy_torso)))
            
            # Spine orientation (lean left/right proxy)
            dx_spine = mid_sh[0] - mid_hip[0]
            spine_orientation = float(math.degrees(math.atan2(dx_spine, dy_torso)))

        # ── Assemble vector ────────────────────────────────────────────────
        vector = np.array([
            yaw,
            pitch,
            roll,
            shoulder_angle,
            neck_angle,
            torso_inclination,
            spine_orientation,
            face_size_ratio,
            inter_eye_dist,
            eye_level_ratio,
            eye_horizontal_diff,
            nose_eye_dist,
            face_aspect_ratio,
            chin_forehead_ratio,
            left_ear_val,
            right_ear_val,
            mouth_openness,
        ], dtype=np.float32)

        return vector

    # ------------------------------------------------------------------
    # Batch helper (used by training pipeline)
    # ------------------------------------------------------------------

    def extract_batch(
        self,
        landmark_batch: List,
        frame_shape: Tuple[int, int] = (480, 640),
    ) -> np.ndarray:
        """
        Extract features for a list of face_landmark objects.

        Returns
        -------
        np.ndarray, shape (N, NUM_FEATURES)
        """
        rows = [self.extract(lm, frame_shape) for lm in landmark_batch]
        return np.vstack(rows).astype(np.float32)


# Module-level singleton
feature_extractor = PostureFeatureExtractor()
