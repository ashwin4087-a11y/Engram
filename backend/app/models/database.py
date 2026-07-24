"""
[DEPRECATED] Legacy database module.

Canonical database implementation is located at:
- Core database engine & sessions: `app.core.database`
- Domain ORM models: `app.domain.entities.models`
"""
from app.core.database import Base, database_manager, get_db_session  # noqa: F401
from app.domain.entities.models import Entity, Episode, Fact, Relationship, Session  # noqa: F401