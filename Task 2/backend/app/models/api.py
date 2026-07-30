"""Generic API Envelopes"""
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

DataT = TypeVar("DataT")

class ApiResponse(BaseModel, Generic[DataT]):
    success: bool
    data: Optional[DataT] = None
    message: str = ""
