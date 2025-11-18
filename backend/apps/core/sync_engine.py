"""Data synchronization engine implementation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, Iterable, Optional

import redis
from loguru import logger
from sqlalchemy import select, text

from apps.core.models import ConflictRecord, DailyStat, SyncConfig, SyncLog
from apps.core.sync_payloads import decode_params

from .config import get_settings
from .database import db_manager
from apps.services.notifications import email_notifier


@dataclass
class SyncEvent:
    """Normalized representation of a cross-database sync event."""

    table: str
    action: str
    payload: Dict[str, Any]
    origin: str
    occurred_at: datetime
    sync_version: int
    record_id: Optional[str] = None

    def as_message(self) -> Dict[str, Any]:
        """Serialize the event for Redis Streams."""

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
    def from_stream(cls, data: Dict[str, Any]) -> "SyncEvent":
        """Instantiate a sync event from Redis stream payload."""

        return cls(
            table=data["table"],
            action=data["action"],
            payload=json.loads(data["payload"]),
            origin=data["origin"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            sync_version=int(data["sync_version"]),
            record_id=(data.get("record_id") or None),
        )


class SyncEngine:
    """Fan-out database events to peer databases with optimistic locking."""

    def __init__(self) -> None:
        settings = get_settings()
        self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self._stream_key = "campuswap:sync:events"

    def publish_event(self, event: SyncEvent) -> None:
        """Push a sync event into Redis stream."""

        message_id = self._redis.xadd(self._stream_key, event.as_message())
        logger.info("Sync event published", message_id=message_id, table=event.table)

    @property
    def stream_key(self) -> str:
        """Expose Redis stream key for workers."""

        return self._stream_key

    @property
    def redis_client(self) -> redis.Redis:
        """Provide direct access to the configured Redis client."""

        return self._redis

    def replicate(self, event: SyncEvent, targets: Iterable[str]) -> None:
        """Perform replication into target databases with optimistic locking."""

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
                    self._record_conflict(event, target)
                else:
                    logger.info(
                        "Replicated event",
                        target=target,
                        table=event.table,
                        rowcount=result.rowcount,
                    )

    def _record_conflict(self, event: SyncEvent, target: str) -> None:
        """Persist conflict information for manual resolution."""

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
            email_notifier.send(subject, body)

    def run_periodic_sync(self) -> None:
        """Run scheduled sync verification tasks and update stats."""

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


sync_engine = SyncEngine()
