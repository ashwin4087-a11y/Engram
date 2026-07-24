"""
Unit tests for Hybrid Retrieval Engine & Scoring logic.
"""
import pytest
import uuid
from app.domain.repositories.episode_repo import EpisodeRepository
from app.domain.repositories.fact_repo import FactRepository
from app.memory.retrieval.engine import HybridRetrievalEngine


@pytest.mark.asyncio
async def test_retrieval_engine_fallback():
    # Test initialization with empty DB session
    class DummyRepo:
        async def get_by_session(self, *args, **kwargs):
            return []
        async def search_by_embedding(self, *args, **kwargs):
            return []

    engine = HybridRetrievalEngine(fact_repo=DummyRepo(), episode_repo=DummyRepo())  # type: ignore
    session_id = uuid.uuid4()
    res = await engine.retrieve(session_id, "test query")

    assert res.session_id == session_id
    assert res.total_retrieved == 0
    assert isinstance(res.memories, list)
