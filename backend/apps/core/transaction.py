"""
Transaction management utilities with configurable isolation levels.

This module provides:
- Transaction decorators with retry logic
- Context managers for transactional scopes
- Savepoint support for nested transactions
- Deadlock detection and automatic retry
- Isolation level configuration per database type
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
    """
    Transaction configuration for different database types.
    
    Each database has optimal isolation level based on use case:
    - MySQL/MariaDB: REPEATABLE READ (default InnoDB, prevents phantom reads)
    - PostgreSQL: READ COMMITTED (MVCC优势,减少锁竞争)
    - SQLite: SERIALIZABLE (单写入器模型,最强一致性)
    """

    # MySQL/MariaDB 默认 REPEATABLE READ,适合多表同步场景
    MYSQL_ISOLATION = IsolationLevel.REPEATABLE_READ
    MARIADB_ISOLATION = IsolationLevel.REPEATABLE_READ

    # PostgreSQL MVCC 特性,READ COMMITTED 性能更优
    POSTGRES_ISOLATION = IsolationLevel.READ_COMMITTED

    # SQLite 单写入器,使用 SERIALIZABLE 保证最强一致性
    SQLITE_ISOLATION = IsolationLevel.SERIALIZABLE

    # 连接池配置
    POOL_SIZE = 10  # 每个数据库连接池大小
    MAX_OVERFLOW = 20  # 超出 pool_size 的临时连接数
    POOL_TIMEOUT = 30  # 获取连接超时(秒)
    POOL_RECYCLE = 3600  # 连接回收时间(秒),防止 MySQL "gone away"

    # 事务超时配置
    TRANSACTION_TIMEOUT = 30  # 事务执行超时(秒)
    LOCK_TIMEOUT = 10  # 锁等待超时(秒)

    # 重试配置
    MAX_RETRIES = 3  # 死锁/序列化失败最大重试次数
    RETRY_DELAY = 0.1  # 重试延迟(秒)
    RETRY_BACKOFF = 2.0  # 退避倍数

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
    
    Args:
        engine: SQLAlchemy Engine instance
        db_name: Database name (mysql/mariadb/postgres/sqlite)
    """
    isolation_level = TransactionConfig.get_isolation_level(db_name)

    @event.listens_for(engine, "connect")
    def set_isolation_level(dbapi_conn, connection_record):
        """Set isolation level on new connection."""
        cursor = dbapi_conn.cursor()
        
        # 设置事务隔离级别
        if db_name in ("mysql", "mariadb"):
            cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level.value}")
            # 设置锁等待超时
            cursor.execute(f"SET SESSION innodb_lock_wait_timeout = {TransactionConfig.LOCK_TIMEOUT}")
            # 启用严格模式
            cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE'")
        elif db_name == "postgres":
            cursor.execute(f"SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL {isolation_level.value}")
            # 设置语句超时
            cursor.execute(f"SET statement_timeout = '{TransactionConfig.TRANSACTION_TIMEOUT}s'")
            cursor.execute(f"SET lock_timeout = '{TransactionConfig.LOCK_TIMEOUT}s'")
        elif db_name == "sqlite":
            # SQLite 通过 PRAGMA 设置
            cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous = NORMAL")  # 平衡性能与安全
            cursor.execute(f"PRAGMA busy_timeout = {TransactionConfig.LOCK_TIMEOUT * 1000}")  # 毫秒
        
        cursor.close()
        logger.info(f"Configured {db_name} engine with isolation level: {isolation_level.value}")


def is_retryable_error(error: Exception) -> bool:
    """
    Check if error is retryable (deadlock, serialization failure).
    
    Args:
        error: Exception raised during transaction
        
    Returns:
        True if error should trigger retry
    """
    if not isinstance(error, (DBAPIError, OperationalError)):
        return False
    
    error_msg = str(error).lower()
    retryable_patterns = [
        "deadlock",  # MySQL/MariaDB/PostgreSQL 死锁
        "lock wait timeout",  # MySQL 锁等待超时
        "could not serialize",  # PostgreSQL 序列化失败
        "database is locked",  # SQLite 锁定
        "serialization failure",  # PostgreSQL SERIALIZABLE 冲突
    ]
    return any(pattern in error_msg for pattern in retryable_patterns)


def with_transaction(
    db_name: str,
    max_retries: Optional[int] = None,
    isolation_level: Optional[IsolationLevel] = None,
) -> Callable[[F], F]:
    """
    Decorator for transactional functions with automatic retry on deadlock.
    
    Usage:
        @with_transaction("mysql", max_retries=3)
        def update_inventory(session: Session, item_id: int, quantity: int):
            # Business logic here
            pass
    
    Args:
        db_name: Database name (mysql/mariadb/postgres/sqlite)
        max_retries: Max retry attempts (default from config)
        isolation_level: Override isolation level for this transaction
        
    Returns:
        Decorated function
    """
    if max_retries is None:
        max_retries = TransactionConfig.MAX_RETRIES

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            session: Optional[Session] = kwargs.get("session")
            if not session:
                raise ValueError("Session must be provided as keyword argument")

            # 设置事务隔离级别(如果指定)
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
    """
    Context manager for transactional scope with savepoint support.
    
    Usage:
        with transactional_scope(session, savepoint=True) as tx:
            # Nested transaction with savepoint
            tx.execute(...)
    
    Args:
        session: SQLAlchemy session
        savepoint: Use savepoint for nested transaction
        isolation_level: Override isolation level
        
    Yields:
        Session object
    """
    if isolation_level:
        session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.value}"))

    if savepoint:
        # 嵌套事务使用 SAVEPOINT
        nested = session.begin_nested()
        try:
            yield session
            nested.commit()
        except Exception:
            nested.rollback()
            raise
    else:
        # 顶层事务
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


@contextmanager
def read_only_transaction(session: Session) -> Generator[Session, None, None]:
    """
    Context manager for read-only transaction (optimization).
    
    Read-only transactions can benefit from:
    - Reduced locking overhead
    - Better query performance in some databases
    - Explicit intent declaration
    
    Usage:
        with read_only_transaction(session) as tx:
            results = tx.query(Item).all()
    
    Args:
        session: SQLAlchemy session
        
    Yields:
        Session object
    """
    db_name = session.info.get("db_name", "")
    
    # 设置只读事务
    if db_name in ("mysql", "mariadb"):
        session.execute(text("SET TRANSACTION READ ONLY"))
    elif db_name == "postgres":
        session.execute(text("SET TRANSACTION READ ONLY"))
    # SQLite 不支持 READ ONLY 语法,自动优化
    
    try:
        yield session
        session.commit()  # READ ONLY 事务仍需 commit 释放资源
    except Exception:
        session.rollback()
        raise


class TransactionMetrics:
    """
    Track transaction metrics for monitoring.
    
    Metrics include:
    - Total transactions
    - Retry counts
    - Deadlock counts
    - Average duration
    """

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


# Global metrics instance
transaction_metrics = TransactionMetrics()
