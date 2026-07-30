"""
api.py — Generic API Envelopes
===============================

Contains the standard response envelope used by all endpoints.
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

# Type variable for the generic data payload
DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """
    Standard envelope for all API responses.

    Attributes:
        success: Whether the request completed without error.
        data:    Payload of type DataT, or None on error.
        message: Human-readable status or error description.
    """

    success: bool
    data: Optional[DataT] = None
    message: str = ""
