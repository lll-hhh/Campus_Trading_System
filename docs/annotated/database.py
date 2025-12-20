"""Annotated copy of `backend/apps/core/database.py` with per-line comments.
此文件为只读注释版，供 PPT/报告阅读，不用于运行。
"""
from __future__ import annotations  # 注: 启用未来注解语法，允许使用延迟类型提示

from contextlib import contextmanager  # 注: 引入 contextmanager 用于创建 session_scope 上下文管理器
from typing import Dict, Generator, Optional  # 注: 类型提示：字典，生成器，可选项

from sqlalchemy import create_engine  # 注: SQLAlchemy 的 create_engine 用于创建 DB 引擎
from sqlalchemy.engine import Engine  # 注: 类型提示 Engine
from sqlalchemy.orm import Session, sessionmaker  # 注: 导入 ORM 的 Session 与 sessionmaker

from .config import get_settings  # 注: 获取项目配置（包含各 DB 的 DSN）
from .sync_listeners import register_sync_listeners  # 注: 注册 ORM 同步监听器的函数
from .transaction import TransactionConfig, configure_engine_isolation  # 注: 事务配置与隔离级别配置函数


class DatabaseManager:  # 注: 数据库管理器，负责多库引擎与 session factory
    """
    Create SQLAlchemy engines and sessions for multiple databases.
    
    Features:
    - Multi-database connection pooling
    - Automatic transaction isolation level configuration
    - Connection health checks (pool_pre_ping)
    - Optimized pool settings for production workloads
    """  # 注: 类文档，说明职责

    def __init__(self) -> None:  # 注: 构造函数，初始化引擎与会话工厂
        self._settings = get_settings()  # 注: 读取配置对象

        # 创建引擎,使用优化的连接池配置
        self._engines: Dict[str, Engine] = {  # 注: 按数据库名称保存 Engine 实例
            "mysql": create_engine(
                self._settings.mysql_dsn,
                pool_pre_ping=True,
                pool_size=TransactionConfig.POOL_SIZE,
                max_overflow=TransactionConfig.MAX_OVERFLOW,
                pool_timeout=TransactionConfig.POOL_TIMEOUT,
                pool_recycle=TransactionConfig.POOL_RECYCLE,
                echo=self._settings.debug,
                future=True,
            ),  # 注: MySQL 引擎配置
            "mariadb": create_engine(
                self._settings.mariadb_dsn,
                pool_pre_ping=True,
                pool_size=TransactionConfig.POOL_SIZE,
                max_overflow=TransactionConfig.MAX_OVERFLOW,
                pool_timeout=TransactionConfig.POOL_TIMEOUT,
                pool_recycle=TransactionConfig.POOL_RECYCLE,
                echo=self._settings.debug,
                future=True,
            ),  # 注: MariaDB 引擎配置
            "postgres": create_engine(
                self._settings.postgres_dsn,
                pool_pre_ping=True,
                pool_size=TransactionConfig.POOL_SIZE,
                max_overflow=TransactionConfig.MAX_OVERFLOW,
                pool_timeout=TransactionConfig.POOL_TIMEOUT,
                pool_recycle=TransactionConfig.POOL_RECYCLE,
                echo=self._settings.debug,
                future=True,
            ),  # 注: PostgreSQL 引擎配置
            "sqlite": create_engine(
                self._settings.sqlite_dsn,
                pool_pre_ping=True,
                # SQLite 特殊配置:单写入器,较小的连接池
                pool_size=1,
                max_overflow=0,
                echo=self._settings.debug,
                future=True,
            ),  # 注: SQLite 引擎配置
        }
        
        # 配置事务隔离级别和超时
        for db_name, engine in self._engines.items():  # 注: 遍历所有引擎
            configure_engine_isolation(engine, db_name)  # 注: 配置隔离级别
        
        # 创建 session factories
        self._sessions: Dict[str, sessionmaker[Session]] = {  # 注: 创建 sessionmaker 字典
            name: sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
            for name, engine in self._engines.items()
        }
        
        # 注册同步监听器(仅 MySQL 作为主库)
        register_sync_listeners(self._sessions["mysql"])  # 注: 仅在 MySQL 上注册监听器

    def get_engine(self, name: str) -> Engine:  # 注: 获取指定名称的引擎
        """Return the engine for the given database name."""

        return self._engines[name]  # 注: 返回引擎实例

    def reconfigure_engine(self, name: str, dsn: str, pool_size: Optional[int] = None) -> None:  # 注: 动态重新配置引擎
        """Hot-reload a database engine with a new DSN."""

        if name not in self._engines:  # 注: 检查引擎是否存在
            raise KeyError(f"Unknown database engine: {name}")

        if name == "sqlite":  # 注: SQLite 特殊处理
            engine = create_engine(
                dsn,
                pool_pre_ping=True,
                pool_size=1,
                max_overflow=0,
                echo=self._settings.debug,
                future=True,
            )
        else:  # 注: 其他数据库通用配置
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

        configure_engine_isolation(engine, name)  # 注: 重新配置隔离级别
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)  # 注: 创建新 sessionmaker

        old_engine = self._engines.get(name)  # 注: 获取旧引擎
        if old_engine is not None:
            old_engine.dispose()  # 注: 销毁旧引擎

        self._engines[name] = engine  # 注: 更新引擎引用
        self._sessions[name] = session_factory  # 注: 更新 sessionmaker 引用

        if name == "mysql":  # 注: 如果是 MySQL，重新注册监听器
            register_sync_listeners(session_factory)

    @contextmanager
    def session_scope(self, name: str) -> Generator[Session, None, None]:  # 注: 上下文管理器，用于自动提交/回滚
        """Provide a transactional scope around a series of operations."""

        session_factory = self._sessions[name]  # 注: 获取对应的 sessionmaker
        session = session_factory()  # 注: 创建 session
        session.info.setdefault("db_name", name)  # 注: 在 session info 中记录数据库名称
        try:
            yield session  # 注: 将 session 暴露给调用者
            session.commit()  # 注: 成功则提交
        except Exception:
            session.rollback()  # 注: 异常则回滚
            raise  # 注: 重新抛出异常
        finally:
            session.close()  # 注: 最终关闭 session


db_manager = DatabaseManager()  # 注: 全局单例实例


def get_all_engines() -> Dict[str, Engine]:  # 注: 辅助函数，获取所有引擎
    """Return all database engines."""
    return db_manager._engines


def get_engine(name: str) -> Engine:  # 注: 辅助函数，获取指定引擎
    """Return the engine for the given database name."""
    return db_manager.get_engine(name)


def get_session_scope(name: str):  # 注: 辅助函数，获取 session scope
    """Get a session scope for the given database name."""
    return db_manager.session_scope(name)
