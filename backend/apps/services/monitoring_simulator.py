"""Synthetic monitoring data helpers for admin dashboards."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Tuple

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.core.database import db_manager
from apps.services.system_settings import SystemSettingsService


@dataclass
class SimulatedQuery:
    """In-memory representation of a fake running query."""

    id: str
    database: str
    query: str
    status: str
    duration: int
    started_at: datetime = field(default_factory=datetime.utcnow)

    def serialize(self) -> Dict[str, object]:
        now = datetime.utcnow()
        elapsed = max(int((now - self.started_at).total_seconds() * 1000), self.duration)
        return {
            "id": self.id,
            "database": self.database,
            "query": self.query,
            "status": self.status,
            "duration": elapsed,
        }


class SimulatedQueryStore:
    """Simple cache that produces fake long-running queries."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._queries: Dict[str, SimulatedQuery] = {}
        self._expires_at: datetime = datetime.min

    def snapshot(self, limit: int = 5) -> List[Dict[str, object]]:
        with self._lock:
            if datetime.utcnow() >= self._expires_at or len(self._queries) < limit:
                self._regenerate(limit)
            return [query.serialize() for query in list(self._queries.values())[:limit]]

    def kill(self, query_id: str) -> bool:
        with self._lock:
            removed = self._queries.pop(query_id, None)
            return removed is not None

    def _regenerate(self, limit: int) -> None:
        self._queries.clear()
        self._expires_at = datetime.utcnow() + timedelta(seconds=30)
        templates: List[Tuple[str, str]] = [
            ("items", "SELECT * FROM items WHERE status = 'available' ORDER BY updated_at DESC"),
            (
                "transactions",
                "SELECT buyer_id, seller_id, amount FROM transactions WHERE status = 'pending' FOR UPDATE",
            ),
            (
                "notifications",
                "UPDATE notifications SET is_read = 1 WHERE user_id = :uid LIMIT 200",
            ),
            ("reports", "SELECT * FROM reports WHERE status = 'open' LIMIT 50"),
        ]
        databases = ["mysql", "postgres", "mariadb", "sqlite"]
        for idx in range(limit):
            table, sql = random.choice(templates)
            db = random.choice(databases)
            query_id = f"SIM-{datetime.utcnow().strftime('%H%M%S')}-{idx}"
            duration = random.randint(1_500, 6_000)
            status = random.choice(["running", "copying result", "sending data"])
            self._queries[query_id] = SimulatedQuery(
                id=query_id,
                database=db,
                query=f"/* {table} */ {sql}",
                status=status,
                duration=duration,
            )


