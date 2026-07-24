"""Session routes."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps import get_session_repo
from app.domain.entities.models import Session
from app.domain.repositories.session_repo import SessionRepository
from app.schemas.session import SessionCreate, SessionResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate | None = None,
    session_repo: SessionRepository = Depends(get_session_repo),
) -> SessionResponse:
    title = body.title if body else "New Memory Session"
    session = Session(title=title)
    created = await session_repo.create(session)
    return SessionResponse.model_validate(created)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    session_repo: SessionRepository = Depends(get_session_repo),
) -> SessionResponse:
    session = await session_repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.model_validate(session)
