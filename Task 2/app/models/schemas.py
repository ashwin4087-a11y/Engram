"""
schemas.py — Pydantic Models (Request / Response Contracts)
============================================================

Every data structure that crosses the API boundary is defined here
with strict typing.  Services may also use these models internally
to ensure structural consistency across layers.

Module 1 defines only the schemas needed for the health endpoint.
Additional schemas will be added as each module is built.

Design decision:
    ApiResponse wraps EVERY endpoint so the frontend always receives
    the same envelope:  { success, data, message }.
"""

from typing import Any, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Generic API envelope
# ---------------------------------------------------------------------------

class ApiResponse(BaseModel):
    """
    Standard envelope for all API responses.

    Attributes:
        success: Whether the request completed without error.
        data:    Payload (endpoint-specific dict), or None on error.
        message: Human-readable status or error description.
    """

    success: bool
    data: Optional[dict[str, Any]] = None
    message: str = ""
