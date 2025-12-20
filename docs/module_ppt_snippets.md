每个后端核心模块：半页 PPT 文案与具体代码摘录
========================================

说明：下面每节为“半页幻灯片”内容（标题 + 1–2 行职责 + 关键代码摘录 + 演示要点），可直接复制到 PPT。代码摘录来自仓库相应文件，保留关键函数与调用点以便答辩时说明实现细节。

1) DatabaseManager（多 DB 引擎、会话管理）
- 核心文件：`backend/apps/core/database.py`
- 作用：创建并管理 mysql/mariadb/postgres/sqlite 引擎与 session_scope，统一提供事务上下文。

关键代码摘录：
```python
class DatabaseManager:
    def __init__(self) -> None:
        self._engines: Dict[str, Engine] = {
            "mysql": create_engine(self._settings.mysql_dsn, pool_pre_ping=True, ... , future=True),
            "sqlite": create_engine(self._settings.sqlite_dsn, pool_pre_ping=True, pool_size=1, ... , future=True),
        }

    @contextmanager
    def session_scope(self, name: str) -> Generator[Session, None, None]:
        session_factory = self._sessions[name]
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```

演示/要点：说明 multi-engine 支持与 hot-reconfigure（`reconfigure_engine`）；前端消费页面：`MarketplaceView.vue`、`ItemDetailView.vue`、`MyItemsView.vue`（CRUD）。

2) sync_listeners（ORM 事务监听 -> 构建并发布 SyncEvent）
- 核心文件：`backend/apps/core/sync_listeners.py`
- 作用：在 `before_flush/after_flush/after_commit` 钩子收集新增/修改/删除并构建可执行 SQL payload，commit 后调用 sync_engine 发布到 Redis Stream。

关键代码摘录：
```python
def register_sync_listeners(factory: sessionmaker[Session]) -> None:
    event.listen(factory, "before_flush", _before_flush)
    event.listen(factory, "after_flush", _after_flush)
    event.listen(factory, "after_commit", _after_commit)

def _after_commit(session: Session) -> None:
    pending: List[PendingSyncMutation] = session.info.pop("pending_sync_events", [])
    for mutation in pending:
        payload = _build_sql_payload(session, mutation)
        if payload is not None:
            ready_events.append(payload)
    _publish_events(session.info.get("db_name", "mysql"), ready_events)

def _publish_events(origin: str, events: List[Dict[str, Any]]) -> None:
    from apps.core.sync_engine import SyncEvent, sync_engine
    for payload in events:
        sync_event = SyncEvent(...)
        sync_engine.publish_event(sync_event)
```

演示/要点：展示如何通过事务钩子自动生成同步事件；前端消费：`ConflictTable.vue`、`DashboardView.vue`（显示由监听器产生的统计）。

3) sync_engine（发布事件、执行 replicate、冲突记录与通知）
- 核心文件：`backend/apps/core/sync_engine.py`
- 作用：将 SyncEvent 写入 Redis stream；在目标库执行 SQL（optimistic locking），在 rowcount==0 时记录冲突并调用邮件通知。

关键代码摘录：
```python
class SyncEngine:
    def publish_event(self, event: SyncEvent) -> None:
        message_id = self._redis.xadd(self._stream_key, event.as_message())

    def replicate(self, event: SyncEvent, targets: Iterable[str]) -> None:
        for target in targets:
            with db_manager.session_scope(target) as session:
                statement = text(event.payload["statement"])
                params = decode_params(event.payload.get("params", {}))
                result = session.execute(statement, params)
                if event.action in {"update", "delete"} and result.rowcount == 0:
                    self._record_conflict(event, target)

    def _record_conflict(self, event: SyncEvent, target: str) -> None:
        with db_manager.session_scope("mysql") as session:
            record = ConflictRecord(...)
            session.add(record)
            subject = f"Sync conflict detected on {event.table}"
            email_notifier.send(subject, body)
```

