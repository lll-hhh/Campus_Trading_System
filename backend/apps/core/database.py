"""Database utilities for managing multi-database connections."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .sync_listeners import register_sync_listeners
from .transaction import TransactionConfig, configure_engine_isolation


class DatabaseManager:
    """
    Create SQLAlchemy engines and sessions for multiple databases.
    
    Features:
    - Multi-database connection pooling
    - Automatic transaction isolation level configuration
    - Connection health checks (pool_pre_ping)
    - Optimized pool settings for production workloads
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        
        # 创建引擎,使用优化的连接池配置
        self._engines: Dict[str, Engine] = {
            "mysql": create_engine(
                self._settings.mysql_dsn,
                pool_pre_ping=True,
                pool_size=TransactionConfig.POOL_SIZE,
                max_overflow=TransactionConfig.MAX_OVERFLOW,
                pool_timeout=TransactionConfig.POOL_TIMEOUT,
                pool_recycle=TransactionConfig.POOL_RECYCLE,
                echo=self._settings.debug,
                future=True,
            ),
        }
        
        # 配置事务隔离级别和超时
        for db_name, engine in self._engines.items():
            configure_engine_isolation(engine, db_name)
        
        # 创建 session factories
        self._sessions: Dict[str, sessionmaker[Session]] = {
            name: sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
            for name, engine in self._engines.items()
        }
        
        # 注册同步监听器 (如果需要，目前仅保留 MySQL)
        # register_sync_listeners(self._sessions["mysql"])

    def get_engine(self, name: str = "mysql") -> Engine:
        """Return the engine for the given database name."""

        return self._engines[name]

    def reconfigure_engine(self, name: str, dsn: str, pool_size: Optional[int] = None) -> None:
        """Hot-reload a database engine with a new DSN."""

        if name not in self._engines:
            raise KeyError(f"Unknown database engine: {name}")

        if name == "sqlite":
            engine = create_engine(
                dsn,
                pool_pre_ping=True,
                pool_size=1,
                max_overflow=0,
                echo=self._settings.debug,
                future=True,
            )
        else:
            effective_pool = pool_size or TransactionConfig.POOL_SIZE
            engine = create_engine(
                dsn,
                pool_pre_ping=True,
                pool_size=effective_pool,
                max_overflow=TransactionConfig.MAX_OVERFLOW,
                pool_timeout=TransactionConfig.POOL_TIMEOUT,
                pool_recycle=TransactionConfig.POOL_RECYCLE,
                echo=self._settings.debug,
                future=True,
            )

        configure_engine_isolation(engine, name)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        old_engine = self._engines.get(name)
        if old_engine is not None:
            old_engine.dispose()

        self._engines[name] = engine
        self._sessions[name] = session_factory

        if name == "mysql":
            register_sync_listeners(session_factory)

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


def get_all_engines() -> Dict[str, Engine]:
    """Return all database engines."""
    return db_manager._engines


def get_engine(name: str) -> Engine:
    """Return the engine for the given database name."""
    return db_manager.get_engine(name)


def get_session_scope(name: str):
    """Get a session scope for the given database name."""
    return db_manager.session_scope(name)
