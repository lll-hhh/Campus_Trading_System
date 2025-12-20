"""Annotated copy of `backend/apps/core/sync_engine.py` with per-line comments.
此文件为只读注释版，供 PPT/报告阅读，不用于运行。
"""
from __future__ import annotations  # 注: 启用未来注解语法

import json  # 注: JSON 序列化工具
from dataclasses import dataclass  # 注: 数据类装饰器
from datetime import date, datetime  # 注: 日期时间处理
from typing import Any, Dict, Iterable, Optional  # 注: 类型提示

import redis  # 注: Redis 客户端库
from loguru import logger  # 注: 日志库
from sqlalchemy import select, text  # 注: SQLAlchemy 查询构建器

from apps.core.models import ConflictRecord, DailyStat, SyncConfig, SyncLog  # 注: 导入相关模型
from apps.core.sync_payloads import decode_params  # 注: 参数解码工具

from .config import get_settings  # 注: 获取配置
from .database import db_manager  # 注: 数据库管理器
from apps.services.notifications import email_notifier  # 注: 邮件通知服务


@dataclass
class SyncEvent:  # 注: 定义跨数据库同步事件的标准结构
    """Normalized representation of a cross-database sync event."""

    table: str  # 注: 表名
    action: str  # 注: 动作 (insert/update/delete)
    payload: Dict[str, Any]  # 注: 载荷 (包含 SQL 语句和参数)
    origin: str  # 注: 来源数据库标识
    occurred_at: datetime  # 注: 事件发生时间
    sync_version: int  # 注: 同步版本号
    record_id: Optional[str] = None  # 注: 关联记录 ID

    def as_message(self) -> Dict[str, Any]:  # 注: 序列化为 Redis 消息格式
        """Serialize the event for Redis Streams."""

        return {
            "table": self.table,
            "action": self.action,
            "payload": json.dumps(self.payload, default=str),  # 注: payload 转 JSON 字符串
            "origin": self.origin,
            "occurred_at": self.occurred_at.isoformat(),  # 注: 时间转 ISO 格式
            "sync_version": self.sync_version,
            "record_id": self.record_id or "",
        }

    @classmethod
    def from_stream(cls, data: Dict[str, Any]) -> "SyncEvent":  # 注: 从 Redis 消息反序列化
        """Instantiate a sync event from Redis stream payload."""

        return cls(
            table=data["table"],
            action=data["action"],
            payload=json.loads(data["payload"]),  # 注: 解析 JSON payload
            origin=data["origin"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),  # 注: 解析时间
            sync_version=int(data["sync_version"]),
            record_id=(data.get("record_id") or None),
        )


class SyncEngine:  # 注: 同步引擎核心类，负责事件发布和复制
    """Fan-out database events to peer databases with optimistic locking."""

    def __init__(self) -> None:  # 注: 初始化
        settings = get_settings()
        self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)  # 注: 连接 Redis
        self._stream_key = "campuswap:sync:events"  # 注: 定义 Redis Stream 键名

    def publish_event(self, event: SyncEvent) -> None:  # 注: 发布事件到 Redis Stream
        """Push a sync event into Redis stream."""

        message_id = self._redis.xadd(self._stream_key, event.as_message())  # 注: 添加消息到 Stream
        logger.info("Sync event published", message_id=message_id, table=event.table)  # 注: 记录日志

    @property
    def stream_key(self) -> str:  # 注: 获取 Stream 键名属性
        """Expose Redis stream key for workers."""

        return self._stream_key

    @property
    def redis_client(self) -> redis.Redis:  # 注: 获取 Redis 客户端属性
        """Provide direct access to the configured Redis client."""

        return self._redis

    def replicate(self, event: SyncEvent, targets: Iterable[str]) -> None:  # 注: 在目标数据库执行复制
        """Perform replication into target databases with optimistic locking."""

        for target in targets:  # 注: 遍历所有目标数据库
            with db_manager.session_scope(target) as session:  # 注: 获取目标库 Session
                statement = text(event.payload["statement"])  # 注: 获取 SQL 语句
                params = decode_params(event.payload.get("params", {}))  # 注: 解码参数
                result = session.execute(statement, params)  # 注: 执行 SQL
                if event.action in {"update", "delete"} and result.rowcount == 0:  # 注: 乐观锁检查
                    logger.warning(  # 注: 如果更新/删除行数为 0，视为冲突
                        "Sync conflict detected",
                        table=event.table,
                        target=target,
                        record_id=event.record_id,
                    )
                    self._record_conflict(event, target)  # 注: 记录冲突
                else:
                    logger.info(  # 注: 记录成功日志
                        "Replicated event",
                        target=target,
                        table=event.table,
                        rowcount=result.rowcount,
                    )

    def _record_conflict(self, event: SyncEvent, target: str) -> None:  # 注: 记录冲突到数据库
        """Persist conflict information for manual resolution."""

        with db_manager.session_scope("mysql") as session:  # 注: 连接主库记录冲突
            record = ConflictRecord(  # 注: 创建冲突记录
                table_name=event.table,
                record_id=event.record_id or str(event.payload.get("record_id", "unknown")),
                source=event.origin,
                target=target,
                payload=event.payload,
            )
            session.add(record)
            session.flush()  # 注: 刷新以获取 ID
            logger.info("Conflict persisted", conflict_id=record.id)
            subject = f"Sync conflict detected on {event.table}"  # 注: 邮件标题
            body = (  # 注: 邮件正文
                "数据库同步冲突提醒\n\n"
                f"表: {event.table}\n来源: {event.origin}\n目标: {target}\n记录: {record.record_id}\n"
                "请登录管理端处理。"
            )
            email_notifier.send(subject, body)  # 注: 发送通知邮件

    def run_periodic_sync(self) -> None:  # 注: 运行周期性同步任务（统计与日志）
        """Run scheduled sync verification tasks and update stats."""

        now = datetime.utcnow()
        today = date.today()
        with db_manager.session_scope("mysql") as session:  # 注: 连接主库
            configs = (  # 注: 获取启用的同步配置
                session.execute(select(SyncConfig).where(SyncConfig.enabled.is_(True))).scalars().all()
            )
            for config in configs:  # 注: 为每个配置生成日志条目
                log_entry = SyncLog(
                    config_id=config.id,
                    status="scheduled",
                    started_at=now,
                    completed_at=now,
                    stats={"mode": config.mode, "target": config.target},
                )
                session.add(log_entry)
                config.last_run_at = now  # 注: 更新最后运行时间

            stat = (  # 注: 获取今日统计记录
                session.execute(select(DailyStat).where(DailyStat.stat_date == today)).scalar_one_or_none()
            )
            if stat is None:  # 注: 如果不存在则创建
                stat = DailyStat(stat_date=today)
                session.add(stat)

            increment = len(configs)
            stat.sync_success_count = (stat.sync_success_count or 0) + increment  # 注: 增加成功计数
            session.flush()


sync_engine = SyncEngine()  # 注: 全局单例实例
