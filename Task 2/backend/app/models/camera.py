"""Camera Models"""
from dataclasses import dataclass
import numpy as np

@dataclass
class FrameData:
    """
    Data wrapper for a single frame capture.
    Using a dataclass for low overhead during high-frequency captures.
    """
    frame: np.ndarray
    timestamp: float
