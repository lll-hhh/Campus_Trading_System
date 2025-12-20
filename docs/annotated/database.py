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
            ),  # 注: Postgres 引擎配置
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
        for db_name, engine in self._engines.items():
            configure_engine_isolation(engine, db_name)  # 注: 为每个引擎设置事务隔离与相关参数

        # 创建 session factories
        self._sessions: Dict[str, sessionmaker[Session]] = {
            name: sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
            for name, engine in self._engines.items()
        }  # 注: 为每个引擎创建对应的 sessionmaker

        # 注册同步监听器(仅 MySQL 作为主库)
        register_sync_listeners(self._sessions["mysql"])  # 注: 将 MySQL 的 session factory 注册 ORM 变更监听器

    def get_engine(self, name: str) -> Engine:  # 注: 返回指定名称的 Engine
        """Return the engine for the given database name."""

        return self._engines[name]

    def reconfigure_engine(self, name: str, dsn: str, pool_size: Optional[int] = None) -> None:
        """Hot-reload a database engine with a new DSN."""  # 注: 动态替换指定名称的引擎

        if name not in self._engines:
            raise KeyError(f"Unknown database engine: {name}")  # 注: 未知引擎名抛错

        if name == "sqlite":
            engine = create_engine(
                dsn,
                pool_pre_ping=True,
                pool_size=1,
                max_overflow=0,
                echo=self._settings.debug,
                future=True,
            )  # 注: SQLite 的特殊重建配置
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
            )  # 注: 其余数据库的重建配置

        configure_engine_isolation(engine, name)  # 注: 为新引擎配置隔离级别
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)  # 注: 新的 sessionmaker

        old_engine = self._engines.get(name)
        if old_engine is not None:
            old_engine.dispose()  # 注: 释放旧引擎的连接池资源

        self._engines[name] = engine  # 注: 更新内部引擎映射
        self._sessions[name] = session_factory  # 注: 更新 session factory 映射

        if name == "mysql":
            register_sync_listeners(session_factory)  # 注: 若重启 MySQL，重新注册同步监听器

    @contextmanager
    def session_scope(self, name: str) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""  # 注: 提供事务上下文管理器

        session_factory = self._sessions[name]
        session = session_factory()
        session.info.setdefault("db_name", name)  # 注: 在 session.info 中记录 db 名称，供监听器使用
        try:
            yield session  # 注: 将 session 暴露给调用者使用
            session.commit()  # 注: 调用方返回后提交事务
        except Exception:
            session.rollback()  # 注: 发生异常时回滚事务
            raise
        finally:
            session.close()  # 注: 最终关闭 session


db_manager = DatabaseManager()  # 注: 全局单例 DatabaseManager


def get_all_engines() -> Dict[str, Engine]:
    """Return all database engines."""
    return db_manager._engines  # 注: 返回内部引擎映射（仅用于只读访问）


def get_engine(name: str) -> Engine:
    """Return the engine for the given database name."""
    return db_manager.get_engine(name)  # 注: 代理方法，返回指定引擎


def get_session_scope(name: str):
    """Get a session scope for the given database name."""
    return db_manager.session_scope(name)  # 注: 返回上下文管理器以供 `with` 使用
