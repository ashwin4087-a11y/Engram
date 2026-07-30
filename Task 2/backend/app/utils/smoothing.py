"""
smoothing.py — Data Smoothing Utilities
=======================================

Contains algorithms for smoothing noisy data streams.
"""

from typing import Optional


class ExponentialMovingAverage:
    """
    Applies Exponential Moving Average (EMA) to a scalar value.
    Smooths out jitter from raw detector measurements.
    
    Formula: val = alpha * new + (1 - alpha) * old
    """
    
    def __init__(self, alpha: float = 0.3):
        self._alpha = max(0.0, min(1.0, alpha))
        self._current_value: Optional[float] = None

    def update(self, new_value: float) -> float:
        """Applies the filter to a new reading and returns the smoothed value."""
        if self._current_value is None:
            self._current_value = new_value
        else:
            self._current_value = self._alpha * new_value + (1.0 - self._alpha) * self._current_value
            
        return self._current_value

    def get(self) -> Optional[float]:
        """Returns the current smoothed value without updating."""
        return self._current_value

    def reset(self) -> None:
        """Clears the history. Useful when tracking is lost."""
        self._current_value = None
