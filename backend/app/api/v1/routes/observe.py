"""Observe endpoint route."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_observe_service
from app.domain.services.observe_service import ObserveService
from app.schemas.observe import ObserveRequest, ObserveResponse

router = APIRouter(tags=["Observation Pipeline"])


@router.post("/observe", response_model=ObserveResponse)
async def observe_text(
    req: ObserveRequest,
    service: ObserveService = Depends(get_observe_service),
) -> ObserveResponse:
    """Ingest user input into the Memory Compiler pipeline."""
    return await service.observe(req)