class MonitoringDataSimulator:
    """Seed and aggregate monitoring data so dashboards remain lively."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._last_seed_at: datetime = datetime.min

    def ensure_baseline(self, force: bool = False) -> None:
        with self._lock:
            refresh_due = datetime.utcnow() - self._last_seed_at > timedelta(minutes=5)
            if not force and not refresh_due:
                return
            with db_manager.session_scope("mysql") as session:
                self._ensure_tables(session)
                self._ensure_database_configs(session)
                self._seed_performance_metrics(session)
                self._seed_sync_logs(session)
                self._seed_conflicts(session)
                self._seed_daily_stats(session)
            self._last_seed_at = datetime.utcnow()

    def generate_heatmap(self, days: int = 7) -> List[Dict[str, int]]:
        days = max(1, min(days, 14))
        cutoff = datetime.utcnow() - timedelta(days=days)
        buckets: Dict[Tuple[int, int], int] = {}
        with db_manager.session_scope("mysql") as session:
            rows = (
                session.execute(
                    text(
                        """
                        SELECT started_at, stats
                        FROM sync_logs
                        WHERE started_at >= :cutoff
                        ORDER BY started_at DESC
                        LIMIT 2000
                        """
                    ),
                    {"cutoff": cutoff},
                )
                .mappings()
                .all()
            )
        for row in rows:
            started_at = row.get("started_at")
            if not isinstance(started_at, datetime):
                continue
            stats = row.get("stats") or {}
            if isinstance(stats, str):
                try:
                    stats = json.loads(stats)
                except json.JSONDecodeError:
                    stats = {}
            volume = int(stats.get("rows_synced") or stats.get("rows") or random.randint(40, 160))
            bucket_key = (started_at.weekday(), started_at.hour)
            buckets[bucket_key] = buckets.get(bucket_key, 0) + volume
        # Ensure matrix has full coverage
        result: List[Dict[str, int]] = []
        for day in range(days):
            for hour in range(24):
                key = ((datetime.utcnow() - timedelta(days=day)).weekday(), hour)
                value = buckets.get(key)
                if value is None:
                    value = random.randint(20, 90)
                result.append({"day": key[0], "hour": hour, "value": value})
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_tables(self, session: Session) -> None:
        session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS maintenance_jobs (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    task VARCHAR(64) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    affected_rows INT DEFAULT 0,
                    details JSON NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS conflict_records (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    table_name VARCHAR(128) NOT NULL,
                    record_id VARCHAR(64) NOT NULL,
                    source VARCHAR(32) NOT NULL,
                    target VARCHAR(32) NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    payload JSON NULL,
                    resolved TINYINT(1) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP NULL,
                    INDEX idx_conflict_table_record (table_name, record_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        )
        current_db = session.execute(text("SELECT DATABASE()"))
        schema_name = current_db.scalar() if current_db else None

        def ensure_column(name: str, ddl: str) -> None:
            if not schema_name:
                return
            exists = session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.columns
                    WHERE table_schema = :schema AND table_name = 'conflict_records' AND column_name = :column
                    """
                ),
                {"schema": schema_name, "column": name},
            ).scalar()
            if not exists:
                try:
                    session.execute(text(f"ALTER TABLE conflict_records ADD COLUMN {ddl}"))
                except Exception as exc:  # pragma: no cover - best effort
                    logger.warning("Failed to add column %s to conflict_records: %s", name, exc)
                    session.rollback()
                    session.begin()

        ensure_column("table_name", "table_name VARCHAR(128) NOT NULL")
        ensure_column("record_id", "record_id VARCHAR(64) NOT NULL")
        ensure_column("source", "source VARCHAR(32) NOT NULL DEFAULT 'mysql'")
        ensure_column("target", "target VARCHAR(32) NOT NULL DEFAULT 'sqlite'")
        ensure_column("status", "status VARCHAR(32) NOT NULL DEFAULT 'pending'")
        ensure_column("payload", "payload JSON NULL")
        ensure_column("resolved", "resolved TINYINT(1) NOT NULL DEFAULT 0")
        ensure_column("created_at", "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
        ensure_column("resolved_at", "resolved_at TIMESTAMP NULL")

    def _resolve_conflict_column_names(self, session: Session) -> Dict[str, str | None]:
        current_db = session.execute(text("SELECT DATABASE()"))
        schema_name = current_db.scalar() if current_db else None
        if not schema_name:
            return {}
        rows = session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = 'conflict_records'
                """
            ),
            {"schema": schema_name},
        ).scalars()
        name_map = {name.lower(): name for name in rows}

        def pick(*candidates: str) -> str | None:
            for candidate in candidates:
                existing = name_map.get(candidate.lower())
                if existing:
                    return existing
            return None

        return {
            "table": pick("table_name", "table"),
            "record": pick("record_id", "recordid", "record_id"),
            "source": pick("source", "source_db"),
            "target": pick("target", "target_db"),
            "legacy_source": pick("source_db"),
            "legacy_target": pick("target_db"),
            "status": pick("status", "conflict_status"),
            "payload": pick("payload", "payload_json", "payload_data"),
            "created_at": pick("created_at", "created_time"),
        }

    def _ensure_database_configs(self, session: Session) -> None:
        service = SystemSettingsService(session)
        defaults = service._default_database_configs()
        for name, config in defaults.items():
            existing = service._fetch_setting("database", name)
            if existing:
                continue
            try:
                service.save_database_config(name, config, user_id=None)
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Failed to seed database config for %s: %s", name, exc)

    def _seed_performance_metrics(self, session: Session) -> None:
        recent = session.execute(
            text("SELECT COUNT(*) FROM performance_metrics WHERE recorded_at >= NOW() - INTERVAL 20 MINUTE")
        ).scalar()
        if recent and recent >= 12:
            return
        samples = [
            ("mysql", "query_time", 145.0, 200.0, True, "SELECT * FROM items WHERE status='available' ORDER BY updated_at DESC"),
            ("mysql", "query_time", 98.0, 200.0, False, "SELECT COUNT(*) FROM transactions WHERE status='pending'"),
            ("postgres", "query_time", 76.2, 180.0, False, "SELECT * FROM reports WHERE status='open' LIMIT 100"),
            ("mariadb", "query_time", 112.4, 220.0, True, "SELECT * FROM notifications WHERE is_read = 0 ORDER BY created_at DESC"),
            ("sqlite", "query_time", 34.5, 120.0, False, "SELECT * FROM favorites WHERE user_id = :uid"),
        ]
        for db_name, metric_type, value, threshold, alert, sql in samples:
            details = json.dumps(
                {
                    "sql": sql,
                    "table": sql.split("FROM ")[1].split()[0],
                    "count": random.randint(1, 300),
                    "max_time": value * random.uniform(1.2, 1.8),
                    "rows": random.randint(10, 500),
                    "suggestion": "为高频过滤列添加复合索引",
                },
                ensure_ascii=False,
            )
            session.execute(
                text(
                    """
                    INSERT INTO performance_metrics
                    (metric_type, db_name, metric_value, threshold_value, is_alert, details, recorded_at)
                    VALUES (:metric_type, :db_name, :metric_value, :threshold, :alert, :details, NOW())
                    """
                ),
                {
                    "metric_type": metric_type,
                    "db_name": db_name,
                    "metric_value": value,
                    "threshold": threshold,
                    "alert": alert,
                    "details": details,
                },
            )

    def _seed_sync_logs(self, session: Session) -> None:
        recent = session.execute(
            text("SELECT COUNT(*) FROM sync_logs WHERE started_at >= NOW() - INTERVAL 15 MINUTE")
        ).scalar()
        if recent and recent >= 6:
            return
        targets = ("mysql", "postgres", "mariadb", "sqlite")
        for target in targets:
            stats = {
                "target": target,
                "rows_synced": random.randint(40, 400),
                "conflicts": random.randint(0, 3),
                "mode": random.choice(["realtime", "periodic", "manual"]),
                "version": random.randint(100, 400),
            }
            duration = random.randint(20, 120)
            session.execute(
                text(
                    """
                    INSERT INTO sync_logs (config_id, status, started_at, completed_at, stats)
                    VALUES (1, :status, NOW() - INTERVAL :duration SECOND, NOW(), :stats)
                    """
                ),
                {
                    "status": random.choice(["completed", "running", "failed"]),
                    "duration": duration,
                    "stats": json.dumps(stats, ensure_ascii=False),
                },
            )

    def _seed_conflicts(self, session: Session) -> None:
        pending = session.execute(text("SELECT COUNT(*) FROM conflict_records WHERE resolved = 0"))
        total_pending = pending.scalar() if pending else 0
        if total_pending and total_pending >= 5:
            return
        columns = self._resolve_conflict_column_names(session)
        required = (columns.get("table"), columns.get("record"), columns.get("source"), columns.get("target"))
        if not all(required):
            logger.warning("conflict_records schema incomplete, skipping simulated conflicts: %s", columns)
            return
        templates = [
            ("items", "price"),
            ("transactions", "status"),
            ("users", "credit_score"),
        ]
        for table, field_name in templates:
            payload = {
                "field": field_name,
                "local": random.randint(10, 999),
                "remote": random.randint(10, 999),
            }
            cols = [columns["table"], columns["record"], columns["source"], columns["target"]]
            placeholders = [":table", ":record_id", ":source", ":target"]
            params = {
                "table": table,
                "record_id": str(random.randint(1, 5000)),
                "source": random.choice(["mysql", "postgres", "mariadb"]),
                "target": random.choice(["sqlite", "mysql", "postgres"]),
            }
            legacy_source = columns.get("legacy_source")
            if legacy_source and legacy_source not in cols:
                cols.append(legacy_source)
                placeholders.append(":source")
            legacy_target = columns.get("legacy_target")
            if legacy_target and legacy_target not in cols:
                cols.append(legacy_target)
                placeholders.append(":target")
            status_column = columns.get("status")
            if status_column:
                cols.append(status_column)
                placeholders.append(":status")
                params["status"] = "pending"
            payload_column = columns.get("payload")
            if payload_column:
                cols.append(payload_column)
                placeholders.append(":payload")
                params["payload"] = json.dumps(payload, ensure_ascii=False)
            created_column = columns.get("created_at")
            if created_column:
                cols.append(created_column)
                placeholders.append("NOW()")
            insert_sql = f"INSERT INTO conflict_records ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
            session.execute(
                text(insert_sql),
                params,
            )

    def _seed_daily_stats(self, session: Session) -> None:
        today = datetime.utcnow().date()
        for offset in range(14):
            day = today - timedelta(days=offset)
            session.execute(
                text(
                    """
                    INSERT IGNORE INTO daily_stats (stat_date, sync_success_count, sync_conflict_count, ai_request_count, inventory_changes)
                    VALUES (:stat_date, :success, :conflict, :ai, :inventory)
                    """
                ),
                {
                    "stat_date": day,
                    "success": random.randint(200, 500),
                    "conflict": random.randint(3, 20),
                    "ai": random.randint(40, 180),
                    "inventory": random.randint(90, 260),
                },
            )


def build_monitoring_simulator() -> MonitoringDataSimulator:
    return MonitoringDataSimulator()


def build_query_store() -> SimulatedQueryStore:
    return SimulatedQueryStore()


monitoring_data_simulator = build_monitoring_simulator()
query_simulator = build_query_store()
