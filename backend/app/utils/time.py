"""Time and date utilities."""
from __future__ import annotations

import math
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def seconds_since(dt: datetime) -> float:
    """Seconds elapsed since a given datetime."""
    return (utcnow() - dt).total_seconds()


def hours_since(dt: datetime) -> float:
    return seconds_since(dt) / 3600.0


def days_since(dt: datetime) -> float:
    return seconds_since(dt) / 86400.0


def decay_factor(dt: datetime, half_life_days: float = 30.0) -> float:
    """
    Ebbinghaus-style exponential decay factor.
    Returns a value between 0.0 (fully decayed) and 1.0 (fresh).
    """
    age_days = days_since(dt)
    if age_days <= 0:
        return 1.0
    return math.exp(-0.693 * age_days / half_life_days)


def recency_score(dt: datetime, max_age_hours: float = 168.0) -> float:
    """
    Linear recency score: 1.0 for just created, 0.0 for max_age_hours old or older.
    """
    age = hours_since(dt)
    return max(0.0, 1.0 - (age / max_age_hours))
