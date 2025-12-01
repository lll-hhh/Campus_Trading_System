"""
Transaction management utilities with configurable isolation levels.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from typing import Any, Callable, Generator, Optional, TypeVar

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class IsolationLevel(str, Enum):
    """Transaction isolation levels (SQL standard)."""

    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class TransactionConfig:
    """Transaction configuration for different database types."""

    MYSQL_ISOLATION = IsolationLevel.REPEATABLE_READ
    MARIADB_ISOLATION = IsolationLevel.REPEATABLE_READ
    POSTGRES_ISOLATION = IsolationLevel.READ_COMMITTED
    SQLITE_ISOLATION = IsolationLevel.SERIALIZABLE

    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600

    TRANSACTION_TIMEOUT = 30
    LOCK_TIMEOUT = 10

    MAX_RETRIES = 3
    RETRY_DELAY = 0.1
    RETRY_BACKOFF = 2.0

    @classmethod
    def get_isolation_level(cls, db_name: str) -> IsolationLevel:
        """Get isolation level for specific database."""
        mapping = {
            "mysql": cls.MYSQL_ISOLATION,
            "mariadb": cls.MARIADB_ISOLATION,
            "postgres": cls.POSTGRES_ISOLATION,
            "sqlite": cls.SQLITE_ISOLATION,
        }
        return mapping.get(db_name, IsolationLevel.READ_COMMITTED)


def configure_engine_isolation(engine: Engine, db_name: str) -> None:
    """
    Configure engine with appropriate isolation level and timeouts.
    """
    isolation_level = TransactionConfig.get_isolation_level(db_name)

    @event.listens_for(engine, "connect")
    def set_isolation_level(dbapi_conn, connection_record):
        """Set isolation level on new connection."""
        cursor = dbapi_conn.cursor()
        
        try:
            # ✅ 根据驱动类型判断数据库
            driver_name = str(type(dbapi_conn).__module__).lower()
            
            # MySQL/MariaDB (pymysql 驱动)
            if 'pymysql' in driver_name or 'mysql' in driver_name:
                cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level.value}")
                cursor.execute(f"SET SESSION innodb_lock_wait_timeout = {TransactionConfig.LOCK_TIMEOUT}")
            
            # PostgreSQL (psycopg 驱动)
            elif 'psycopg' in driver_name or 'pg' in driver_name:
                cursor.execute(f"SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL {isolation_level.value}")
                cursor.execute(f"SET statement_timeout = '{TransactionConfig.TRANSACTION_TIMEOUT}s'")
                cursor.execute(f"SET lock_timeout = '{TransactionConfig.LOCK_TIMEOUT}s'")
            
            # SQLite
            elif 'sqlite' in driver_name:
                cursor.execute("PRAGMA journal_mode = WAL")
                cursor.execute("PRAGMA synchronous = NORMAL")
                cursor.execute(f"PRAGMA busy_timeout = {TransactionConfig.LOCK_TIMEOUT * 1000}")
            
            logger.debug(f"Configured {db_name} with isolation level: {isolation_level.value}")
            
        except Exception as e:
            # 只是警告，不阻止连接
            logger.warning(f"Failed to configure isolation level for {db_name}: {e}")
        finally:
            cursor.close()


def is_retryable_error(error: Exception) -> bool:
    """Check if error is retryable (deadlock, serialization failure)."""
    if not isinstance(error, (DBAPIError, OperationalError)):
        return False
    
    error_msg = str(error).lower()
    retryable_patterns = [
        "deadlock",
        "lock wait timeout",
        "could not serialize",
        "database is locked",
        "serialization failure",
    ]
    return any(pattern in error_msg for pattern in retryable_patterns)


def with_transaction(
    db_name: str,
    max_retries: Optional[int] = None,
    isolation_level: Optional[IsolationLevel] = None,
) -> Callable[[F], F]:
    """Decorator for transactional functions with automatic retry on deadlock."""
    if max_retries is None:
        max_retries = TransactionConfig.MAX_RETRIES

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            session: Optional[Session] = kwargs.get("session")
            if not session:
                raise ValueError("Session must be provided as keyword argument")

            if isolation_level:
                session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.value}"))

            attempt = 0
            delay = TransactionConfig.RETRY_DELAY

            while attempt < max_retries:
                try:
                    result = func(*args, **kwargs)
                    session.commit()
                    return result
                except Exception as e:
                    session.rollback()
                    
                    if is_retryable_error(e) and attempt < max_retries - 1:
                        attempt += 1
                        logger.warning(
                            f"Retryable error in {func.__name__} (attempt {attempt}/{max_retries}): {e}"
                        )
                        time.sleep(delay)
                        delay *= TransactionConfig.RETRY_BACKOFF
                    else:
                        logger.error(f"Transaction failed in {func.__name__}: {e}")
                        raise

            raise RuntimeError(f"Transaction failed after {max_retries} retries")

        return wrapper  # type: ignore

    return decorator


@contextmanager
def transactional_scope(
    session: Session,
    savepoint: bool = False,
    isolation_level: Optional[IsolationLevel] = None,
) -> Generator[Session, None, None]:
    """Context manager for transactional scope with savepoint support."""
    if isolation_level:
        session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.value}"))

    if savepoint:
        nested = session.begin_nested()
        try:
            yield session
            nested.commit()
        except Exception:
            nested.rollback()
            raise
    else:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


@contextmanager
def read_only_transaction(session: Session) -> Generator[Session, None, None]:
    """Context manager for read-only transaction (optimization)."""
    db_name = session.info.get("db_name", "")
    
    try:
        if db_name in ("mysql", "mariadb"):
            session.execute(text("SET TRANSACTION READ ONLY"))
        elif db_name == "postgres":
            session.execute(text("SET TRANSACTION READ ONLY"))
    except Exception as e:
        logger.warning(f"Failed to set read-only transaction: {e}")
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise


class TransactionMetrics:
    """Track transaction metrics for monitoring."""

    def __init__(self):
        self.total_transactions = 0
        self.total_retries = 0
        self.total_deadlocks = 0
        self.total_duration = 0.0

    def record_transaction(
        self,
        duration: float,
        retries: int = 0,
        deadlocked: bool = False,
    ) -> None:
        """Record transaction metrics."""
        self.total_transactions += 1
        self.total_retries += retries
        self.total_duration += duration
        if deadlocked:
            self.total_deadlocks += 1

    def get_stats(self) -> dict:
        """Get transaction statistics."""
        avg_duration = (
            self.total_duration / self.total_transactions
            if self.total_transactions > 0
            else 0.0
        )
        return {
            "total_transactions": self.total_transactions,
            "total_retries": self.total_retries,
            "total_deadlocks": self.total_deadlocks,
            "avg_duration_seconds": round(avg_duration, 3),
            "retry_rate": (
                round(self.total_retries / self.total_transactions, 3)
                if self.total_transactions > 0
                else 0.0
            ),
        }


transaction_metrics = TransactionMetrics()
