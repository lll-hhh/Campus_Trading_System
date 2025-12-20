"""Annotated copy of `backend/apps/core/sync_listeners.py` with per-line comments.
仅用于阅读与答辩说明，不用于执行。
"""
from __future__ import annotations  # 注: 支持延迟类型注解

from collections import OrderedDict  # 注: 有序字典，用于按列顺序构造主键
from dataclasses import dataclass  # 注: dataclass 用于轻量数据结构
from datetime import datetime, timezone  # 注: 时间戳处理
from typing import Any, Dict, List, Optional  # 注: 类型提示

from loguru import logger  # 注: 日志记录库
from sqlalchemy import event, inspect  # 注: SQLAlchemy 事件与 inspect 用于对象状态检测
from sqlalchemy.orm import Session, class_mapper, sessionmaker  # 注: ORM 类型与映射器
from sqlalchemy.orm.state import InstanceState  # 注: ORM 实例状态类型

from apps.core.sync_payloads import encode_params  # 注: 将参数编码为可序列化形式的 helper

META_COLUMNS = {"created_at", "updated_at", "sync_version"}  # 注: 元字段在比较变更时忽略


@dataclass
class PendingSyncMutation:  # 注: 内存中暂存的变更记录结构
    action: str
    table_name: str
    model_class: type
    primary_key: Dict[str, Any]
    record_id: str
    previous_version: Optional[int]
    row_data: Optional[Dict[str, Any]] = None  # 注: 在 flush 阶段保存的行数据


def register_sync_listeners(factory: sessionmaker[Session]) -> None:  # 注: 给 session factory 注册钩子
    event.listen(factory, "before_flush", _before_flush)  # 注: flush 前触发
    event.listen(factory, "after_flush", _after_flush)  # 注: flush 后触发
    event.listen(factory, "after_commit", _after_commit)  # 注: commit 后触发发布
    event.listen(factory, "after_rollback", _after_rollback)  # 注: rollback 时清理


def _before_flush(session: Session, _flush_context: Any, _instances: Any) -> None:  # 注: flush 前收集并准备变更
    if not _is_primary_session(session):
        return  # 注: 仅在主库（mysql）上采集变更

    now = datetime.now(timezone.utc)  # 注: 使用 UTC 时间戳

    for obj in list(session.new):
        if not _is_tracked_object(obj):
            continue
        _initialize_new_object(obj, now)  # 注: 初始化新增对象的元字段

    for obj in list(session.dirty):
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        if state.deleted or not _has_meaningful_changes(state):
            continue
        _touch_updated(obj, now)  # 注: 更新 updated_at 时间
        _increment_version(obj, state)  # 注: 增加 sync_version


def _after_flush(session: Session, _flush_context: Any) -> None:  # 注: flush 后把序列化的数据加入 pending 列表
    if not _is_primary_session(session):
        return

    pending = session.info.setdefault("pending_sync_events", [])
    pending.extend(_collect_mutations(session))  # 注: 收集 mutations 并放入 session.info


def _after_commit(session: Session) -> None:  # 注: commit 成功后构建 payload 并发布事件
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

    _publish_events(session.info.get("db_name", "mysql"), ready_events)  # 注: 发布到 sync_engine


def _after_rollback(session: Session) -> None:  # 注: 回滚时清理 pending
    session.info.pop("pending_sync_events", None)


def _publish_events(origin: str, events: List[Dict[str, Any]]) -> None:  # 注: 将构建的事件转换为 SyncEvent 并 publish
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
        sync_engine.publish_event(sync_event)  # 注: 将事件写入 Redis stream


