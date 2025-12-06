"""Domain service to manage administrator runtime settings."""
from __future__ import annotations

from datetime import datetime
from email.message import EmailMessage
import smtplib
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.core.config import get_settings
from apps.core.database import db_manager
from apps.core.models import SystemSetting
from apps.core.transaction import TransactionConfig


class SystemSettingsService:
    """Encapsulate persistence and health checks for admin settings."""

    SUPPORTED_DATABASES: Dict[str, Dict[str, str]] = {
        "mysql": {"label": "MySQL", "icon": "🐬"},
        "mariadb": {"label": "MariaDB", "icon": "🦭"},
        "postgres": {"label": "PostgreSQL", "icon": "🐘"},
        "sqlite": {"label": "SQLite", "icon": "🪶"},
    }

    DEFAULT_SYNC_CONFIG: Dict[str, Any] = {
        "mode": "hybrid",
        "interval_minutes": 15,
        "max_retries": 3,
        "auto_sync_enabled": True,
    }

    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Database configuration helpers
    # ------------------------------------------------------------------

    def list_database_configs(self) -> List[Dict[str, Any]]:
        stored = self._fetch_category_with_meta("database")
        defaults = self._default_database_configs()
        payload: List[Dict[str, Any]] = []

        for name, meta in self.SUPPORTED_DATABASES.items():
            runtime = defaults.get(name, {}).copy()
            stored_value = stored.get(name)
            updated_at = None
            if stored_value:
                updated_at = stored_value["updated_at"]
                runtime.update({k: v for k, v in stored_value["value"].items() if v not in (None, "")})

            status = self._quick_ping(name, runtime)
            payload.append(
                {
                    "name": name,
                    "label": meta["label"],
                    "icon": meta["icon"],
                    "host": runtime.get("host", ""),
                    "port": runtime.get("port", 0),
                    "username": runtime.get("username", ""),
                    "database": runtime.get("database", ""),
                    "pool_size": runtime.get("pool_size", TransactionConfig.POOL_SIZE),
                    "has_password": bool(runtime.get("password")),
                    "connected": status["connected"],
                    "status_message": status["status_message"],
                    "last_checked_at": status["last_checked_at"],
                    "updated_at": updated_at,
                }
            )

        return payload

    def save_database_config(self, name: str, data: Dict[str, Any], user_id: Optional[int]) -> Dict[str, Any]:
        self._ensure_supported_database(name)
        sanitized = self._normalize_database_payload(name, data)
        existing = self._fetch_setting("database", name)
        if existing and not sanitized.get("password"):
            sanitized["password"] = existing.get("password")

        setting = self._upsert("database", name, sanitized, user_id)
        self.session.flush()

        dsn = self._compose_dsn(name, sanitized)
        try:
            db_manager.reconfigure_engine(name, dsn, sanitized.get("pool_size"))
        except Exception as exc:  # pragma: no cover - safety net
            logger.error("Failed to reconfigure %s engine: %s", name, exc)

        status = self._quick_ping(name, sanitized)
        return {
            "name": name,
            "label": self.SUPPORTED_DATABASES[name]["label"],
            "icon": self.SUPPORTED_DATABASES[name]["icon"],
            "host": sanitized.get("host", ""),
            "port": sanitized.get("port", 0),
            "username": sanitized.get("username", ""),
            "database": sanitized.get("database", ""),
            "pool_size": sanitized.get("pool_size", TransactionConfig.POOL_SIZE),
            "has_password": bool(sanitized.get("password")),
            "connected": status["connected"],
            "status_message": status["status_message"],
            "last_checked_at": status["last_checked_at"],
            "updated_at": setting.updated_at,
        }

    def test_database_connection(self, name: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._ensure_supported_database(name)
        runtime = self._normalize_database_payload(name, data or {})
        if not runtime.get("host") and name != "sqlite":
            existing = self._fetch_setting("database", name) or self._default_database_configs().get(name, {})
            runtime = {**existing, **{k: v for k, v in runtime.items() if v not in (None, "")}}
        status = self._quick_ping(name, runtime)
        return {
            "name": name,
            "connected": status["connected"],
            "status_message": status["status_message"],
            "last_checked_at": status["last_checked_at"],
        }

    # ------------------------------------------------------------------
    # Sync strategy helpers
    # ------------------------------------------------------------------

    def get_sync_config(self) -> Dict[str, Any]:
        stored = self._fetch_setting_row("sync", "global")
        config = {**self.DEFAULT_SYNC_CONFIG}
        updated_at = None
        if stored:
            updated_at = stored.updated_at
            config.update(stored.value or {})
        return {**config, "updated_at": updated_at}

    def save_sync_config(self, data: Dict[str, Any], user_id: Optional[int]) -> Dict[str, Any]:
        payload = {
            "mode": data.get("mode", self.DEFAULT_SYNC_CONFIG["mode"]),
            "interval_minutes": int(data.get("interval_minutes", self.DEFAULT_SYNC_CONFIG["interval_minutes"])),
            "max_retries": int(data.get("max_retries", self.DEFAULT_SYNC_CONFIG["max_retries"])),
            "auto_sync_enabled": bool(data.get("auto_sync_enabled", True)),
        }
        setting = self._upsert("sync", "global", payload, user_id)
        self.session.flush()
        return {**payload, "updated_at": setting.updated_at}

    # ------------------------------------------------------------------
    # Notification helpers
    # ------------------------------------------------------------------

    def get_notification_config(self) -> Dict[str, Any]:
        stored = self._fetch_setting_row("notification", "email")
        payload = self._notification_defaults()
        updated_at = None
        if stored:
            updated_at = stored.updated_at
            payload.update(stored.value or {})
        return {**payload, "updated_at": updated_at}

    def save_notification_config(self, data: Dict[str, Any], user_id: Optional[int]) -> Dict[str, Any]:
        payload = self._normalize_notification_payload(data)
        existing = self._fetch_setting("notification", "email")
        if existing and not payload.get("smtp_password"):
            payload["smtp_password"] = existing.get("smtp_password")
        setting = self._upsert("notification", "email", payload, user_id)
        self.session.flush()
        return {**payload, "updated_at": setting.updated_at}

    def test_notification_channel(self, recipient: Optional[str] = None) -> Dict[str, Any]:
        config = self.get_notification_config()
        recipients = config.get("admin_emails", [])
        target = recipient or (recipients[0] if recipients else None)
        if not target:
            return {"success": False, "error": "缺少管理员邮箱，无法发送测试邮件"}
        if not config.get("smtp_server"):
            return {"success": False, "error": "SMTP 服务未配置"}

        message = EmailMessage()
        sender = config.get("from_email") or config.get("smtp_username") or "noreply@campuswap"
        message["Subject"] = "CampuSwap 管理后台测试邮件"
        message["From"] = sender
        message["To"] = target
        message.set_content("这是一封来自 CampuSwap 管理后台的测试邮件。")

        try:
            if config.get("use_tls", True):
                with smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=10) as smtp:
                    smtp.starttls()
                    if config.get("smtp_username") and config.get("smtp_password"):
                        smtp.login(config["smtp_username"], config["smtp_password"])
                    smtp.send_message(message)
            else:
                with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], timeout=10) as smtp:
                    if config.get("smtp_username") and config.get("smtp_password"):
                        smtp.login(config["smtp_username"], config["smtp_password"])
                    smtp.send_message(message)
            return {"success": True, "recipient": target}
        except Exception as exc:  # pragma: no cover - external dependency
            logger.error("SMTP test failed: %s", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_category_with_meta(self, category: str) -> Dict[str, Dict[str, Any]]:
        rows = (
            self.session.query(SystemSetting)
            .filter(SystemSetting.category == category)
            .all()
        )
        return {
            row.key: {"value": row.value or {}, "updated_at": row.updated_at}
            for row in rows
        }

    def _fetch_setting(self, category: str, key: str) -> Dict[str, Any]:
        row = self._fetch_setting_row(category, key)
        return row.value if row and row.value else {}

    def _fetch_setting_row(self, category: str, key: str) -> Optional[SystemSetting]:
        return (
            self.session.query(SystemSetting)
            .filter(SystemSetting.category == category, SystemSetting.key == key)
            .one_or_none()
        )

    def _upsert(self, category: str, key: str, value: Dict[str, Any], user_id: Optional[int]) -> SystemSetting:
        row = self._fetch_setting_row(category, key)
        if row:
            row.value = value
            row.updated_by = user_id
        else:
            row = SystemSetting(category=category, key=key, value=value, updated_by=user_id)
            self.session.add(row)
        return row

    def _default_database_configs(self) -> Dict[str, Dict[str, Any]]:
        env_map = {
            "mysql": self.settings.mysql_dsn,
            "mariadb": self.settings.mariadb_dsn,
            "postgres": self.settings.postgres_dsn,
            "sqlite": self.settings.sqlite_dsn,
        }
        defaults: Dict[str, Dict[str, Any]] = {}
        for name, dsn in env_map.items():
            defaults[name] = self._parse_dsn(name, dsn)
        return defaults

    def _parse_dsn(self, name: str, dsn: str) -> Dict[str, Any]:
        try:
            url = make_url(dsn)
        except Exception:
            return {
                "host": "",
                "port": 0,
                "username": "",
                "password": "",
                "database": "",
                "pool_size": TransactionConfig.POOL_SIZE,
            }

        if name == "sqlite":
            return {
                "host": "local",
                "port": 0,
                "username": "",
                "password": "",
                "database": url.database or "campus_trading.db",
                "pool_size": 1,
            }

        return {
            "host": url.host or "localhost",
            "port": url.port or 3306,
            "username": url.username or "root",
            "password": url.password or "",
            "database": url.database or "campus_trading",
            "pool_size": TransactionConfig.POOL_SIZE,
        }

    def _normalize_database_payload(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {k: v for k, v in (data or {}).items() if v not in (None, "")}
        if "port" in payload:
            payload["port"] = int(payload["port"])
        if "pool_size" in payload:
            payload["pool_size"] = max(1, int(payload["pool_size"]))
        if name == "sqlite":
            payload.setdefault("database", self._default_database_configs()["sqlite"].get("database"))
        return payload

    def _compose_dsn(self, name: str, data: Dict[str, Any]) -> str:
        if name == "sqlite":
            database = data.get("database") or self._default_database_configs()["sqlite"].get("database")
            return f"sqlite:///{database}"

        driver_map = {
            "mysql": "mysql+pymysql",
            "mariadb": "mariadb+pymysql",
            "postgres": "postgresql+psycopg2",
        }
        driver = driver_map[name]
        url = URL.create(
            drivername=driver,
            username=data.get("username"),
            password=data.get("password"),
            host=data.get("host"),
            port=data.get("port"),
            database=data.get("database"),
        )
        return str(url)

    def _quick_ping(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        status_message = "未配置连接信息"
        connected = False
        timestamp = datetime.utcnow()
        engine = None

        if name != "sqlite" and not data.get("host"):
            return {"connected": False, "status_message": status_message, "last_checked_at": timestamp}

        try:
            dsn = self._compose_dsn(name, data if data else self._default_database_configs().get(name, {}))
            engine_kwargs = self._engine_kwargs(name, data)
            engine = create_engine(dsn, **engine_kwargs)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            connected = True
            status_message = "连接成功"
        except SQLAlchemyError as exc:
            status_message = str(exc)
        except Exception as exc:  # pragma: no cover
            status_message = str(exc)
        finally:
            if engine is not None:
                try:
                    engine.dispose()
                except Exception:  # pragma: no cover
                    pass

        return {
            "connected": connected,
            "status_message": status_message,
            "last_checked_at": timestamp,
        }

    def _engine_kwargs(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if name == "sqlite":
            return {"pool_pre_ping": True, "pool_size": 1, "max_overflow": 0, "future": True}
        pool_size = data.get("pool_size", TransactionConfig.POOL_SIZE)
        return {
            "pool_pre_ping": True,
            "pool_size": pool_size,
            "max_overflow": TransactionConfig.MAX_OVERFLOW,
            "pool_timeout": TransactionConfig.POOL_TIMEOUT,
            "pool_recycle": TransactionConfig.POOL_RECYCLE,
            "future": True,
        }

    def _notification_defaults(self) -> Dict[str, Any]:
        return {
            "smtp_server": self.settings.smtp_host or "",
            "smtp_port": self.settings.smtp_port,
            "smtp_username": self.settings.smtp_username or "",
            "smtp_password": self.settings.smtp_password or "",
            "from_email": self.settings.alert_sender or (self.settings.smtp_username or "noreply@campuswap"),
            "admin_emails": list(self.settings.alert_recipients or []),
            "use_tls": self.settings.smtp_use_tls,
            "notify_conflicts": True,
            "notify_failures": True,
            "notify_daily_report": False,
        }

    def _normalize_notification_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        emails = data.get("admin_emails", [])
        if isinstance(emails, str):
            emails = [email.strip() for email in emails.split(",") if email.strip()]
        payload = {
            "smtp_server": data.get("smtp_server", ""),
            "smtp_port": int(data.get("smtp_port", 587)),
            "smtp_username": data.get("smtp_username", ""),
            "smtp_password": data.get("smtp_password", ""),
            "from_email": data.get("from_email", ""),
            "admin_emails": emails,
            "use_tls": bool(data.get("use_tls", True)),
            "notify_conflicts": bool(data.get("notify_conflicts", True)),
            "notify_failures": bool(data.get("notify_failures", True)),
            "notify_daily_report": bool(data.get("notify_daily_report", False)),
        }
        return payload

    def _ensure_supported_database(self, name: str) -> None:
        if name not in self.SUPPORTED_DATABASES:
            raise ValueError(f"Unsupported database: {name}")

