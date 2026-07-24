"""
Unit tests for Knowledge Graph Engine & Contradiction Engine.
"""
import pytest
import uuid
from app.memory.graph.contradiction import ContradictionEngine


@pytest.mark.asyncio
async def test_contradiction_engine_heuristic():
    class DummyFactRepo:
        async def get_by_entity(self, entity_id, active_only=True):
            class DummyFact:
                id = uuid.uuid4()
                statement = "User lives in Berlin"
            return [DummyFact()]

        async def supersede(self, old_id, new_id):
            pass

    class DummyAuditRepo:
        async def create(self, log):
            pass

    engine = ContradictionEngine(fact_repo=DummyFactRepo(), contradiction_repo=DummyAuditRepo())  # type: ignore
    session_id = uuid.uuid4()
    entity_id = uuid.uuid4()

    is_conflict = await engine.check_and_resolve(
        session_id, entity_id, "User lives in Chennai", uuid.uuid4()
    )
    assert is_conflict is True