def _collect_mutations(session: Session) -> List[PendingSyncMutation]:  # 注: 遍历 session 的 new/dirty/deleted
    mutations: List[PendingSyncMutation] = []

    for obj in list(session.new):
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        pk = _extract_primary_key(state)
        if not pk:
            continue
        mapper = class_mapper(state.mapper.class_)
        row_data = _serialize_instance(mapper, obj)
        mutations.append(
            PendingSyncMutation(
                action="insert",
                table_name=_table_name(state),
                model_class=state.mapper.class_,
                primary_key=pk,
                record_id=_record_id(pk),
                previous_version=None,
                row_data=row_data,
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
        mapper = class_mapper(state.mapper.class_)
        row_data = _serialize_instance(mapper, obj)
        mutations.append(
            PendingSyncMutation(
                action="update",
                table_name=_table_name(state),
                model_class=state.mapper.class_,
                primary_key=pk,
                record_id=_record_id(pk),
                previous_version=previous_version,
                row_data=row_data,
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
                row_data=None,  # 注: 删除操作不需要 row_data
            )
        )

    return mutations


def _build_sql_payload(session: Session, mutation: PendingSyncMutation) -> Optional[Dict[str, Any]]:  # 注: 将 mutation 转为可执行的 SQL statement + params
    class_mapper(mutation.model_class)

    if mutation.action == "delete":
        statement, params = _compose_delete_statement(
            mutation.table_name, mutation.primary_key, mutation.previous_version
        )
        sync_version = mutation.previous_version or 0
    else:
        row_data = mutation.row_data
        if row_data is None:
            logger.warning(
                "Skipped sync mutation because row_data is None",
                table=mutation.table_name,
                action=mutation.action,
                record_id=mutation.record_id,
            )
            return None
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


def _compose_insert_statement(table_name: str, row_data: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:  # 注: 组装 INSERT 语句与参数
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
) -> tuple[str, Dict[str, Any]]:  # 注: 组装 UPDATE 语句
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
) -> tuple[str, Dict[str, Any]]:  # 注: 组装 DELETE 语句
    where_clauses, params = _build_where_clause(primary_key, previous_version)
    statement = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"
    return statement, params


def _build_where_clause(
    primary_key: Dict[str, Any], previous_version: Optional[int]
) -> tuple[List[str], Dict[str, Any]]:  # 注: 构造 WHERE 子句与参数
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


def _initialize_new_object(obj: Any, now: datetime) -> None:  # 注: 初始化新增对象的元字段
    if hasattr(obj, "sync_version") and not getattr(obj, "sync_version", None):
        setattr(obj, "sync_version", 1)
    if hasattr(obj, "created_at") and getattr(obj, "created_at", None) is None:
        setattr(obj, "created_at", now)
    if hasattr(obj, "updated_at"):
        setattr(obj, "updated_at", now)


def _touch_updated(obj: Any, now: datetime) -> None:  # 注: 更新 updated_at 字段
    if hasattr(obj, "updated_at"):
        setattr(obj, "updated_at", now)


def _increment_version(obj: Any, state: InstanceState[Any]) -> None:  # 注: 将 sync_version 自增并记录 previous_sync_version
    if state.info.get("sync_version_incremented"):
        return
    current_version = getattr(obj, "sync_version", 1) or 1
    state.info["previous_sync_version"] = current_version
    setattr(obj, "sync_version", current_version + 1)
    state.info["sync_version_incremented"] = True


def _has_meaningful_changes(state: InstanceState[Any]) -> bool:  # 注: 判断是否存在非元字段的变更
    for attr in state.mapper.column_attrs:
        if attr.key in META_COLUMNS:
            continue
        history = state.attrs[attr.key].history
        if history.has_changes():
            return True
    return False


def _is_tracked_object(obj: Any) -> bool:  # 注: 仅追踪具有 __table__ 与 sync_version 的 ORM 实例
    return hasattr(obj, "__table__") and hasattr(obj, "sync_version")


def _is_primary_session(session: Session) -> bool:  # 注: 判断 session 是否属于主库（mysql）
    return session.info.get("db_name") == "mysql"


def _inspect_state(obj: Any) -> InstanceState[Any]:
    return inspect(obj)  # 注: 返回 ORM 实例状态对象


def _extract_primary_key(state: InstanceState[Any]) -> Dict[str, Any]:  # 注: 提取主键列及其值
    pk = OrderedDict()
    for column in state.mapper.primary_key:
        value = state.attrs[column.key].value
        if value is None:
            return {}
        pk[column.key] = value
    return pk


def _record_id(primary_key: Dict[str, Any]) -> str:  # 注: 将主键值拼成字符串作为记录标识
    return "|".join(str(value) for value in primary_key.values())


def _current_version(state: InstanceState[Any]) -> Optional[int]:
    if "sync_version" not in state.attrs:
        return None
    return state.attrs["sync_version"].value


def _identity_from_pk(mapper, primary_key: Dict[str, Any]):
    identity = tuple(primary_key[column.key] for column in mapper.primary_key)
    return identity[0] if len(identity) == 1 else identity


def _serialize_instance(mapper, instance: Any) -> Dict[str, Any]:  # 注: 将实例属性序列化为字典
    values: Dict[str, Any] = {}
    for prop in mapper.iterate_properties:
        if hasattr(prop, 'columns'):
            attr_name = prop.key
            if hasattr(instance, attr_name):
                values[attr_name] = getattr(instance, attr_name)
    return values


def _table_name(state: InstanceState[Any]) -> str:
    table = state.mapper.mapped_table
    if table.schema:
        return f"{table.schema}.{table.name}"
    return table.name
