"""Database utilities for managing MySQL connection."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .transaction import TransactionConfig, configure_engine_isolation


class DatabaseManager:
    """
    Create SQLAlchemy engine and session for MySQL.
    
    Features:
    - Connection pooling
    - Automatic transaction isolation level configuration
    - Connection health checks (pool_pre_ping)
    - Optimized pool settings for production workloads
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        
        # 创建引擎,使用优化的连接池配置
        self._engine = create_engine(
            self._settings.mysql_dsn,
            pool_pre_ping=True,
            pool_size=TransactionConfig.POOL_SIZE,
            max_overflow=TransactionConfig.MAX_OVERFLOW,
            pool_timeout=TransactionConfig.POOL_TIMEOUT,
            pool_recycle=TransactionConfig.POOL_RECYCLE,
            echo=self._settings.debug,
            future=True,
        )
        
        # 配置事务隔离级别和超时
        configure_engine_isolation(self._engine, "mysql")
        
        # 创建 session factory
        self._session_factory = sessionmaker(
            bind=self._engine, 
            autoflush=False, 
            autocommit=False, 
            future=True
        )

    def get_engine(self) -> Engine:
        """Return the MySQL engine."""
        return self._engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def session_scope(self, db_name: str = "mysql") -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations.
        
        Args:
            db_name: Database name (ignored, always uses MySQL)
        """
        with self.get_session() as session:
            yield session

# Global instance
db_manager = DatabaseManager()
