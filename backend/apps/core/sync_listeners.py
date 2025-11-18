"""SQLAlchemy session listeners that emit Redis sync events."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, class_mapper, sessionmaker
from sqlalchemy.orm.state import InstanceState

from apps.core.sync_payloads import encode_params

META_COLUMNS = {"created_at", "updated_at", "sync_version"}


@dataclass
class PendingSyncMutation:
    """In-memory representation of a change waiting to be published."""

    action: str
    table_name: str
    model_class: type
    primary_key: Dict[str, Any]
    record_id: str
    previous_version: Optional[int]


def register_sync_listeners(factory: sessionmaker[Session]) -> None:
    """Attach sync listeners to the provided session factory."""

    event.listen(factory, "before_flush", _before_flush)
    event.listen(factory, "after_flush", _after_flush)
    event.listen(factory, "after_commit", _after_commit)
    event.listen(factory, "after_rollback", _after_rollback)


def _before_flush(session: Session, _flush_context: Any, _instances: Any) -> None:
    if not _is_primary_session(session):
        return

    now = datetime.now(timezone.utc)

    for obj in list(session.new):
        if not _is_tracked_object(obj):
            continue
        _initialize_new_object(obj, now)

    for obj in list(session.dirty):
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        if state.deleted or not _has_meaningful_changes(state):
            continue
        _touch_updated(obj, now)
        _increment_version(obj, state)


def _after_flush(session: Session, _flush_context: Any) -> None:
    if not _is_primary_session(session):
        return

    pending = session.info.setdefault("pending_sync_events", [])
    pending.extend(_collect_mutations(session))


def _after_commit(session: Session) -> None:
    if not _is_primary_session(session):
        session.info.pop("pending_sync_events", None)
        return

    pending: List[PendingSyncMutation] = session.info.pop("pending_sync_events", [])
    if not pending:
        return

    ready_events: List[Dict[str, Any]] = []
    for mutation in pending:
        payload = _build_sql_payload(session, mutation)
        if payload is not None:
            ready_events.append(payload)

    if not ready_events:
        return

    _publish_events(session.info.get("db_name", "mysql"), ready_events)


def _after_rollback(session: Session) -> None:
    session.info.pop("pending_sync_events", None)


def _publish_events(origin: str, events: List[Dict[str, Any]]) -> None:
    from apps.core.sync_engine import SyncEvent, sync_engine

    for payload in events:
        sync_event = SyncEvent(
            table=payload["table"],
            action=payload["action"],
            payload={"statement": payload["statement"], "params": payload["params"]},
            origin=origin,
            occurred_at=datetime.now(timezone.utc),
            sync_version=payload["sync_version"],
            record_id=payload["record_id"],
        )
        sync_engine.publish_event(sync_event)


def _collect_mutations(session: Session) -> List[PendingSyncMutation]:
    mutations: List[PendingSyncMutation] = []

    for obj in list(session.new):
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        pk = _extract_primary_key(state)
        if not pk:
            continue
        mutations.append(
            PendingSyncMutation(
                action="insert",
                table_name=_table_name(state),
                model_class=state.mapper.class_,
                primary_key=pk,
                record_id=_record_id(pk),
                previous_version=None,
            )
        )

    for obj in list(session.dirty):
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        if state.deleted or not _has_meaningful_changes(state):
            continue
        pk = _extract_primary_key(state)
        if not pk:
            continue
        previous_version = state.info.get("previous_sync_version")
        mutations.append(
            PendingSyncMutation(
                action="update",
                table_name=_table_name(state),
                model_class=state.mapper.class_,
                primary_key=pk,
                record_id=_record_id(pk),
                previous_version=previous_version,
            )
        )

    for obj in list(session.deleted):
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        pk = _extract_primary_key(state)
        if not pk:
            continue
        previous_version = _current_version(state)
        mutations.append(
            PendingSyncMutation(
                action="delete",
                table_name=_table_name(state),
                model_class=state.mapper.class_,
                primary_key=pk,
                record_id=_record_id(pk),
                previous_version=previous_version,
            )
        )

    return mutations


def _build_sql_payload(session: Session, mutation: PendingSyncMutation) -> Optional[Dict[str, Any]]:
    mapper = class_mapper(mutation.model_class)

    if mutation.action == "delete":
        statement, params = _compose_delete_statement(
            mutation.table_name, mutation.primary_key, mutation.previous_version
        )
        sync_version = mutation.previous_version or 0
    else:
        instance = session.get(mutation.model_class, _identity_from_pk(mapper, mutation.primary_key))
        if instance is None:
            logger.warning(
                "Skipped sync mutation because row no longer exists",
                table=mutation.table_name,
                action=mutation.action,
                record_id=mutation.record_id,
            )
            return None
        row_data = _serialize_instance(mapper, instance)
        if mutation.action == "insert":
            statement, params = _compose_insert_statement(mutation.table_name, row_data)
        else:
            statement, params = _compose_update_statement(
                mutation.table_name, row_data, mutation.primary_key, mutation.previous_version
            )
        sync_version = row_data.get("sync_version", 1)

    return {
        "table": mutation.table_name,
        "action": mutation.action,
        "statement": statement,
        "params": encode_params(params),
        "record_id": mutation.record_id,
        "sync_version": sync_version,
    }


def _compose_insert_statement(table_name: str, row_data: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    columns = list(row_data.keys())
    placeholders = [f":{column}" for column in columns]
    statement = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    params = {column: row_data[column] for column in columns}
    return statement, params


def _compose_update_statement(
    table_name: str,
    row_data: Dict[str, Any],
    primary_key: Dict[str, Any],
    previous_version: Optional[int],
) -> tuple[str, Dict[str, Any]]:
    set_clauses: List[str] = []
    params: Dict[str, Any] = {}

    for column, value in row_data.items():
        if column in primary_key:
            continue
        param_name = f"set_{column}"
        set_clauses.append(f"{column} = :{param_name}")
        params[param_name] = value

    where_clauses, where_params = _build_where_clause(primary_key, previous_version)
    params.update(where_params)
    statement = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
    return statement, params


def _compose_delete_statement(
    table_name: str, primary_key: Dict[str, Any], previous_version: Optional[int]
) -> tuple[str, Dict[str, Any]]:
    where_clauses, params = _build_where_clause(primary_key, previous_version)
    statement = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"
    return statement, params


def _build_where_clause(
    primary_key: Dict[str, Any], previous_version: Optional[int]
) -> tuple[List[str], Dict[str, Any]]:
    clauses: List[str] = []
    params: Dict[str, Any] = {}
    for column, value in primary_key.items():
        param_name = f"pk_{column}"
        clauses.append(f"{column} = :{param_name}")
        params[param_name] = value
    if previous_version is not None:
        clauses.append("sync_version = :where_sync_version")
        params["where_sync_version"] = previous_version
    return clauses, params


def _initialize_new_object(obj: Any, now: datetime) -> None:
    if hasattr(obj, "sync_version") and not getattr(obj, "sync_version", None):
        setattr(obj, "sync_version", 1)
    if hasattr(obj, "created_at") and getattr(obj, "created_at", None) is None:
        setattr(obj, "created_at", now)
    if hasattr(obj, "updated_at"):
        setattr(obj, "updated_at", now)


def _touch_updated(obj: Any, now: datetime) -> None:
    if hasattr(obj, "updated_at"):
        setattr(obj, "updated_at", now)


def _increment_version(obj: Any, state: InstanceState[Any]) -> None:
    if state.info.get("sync_version_incremented"):
        return
    current_version = getattr(obj, "sync_version", 1) or 1
    state.info["previous_sync_version"] = current_version
    setattr(obj, "sync_version", current_version + 1)
    state.info["sync_version_incremented"] = True


def _has_meaningful_changes(state: InstanceState[Any]) -> bool:
    for attr in state.mapper.column_attrs:
        if attr.key in META_COLUMNS:
            continue
        history = state.attrs[attr.key].history
        if history.has_changes():
            return True
    return False


def _is_tracked_object(obj: Any) -> bool:
    return hasattr(obj, "__table__") and hasattr(obj, "sync_version")


def _is_primary_session(session: Session) -> bool:
    return session.info.get("db_name") == "mysql"


def _inspect_state(obj: Any) -> InstanceState[Any]:
    return inspect(obj)


def _extract_primary_key(state: InstanceState[Any]) -> Dict[str, Any]:
    pk = OrderedDict()
    for column in state.mapper.primary_key:
        value = state.attrs[column.key].value
        if value is None:
            return {}
        pk[column.key] = value
    return pk


def _record_id(primary_key: Dict[str, Any]) -> str:
    return "|".join(str(value) for value in primary_key.values())


def _current_version(state: InstanceState[Any]) -> Optional[int]:
    if "sync_version" not in state.attrs:
        return None
    return state.attrs["sync_version"].value


def _identity_from_pk(mapper, primary_key: Dict[str, Any]):
    identity = tuple(primary_key[column.key] for column in mapper.primary_key)
    return identity[0] if len(identity) == 1 else identity


def _serialize_instance(mapper, instance: Any) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for column in mapper.columns:
        values[column.key] = getattr(instance, column.key)
    return values


def _table_name(state: InstanceState[Any]) -> str:
    table = state.mapper.mapped_table
    if table.schema:
        return f"{table.schema}.{table.name}"
    return table.name
