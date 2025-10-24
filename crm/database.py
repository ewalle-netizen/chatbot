"""Database initialisation and session management utilities."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings


Base = declarative_base()

_engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=_engine, class_=Session, autoflush=False, autocommit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all database tables."""

    Base.metadata.create_all(bind=_engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that provides a database session."""

    with session_scope() as session:
        yield session
