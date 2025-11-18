"""Database utilities for managing multi-database connections."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .sync_listeners import register_sync_listeners


class DatabaseManager:
    """Create SQLAlchemy engines and sessions for multiple databases."""

    def __init__(self) -> None:
        settings = get_settings()
        self._engines: Dict[str, Engine] = {
            "mysql": create_engine(settings.mysql_dsn, pool_pre_ping=True, future=True),
            "mariadb": create_engine(settings.mariadb_dsn, pool_pre_ping=True, future=True),
            "postgres": create_engine(settings.postgres_dsn, pool_pre_ping=True, future=True),
            "sqlite": create_engine(settings.sqlite_dsn, pool_pre_ping=True, future=True),
        }
        self._sessions: Dict[str, sessionmaker[Session]] = {
            name: sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
            for name, engine in self._engines.items()
        }
        register_sync_listeners(self._sessions["mysql"])

    def get_engine(self, name: str) -> Engine:
        """Return the engine for the given database name."""

        return self._engines[name]

    @contextmanager
    def session_scope(self, name: str) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""

        session_factory = self._sessions[name]
        session = session_factory()
        session.info.setdefault("db_name", name)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


db_manager = DatabaseManager()
