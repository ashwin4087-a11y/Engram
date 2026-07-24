"""Timeline endpoint route handler — fetches historical context snapshots."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps import get_bundle_repo
from app.domain.repositories.metrics_repo import ContextBundleRepository
from app.schemas.context import ContextBundleResponse

router = APIRouter(tags=["Timeline"])


@router.get("/timeline", response_model=list[ContextBundleResponse])
async def list_timeline(
    session_id: UUID,
    bundle_repo: ContextBundleRepository = Depends(get_bundle_repo),
) -> list[ContextBundleResponse]:
    """Retrieve historical context bundle snapshots for a session."""
    bundles = await bundle_repo.get_by_session(session_id)
    return [ContextBundleResponse(**b.bundle_json) for b in bundles]


@router.get("/context-bundle/{turn_number}", response_model=ContextBundleResponse)
@router.get("/context", response_model=ContextBundleResponse)
async def get_context_bundle_by_turn(
    session_id: UUID,
    turn_number: int,
    bundle_repo: ContextBundleRepository = Depends(get_bundle_repo),
) -> ContextBundleResponse:
    """Retrieve a specific context bundle snapshot by turn number."""
    bundle = await bundle_repo.get_by_turn(session_id, turn_number)
    if not bundle:
        raise HTTPException(status_code=404, detail="Context bundle not found")
    return ContextBundleResponse(**bundle.bundle_json)
