"""Database utilities for managing multi-database connections."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Generator

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
        settings = get_settings()
        
        # 创建引擎,使用优化的连接池配置
        self._engines: Dict[str, Engine] = {
            "mysql": create_engine(
                settings.mysql_dsn,
                pool_pre_ping=True,
                pool_size=TransactionConfig.POOL_SIZE,
                max_overflow=TransactionConfig.MAX_OVERFLOW,
                pool_timeout=TransactionConfig.POOL_TIMEOUT,
                pool_recycle=TransactionConfig.POOL_RECYCLE,
                echo=settings.debug,
                future=True,
            ),
            "mariadb": create_engine(
                settings.mariadb_dsn,
                pool_pre_ping=True,
                pool_size=TransactionConfig.POOL_SIZE,
                max_overflow=TransactionConfig.MAX_OVERFLOW,
                pool_timeout=TransactionConfig.POOL_TIMEOUT,
                pool_recycle=TransactionConfig.POOL_RECYCLE,
                echo=settings.debug,
                future=True,
            ),
            "postgres": create_engine(
                settings.postgres_dsn,
                pool_pre_ping=True,
                pool_size=TransactionConfig.POOL_SIZE,
                max_overflow=TransactionConfig.MAX_OVERFLOW,
                pool_timeout=TransactionConfig.POOL_TIMEOUT,
                pool_recycle=TransactionConfig.POOL_RECYCLE,
                echo=settings.debug,
                future=True,
            ),
            "sqlite": create_engine(
                settings.sqlite_dsn,
                pool_pre_ping=True,
                # SQLite 特殊配置:单写入器,较小的连接池
                pool_size=1,
                max_overflow=0,
                echo=settings.debug,
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
        
        # 注册同步监听器(仅 MySQL 作为主库)
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


def get_all_engines() -> Dict[str, Engine]:
    """Return all database engines."""
    return db_manager._engines


def get_engine(name: str) -> Engine:
    """Return the engine for the given database name."""
    return db_manager.get_engine(name)


def get_session_scope(name: str):
    """Get a session scope for the given database name."""
    return db_manager.session_scope(name)
