"""Annotated copy of `backend/apps/core/sync_listeners.py` with per-line comments.
此文件为只读注释版，供 PPT/报告阅读，不用于运行。
"""
from __future__ import annotations  # 注: 启用未来注解语法

from collections import OrderedDict  # 注: 导入有序字典
from dataclasses import dataclass  # 注: 导入 dataclass 装饰器
from datetime import datetime, timezone  # 注: 导入时间处理
from typing import Any, Dict, List, Optional  # 注: 导入类型提示

from loguru import logger  # 注: 导入日志库
from sqlalchemy import event, inspect  # 注: 导入 SQLAlchemy 事件和检查器
from sqlalchemy.orm import Session, class_mapper, sessionmaker  # 注: 导入 ORM 组件
from sqlalchemy.orm.state import InstanceState  # 注: 导入实例状态类

from apps.core.sync_payloads import encode_params  # 注: 导入参数编码工具

META_COLUMNS = {"created_at", "updated_at", "sync_version"}  # 注: 定义元数据列集合，用于变更检测过滤


@dataclass
class PendingSyncMutation:  # 注: 定义待同步变更的数据类
    """In-memory representation of a change waiting to be published."""

    action: str  # 注: 动作类型 (insert, update, delete)
    table_name: str  # 注: 表名
    model_class: type  # 注: 模型类
    primary_key: Dict[str, Any]  # 注: 主键字典
    record_id: str  # 注: 记录 ID 字符串
    previous_version: Optional[int]  # 注: 变更前的版本号
    row_data: Optional[Dict[str, Any]] = None  # 注: 行数据快照，在 flush 阶段保存


def register_sync_listeners(factory: sessionmaker[Session]) -> None:  # 注: 注册同步监听器的主入口
    """Attach sync listeners to the provided session factory."""

    event.listen(factory, "before_flush", _before_flush)  # 注: 监听 flush 前事件，用于初始化和版本控制
    event.listen(factory, "after_flush", _after_flush)  # 注: 监听 flush 后事件，用于收集变更
    event.listen(factory, "after_commit", _after_commit)  # 注: 监听提交后事件，用于发布消息
    event.listen(factory, "after_rollback", _after_rollback)  # 注: 监听回滚后事件，用于清理上下文


def _before_flush(session: Session, _flush_context: Any, _instances: Any) -> None:  # 注: flush 前钩子
    if not _is_primary_session(session):  # 注: 仅处理主库 session
        return

    now = datetime.now(timezone.utc)  # 注: 获取当前 UTC 时间

    for obj in list(session.new):  # 注: 遍历新增对象
        if not _is_tracked_object(obj):  # 注: 过滤非追踪对象
            continue
        _initialize_new_object(obj, now)  # 注: 初始化新对象（设置版本号等）

    for obj in list(session.dirty):  # 注: 遍历修改对象
        if not _is_tracked_object(obj):  # 注: 过滤非追踪对象
            continue
        state = _inspect_state(obj)  # 注: 获取对象状态
        if state.deleted or not _has_meaningful_changes(state):  # 注: 过滤删除或无实质变更的对象
            continue
        _touch_updated(obj, now)  # 注: 更新 updated_at
        _increment_version(obj, state)  # 注: 递增 sync_version


def _after_flush(session: Session, _flush_context: Any) -> None:  # 注: flush 后钩子
    if not _is_primary_session(session):  # 注: 仅处理主库 session
        return

    pending = session.info.setdefault("pending_sync_events", [])  # 注: 获取或初始化待处理事件列表
    pending.extend(_collect_mutations(session))  # 注: 收集本次 flush 的变更并添加到列表