演示/要点：强调 Redis stream key：`campuswap:sync:events`（可在答辩时展示日志中的 message_id）；前端消费：`AdminConsoleView.vue`、`SystemSettingsView.vue`（测试邮件）。

4) sync_worker（Redis Stream 消费者，执行消费与 ack）
- 核心文件：`backend/apps/services/sync_worker.py`
- 作用：以 consumer group 拉取 stream 条目，调用 `sync_engine.replicate` 并 xack；支持 pending replay 与 graceful shutdown。

关键代码摘录：
```python
def consume_events(batch_size: int = 100, block_ms: int = 5000, replay_pending: bool = True, ...) -> int:
    _ensure_consumer_group(group_name)
    read_id = "0" if replay_pending else ">"
    while not STOP_EVENT.is_set():
        response = redis_client.xreadgroup(...)
        for stream_key, events in response:
            for event_id, payload in events:
                sync_event = SyncEvent.from_stream(payload)
                targets = tuple(t for t in ALL_TARGETS if t != sync_event.origin)
                sync_engine.replicate(sync_event, targets)
                redis_client.xack(stream_key, group_name, event_id)
```

演示/要点：演示命令行启动 worker（日志会显示“Replicated event”）；前端消费：`AdminOperationsView.vue`（触发 replay / 查看 pending）。

5) admin_operations 路由（管理/维护相关 HTTP API）
- 核心文件：`backend/apps/api_gateway/routers/admin_operations.py`
- 作用：提供运维 API（导出冲突、运行 SQL、回放/pending 操作、维护任务），并在管理界面被调用。

关键代码摘录：
```python
@router.post("/sql/run")
def run_sql(payload: SqlPayload, session: Session = Depends(get_db_session)):
    if payload.database not in SUPPORTED_DATABASES:
        raise HTTPException(400, "Unsupported")
    result = session.execute(text(payload.query))
    return {"rowcount": result.rowcount}

@router.post("/replay")
def replay_pending(...):
    # 调用 sync_engine 或后台任务来回放 pending
    ...
```

演示/要点：用于答辩现场触发回放、导出冲突或运行定制 SQL；前端消费：`AdminOperationsView.vue`, `AdminConsoleView.vue`。

6) dashboard 路由 / service（统计与聚合接口）
- 核心文件：`backend/apps/api_gateway/routers/dashboard.py`（路由），部分逻辑在 `sync_engine.run_periodic_sync`。
- 作用：对 daily-stats、sync-logs、inventory 等数据做聚合，供前端报表使用。

关键代码摘录：
```python
@router.get("/stats")
def get_dashboard_stats(session: Session = Depends(get_db_session)) -> Dict[str, Any]:
    total_users = session.execute(select(func.count(User.id))).scalar() or 0
    total_items = session.execute(select(func.count(Item.id))).scalar() or 0
    total_transactions = session.execute(select(func.count(Transaction.id))).scalar() or 0
    return {"users": {"total": total_users}, "items": {"total": total_items}, "transactions": {"total": total_transactions}}

@router.get("/daily-stats")
def get_daily_stats(limit: int = 7, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    stats = session.execute(select(DailyStat).order_by(DailyStat.stat_date.desc()).limit(limit)).scalars().all()
    return [{"date": stat.stat_date.isoformat(), "sync_success": stat.sync_success_count, "sync_conflicts": stat.sync_conflict_count} for stat in stats]
```

演示/要点：答辩时展示 `GET /api/v1/dashboard/stats` 返回的 JSON，配合前端 `DashboardView.vue` 的图表（SyncTrendChart/ConflictPieChart）。

---
文件已保存：`docs/module_ppt_snippets.md`（可直接复制至 PPT）。如需我把此文件提交到当前分支（创建 commit），回复“写入仓库”，我会提交并报告结果。若要我把每节单独做成 PPT 幻灯片（SVG 图像），回复“生成图表”。
