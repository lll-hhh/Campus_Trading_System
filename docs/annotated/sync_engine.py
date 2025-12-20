"""Annotated copy of `backend/apps/core/sync_engine.py` with per-line comments.
仅供阅读与答辩，不用于运行。
"""
from __future__ import annotations  # 注: 启用未来注解

import json  # 注: 用于序列化事件 payload
from dataclasses import dataclass  # 注: dataclass 用于 SyncEvent
from datetime import date, datetime  # 注: 日期/时间处理
from typing import Any, Dict, Iterable, Optional  # 注: 类型提示

import redis  # 注: Redis 客户端
from loguru import logger  # 注: 日志
from sqlalchemy import select, text  # 注: 执行原生 SQL

from apps.core.models import ConflictRecord, DailyStat, SyncConfig, SyncLog  # 注: ORM 模型
from apps.core.sync_payloads import decode_params  # 注: 解码参数 helper

from .config import get_settings  # 注: 读取配置
from .database import db_manager  # 注: 引入全局 db_manager
from apps.services.notifications import email_notifier  # 注: 邮件通知服务实例


@dataclass
class SyncEvent:  # 注: 标准化的跨库同步事件结构
    table: str
    action: str
    payload: Dict[str, Any]
    origin: str
    occurred_at: datetime
    sync_version: int
    record_id: Optional[str] = None

    def as_message(self) -> Dict[str, Any]:  # 注: 将事件序列化为 Redis Stream 可存储的字典
        return {
            "table": self.table,
            "action": self.action,
            "payload": json.dumps(self.payload, default=str),
            "origin": self.origin,
            "occurred_at": self.occurred_at.isoformat(),
            "sync_version": self.sync_version,
            "record_id": self.record_id or "",
        }

    @classmethod
    def from_stream(cls, data: Dict[str, Any]) -> "SyncEvent":  # 注: 从 Redis stream 数据反序列化
        return cls(
            table=data["table"],
            action=data["action"],
            payload=json.loads(data["payload"]),
            origin=data["origin"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            sync_version=int(data["sync_version"]),
            record_id=(data.get("record_id") or None),
        )


class SyncEngine:  # 注: 负责发布事件与执行跨库 replicate
    def __init__(self) -> None:
        settings = get_settings()
        self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)  # 注: 创建 Redis 客户端
        self._stream_key = "campuswap:sync:events"  # 注: Redis stream key

    def publish_event(self, event: SyncEvent) -> None:  # 注: 将事件写入 Redis stream
        message_id = self._redis.xadd(self._stream_key, event.as_message())
        logger.info("Sync event published", message_id=message_id, table=event.table)

    @property
    def stream_key(self) -> str:
        return self._stream_key  # 注: 暴露 stream key

    @property
    def redis_client(self) -> redis.Redis:
        return self._redis  # 注: 暴露 redis 客户端

    def replicate(self, event: SyncEvent, targets: Iterable[str]) -> None:  # 注: 在目标数据库执行 SQL
        for target in targets:
            with db_manager.session_scope(target) as session:
                statement = text(event.payload["statement"])
                params = decode_params(event.payload.get("params", {}))
                result = session.execute(statement, params)
                if event.action in {"update", "delete"} and result.rowcount == 0:
                    logger.warning(
                        "Sync conflict detected",
                        table=event.table,
                        target=target,
                        record_id=event.record_id,
                    )
                    self._record_conflict(event, target)  # 注: 记录冲突并发送通知
                else:
                    logger.info(
                        "Replicated event",
                        target=target,
                        table=event.table,
                        rowcount=result.rowcount,
                    )

    def _record_conflict(self, event: SyncEvent, target: str) -> None:  # 注: 将冲突写入 ConflictRecord 并通知管理员
        with db_manager.session_scope("mysql") as session:
            record = ConflictRecord(
                table_name=event.table,
                record_id=event.record_id or str(event.payload.get("record_id", "unknown")),
                source=event.origin,
                target=target,
                payload=event.payload,
            )
            session.add(record)
            session.flush()
            logger.info("Conflict persisted", conflict_id=record.id)
            subject = f"Sync conflict detected on {event.table}"
            body = (
                "数据库同步冲突提醒\n\n"
                f"表: {event.table}\n来源: {event.origin}\n目标: {target}\n记录: {record.record_id}\n"
                "请登录管理端处理。"
            )
            email_notifier.send(subject, body)  # 注: 发送邮件通知管理员

    def run_periodic_sync(self) -> None:  # 注: 定期统计与同步验证任务
        now = datetime.utcnow()
        today = date.today()
        with db_manager.session_scope("mysql") as session:
            configs = (
                session.execute(select(SyncConfig).where(SyncConfig.enabled.is_(True))).scalars().all()
            )
            for config in configs:
                log_entry = SyncLog(
                    config_id=config.id,
                    status="scheduled",
                    started_at=now,
                    completed_at=now,
                    stats={"mode": config.mode, "target": config.target},
                )
                session.add(log_entry)
                config.last_run_at = now

            stat = (
                session.execute(select(DailyStat).where(DailyStat.stat_date == today)).scalar_one_or_none()
            )
            if stat is None:
                stat = DailyStat(stat_date=today)
                session.add(stat)

            increment = len(configs)
            stat.sync_success_count = (stat.sync_success_count or 0) + increment
            session.flush()


sync_engine = SyncEngine()  # 注: 模块级单例，用于其它模块导入并使用