def _after_commit(session: Session) -> None:  # 注: 提交后钩子
    if not _is_primary_session(session):  # 注: 非主库 session 清理上下文并返回
        session.info.pop("pending_sync_events", None)
        return

    pending: List[PendingSyncMutation] = session.info.pop("pending_sync_events", [])  # 注: 取出并清空待处理事件
    if not pending:  # 注: 无事件则返回
        return

    ready_events: List[Dict[str, Any]] = []  # 注: 准备发布的事件列表
    for mutation in pending:  # 注: 遍历变更
        payload = _build_sql_payload(session, mutation)  # 注: 构建 SQL 载荷
        if payload is not None:
            ready_events.append(payload)

    if not ready_events:
        return

    _publish_events(session.info.get("db_name", "mysql"), ready_events)  # 注: 发布事件到 Redis


def _after_rollback(session: Session) -> None:  # 注: 回滚后钩子
    session.info.pop("pending_sync_events", None)  # 注: 清空待处理事件，丢弃变更


def _publish_events(origin: str, events: List[Dict[str, Any]]) -> None:  # 注: 发布事件辅助函数
    from apps.core.sync_engine import SyncEvent, sync_engine  # 注: 延迟导入避免循环依赖

    for payload in events:  # 注: 遍历事件载荷
        sync_event = SyncEvent(  # 注: 创建 SyncEvent 对象
            table=payload["table"],
            action=payload["action"],
            payload={"statement": payload["statement"], "params": payload["params"]},
            origin=origin,
            occurred_at=datetime.now(timezone.utc),
            sync_version=payload["sync_version"],
            record_id=payload["record_id"],
        )
        sync_engine.publish_event(sync_event)  # 注: 调用引擎发布


def _collect_mutations(session: Session) -> List[PendingSyncMutation]:  # 注: 收集变更核心逻辑
    mutations: List[PendingSyncMutation] = []  # 注: 变更列表

    for obj in list(session.new):  # 注: 处理新增对象
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        pk = _extract_primary_key(state)  # 注: 提取主键
        if not pk:
            continue
        # 在 flush 阶段就序列化实例数据
        mapper = class_mapper(state.mapper.class_)
        row_data = _serialize_instance(mapper, obj)  # 注: 序列化对象数据
        mutations.append(  # 注: 添加 insert 变更
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

    for obj in list(session.dirty):  # 注: 处理修改对象
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        if state.deleted or not _has_meaningful_changes(state):
            continue
        pk = _extract_primary_key(state)
        if not pk:
            continue
        previous_version = state.info.get("previous_sync_version")  # 注: 获取旧版本号
        # 在 flush 阶段就序列化实例数据
        mapper = class_mapper(state.mapper.class_)
        row_data = _serialize_instance(mapper, obj)
        mutations.append(  # 注: 添加 update 变更
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

    for obj in list(session.deleted):  # 注: 处理删除对象
        if not _is_tracked_object(obj):
            continue
        state = _inspect_state(obj)
        pk = _extract_primary_key(state)
        if not pk:
            continue
        previous_version = _current_version(state)
        mutations.append(  # 注: 添加 delete 变更
            PendingSyncMutation(
                action="delete",
                table_name=_table_name(state),
                model_class=state.mapper.class_,
                primary_key=pk,
                record_id=_record_id(pk),
                previous_version=previous_version,
                row_data=None,  # 删除操作不需要 row_data
            )
        )

    return mutations  # 注: 返回收集到的变更列表


def _build_sql_payload(session: Session, mutation: PendingSyncMutation) -> Optional[Dict[str, Any]]:  # 注: 构建 SQL 载荷
    class_mapper(mutation.model_class)  # 注: 确保 mapper 已初始化

    if mutation.action == "delete":  # 注: 处理删除
        statement, params = _compose_delete_statement(
            mutation.table_name, mutation.primary_key, mutation.previous_version
        )
        sync_version = mutation.previous_version or 0
    else:  # 注: 处理插入和更新
        # 使用在 flush 阶段保存的 row_data，避免在 commit 后查询
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
                mutation.table_name, mutation.primary_key, row_data, mutation.previous_version
            )
        sync_version = row_data.get("sync_version", 0)

    return {  # 注: 返回标准化的事件载荷
        "table": mutation.table_name,
        "action": mutation.action,
        "statement": statement,
        "params": params,
        "sync_version": sync_version,
        "record_id": mutation.record_id,
    }

# ...existing code...
