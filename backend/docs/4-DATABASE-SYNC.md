# 四库同步与事务管理 - 完整实现文档

## 📋 概述

CampuSwap 系统中**所有数据库操作**都采用统一的四库同步机制和事务管理策略,确保:

✅ **数据一致性**: 所有写操作自动同步到 MySQL/MariaDB/PostgreSQL/SQLite  
✅ **事务完整性**: ACID 保证,自动提交/回滚  
✅ **并发安全**: 死锁检测与自动重试  
✅ **隔离优化**: 针对不同数据库的最优隔离级别  
✅ **冲突处理**: 自动检测并记录同步冲突

---

## 🏗️ 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                   API 层 (FastAPI)                      │
│  inventory_service / trade_service / sync_service       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          DatabaseOperationService (统一服务)            │
│  - insert_with_sync()                                   │
│  - update_with_sync()                                   │
│  - delete_with_sync()                                   │
│  - verify_sync_consistency()                            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐     ┌──────────────────┐
│ TransactionMgr   │     │   SyncEngine     │
│ - @with_trans... │     │ - publish_event()│
│ - SAVEPOINT      │     │ - replicate()    │
│ - 自动重试        │     │ - Redis Streams  │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ▼                        ▼
┌─────────────────────────────────────────┐
│        DatabaseManager (连接池)         │
│  MySQL / MariaDB / PostgreSQL / SQLite  │
└─────────────────────────────────────────┘
```

---

## 🔄 四库同步机制

### 1. 同步流程

所有写操作(INSERT/UPDATE/DELETE)按以下流程执行:

```python
# 步骤 1: 在主库(MySQL)执行操作(带事务管理)
with db_manager.session_scope("mysql") as session:
    # 使用 @with_transaction 装饰器自动处理事务
    result = db_operation_service.insert_with_sync(
        session=session,
        table='items',
        data={...},
        sync_to_all=True,  # 启用四库同步
    )

# 步骤 2: 自动创建同步事件
event = SyncEvent(
    table='items',
    action='insert',
    payload={'statement': sql, 'params': data},
    origin='mysql',
    occurred_at=datetime.utcnow(),
    sync_version=1,
)

# 步骤 3: 立即同步到其他数据库(同步模式)
for target_db in ['mariadb', 'postgres', 'sqlite']:
    with db_manager.session_scope(target_db) as session:
        session.execute(sql, params)
        session.commit()  # 独立事务

# 步骤 4: 发布到 Redis Streams(异步模式,供 worker 重试)
redis.xadd('campuswap:sync:events', event.as_message())
```

### 2. 同步模式对比

| 模式 | 时机 | 用途 | 优点 | 缺点 |
|-----|------|------|------|------|
| **同步模式** | 操作执行时立即同步 | 关键业务(交易/库存) | 强一致性 | 延迟较高 |
| **异步模式** | Redis Streams + Worker | 日志/统计/审计 | 低延迟 | 最终一致性 |

**当前实现**: 混合模式
- INSERT/UPDATE/DELETE 使用**同步模式**(立即同步到四库)
- 同时发布到 Redis Streams 作为**备份机制**(Worker 可重试失败的同步)

---

## 🔒 事务管理策略

### 1. 隔离级别配置

| 数据库 | 隔离级别 | 配置原因 |
|-------|---------|---------|
| **MySQL** | `REPEATABLE READ` | InnoDB 默认,Next-Key Lock 防幻读,适合多表事务 |
| **MariaDB** | `REPEATABLE READ` | 与 MySQL 兼容,保持一致性 |
| **PostgreSQL** | `READ COMMITTED` | MVCC 优势,高并发性能优,减少序列化失败 |
| **SQLite** | `SERIALIZABLE` | 单写入器模型,最强一致性,无额外开销 |

### 2. 事务特性

#### 自动提交/回滚
```python
@with_transaction("mysql", max_retries=3)
def create_item(session: Session, data: dict):
    # 业务逻辑
    ...
    # 成功时自动 commit
    # 失败时自动 rollback
```

#### 死锁检测与重试
```python
# 配置
MAX_RETRIES = 3          # 最大重试次数
RETRY_DELAY = 0.1        # 初始延迟 100ms
RETRY_BACKOFF = 2.0      # 指数退避倍数

# 重试序列: 100ms → 200ms → 400ms
```

#### 嵌套事务(SAVEPOINT)
```python
# 主事务
with db_manager.session_scope("mysql") as session:
    # 子事务 1(成功)
    with transactional_scope(session, savepoint=True):
        process_order_1()  # COMMIT
    
    # 子事务 2(失败,仅回滚此部分)
    with transactional_scope(session, savepoint=True):
        process_order_2()  # ROLLBACK TO SAVEPOINT
    
    # 主事务继续,子事务 1 的结果保留
```

---

## 📝 API 使用示例

### 示例 1: 创建商品(四库同步)

**请求**:
```http
POST /inventory/items
Content-Type: application/json

{
  "seller_id": 123,
  "title": "iPhone 13 Pro",
  "category_id": 5,
  "price": 4999.0,
  "description": "95新,无磕碰",
  "currency": "CNY"
}
```

**响应**:
```json
{
  "id": 456,
  "title": "iPhone 13 Pro",
  "status": "draft",
  "price": 4999.0,
  "synced_to": ["mysql", "mariadb", "postgres", "sqlite"]
}
```

**内部执行**:
1. ✅ MySQL: INSERT 成功 (主库,REPEATABLE READ)
2. ✅ MariaDB: INSERT 成功 (REPEATABLE READ)
3. ✅ PostgreSQL: INSERT 成功 (READ COMMITTED)
4. ✅ SQLite: INSERT 成功 (SERIALIZABLE)
5. 📤 Redis Stream: 事件已发布 (Worker 备份)

---

### 示例 2: 更新商品(带冲突检测)

**请求**:
```http
PUT /inventory/items/456
Content-Type: application/json

{
  "seller_id": 123,
  "title": "iPhone 13 Pro (降价)",
  "category_id": 5,
  "price": 4499.0,
  "description": "95新,无磕碰,急售",
  "currency": "CNY"
}
```

**响应**:
```json
{
  "id": 456,
  "message": "Item updated successfully",
  "synced_to": ["mysql", "mariadb", "postgres", "sqlite"]
}
```

**冲突处理**:
- 如果某个数据库同步失败(如记录已被删除)
- 自动记录到 `conflict_records` 表
- 发送邮件告警给管理员
- 其他数据库继续同步

---

### 示例 3: 创建交易(跨表事务)

**请求**:
```http
POST /trade/transactions
Content-Type: application/json

{
  "buyer_id": 789,
  "seller_id": 123,
  "item_id": 456,
  "amount": 4499.0
}
```

**响应**:
```json
{
  "transaction_id": 1001,
  "item_id": 456,
  "buyer_id": 789,
  "seller_id": 123,
  "amount": 4499.0,
  "status": "pending",
  "item_status": "sold",
  "synced_to": ["mysql", "mariadb", "postgres", "sqlite"],
  "message": "Transaction created and item marked as sold across all databases"
}
```

**ACID 保证**:
1. **原子性**: 创建交易 + 更新商品状态 = 一个事务
2. **一致性**: 触发器自动更新 `sync_version` 和 `audit_logs`
3. **隔离性**: REPEATABLE READ 防止并发修改
4. **持久性**: 四个数据库全部提交后才返回

---

### 示例 4: 验证同步一致性

**请求**:
```http
GET /inventory/items/456/sync-status
```

**响应**:
```json
{
  "item_id": 456,
  "consistent": true,
  "databases_checked": 4,
  "records": {
    "mysql": {
      "id": 456,
      "title": "iPhone 13 Pro (降价)",
      "price": 4499.0,
      "status": "sold",
      "sync_version": 3
    },
    "mariadb": {
      "id": 456,
      "title": "iPhone 13 Pro (降价)",
      "price": 4499.0,
      "status": "sold",
      "sync_version": 3
    },
    "postgres": {
      "id": 456,
      "title": "iPhone 13 Pro (降价)",
      "price": 4499.0,
      "status": "sold",
      "sync_version": 3
    },
    "sqlite": {
      "id": 456,
      "title": "iPhone 13 Pro (降价)",
      "price": 4499.0,
      "status": "sold",
      "sync_version": 3
    }
  }
}
```

---

### 示例 5: 获取同步状态

**请求**:
```http
GET /inventory/sync-status
```

**响应**:
```json
{
  "primary_database": "mysql",
  "target_databases": ["mysql", "mariadb", "postgres", "sqlite"],
  "database_status": {
    "mysql": {
      "status": "online",
      "isolation_level": "REPEATABLE READ"
    },
    "mariadb": {
      "status": "online",
      "isolation_level": "REPEATABLE READ"
    },
    "postgres": {
      "status": "online",
      "isolation_level": "READ COMMITTED"
    },
    "sqlite": {
      "status": "online",
      "isolation_level": "SERIALIZABLE"
    }
  }
}
```

---

## 🛠️ 核心代码实现

### 1. 统一数据库操作服务

**文件**: `backend/apps/services/db_operations.py`

```python
class DatabaseOperationService:
    """统一数据库操作服务,自动处理四库同步和事务管理"""
    
    TARGET_DATABASES = ["mysql", "mariadb", "postgres", "sqlite"]
    PRIMARY_DATABASE = "mysql"
    
    @with_transaction(PRIMARY_DATABASE, max_retries=3)
    def insert_with_sync(self, session, table, data, sync_to_all=True):
        """插入记录并同步到所有数据库"""
        # 1. 在主库执行
        sql = f"INSERT INTO {table} (...) VALUES (...)"
        result = session.execute(text(sql), data)
        
        # 2. 同步到其他数据库
        if sync_to_all:
            event = SyncEvent(table, 'insert', {...})
            self.sync_engine.replicate(event, other_targets)
            self.sync_engine.publish_event(event)
        
        return result.lastrowid
```

### 2. 事务管理装饰器

**文件**: `backend/apps/core/transaction.py`

```python
@with_transaction("mysql", max_retries=3)
def create_order(session: Session, ...):
    """
    自动处理:
    - 设置隔离级别
    - 提交/回滚
    - 死锁重试(指数退避)
    """
    # 业务逻辑
    ...
```

### 3. 同步引擎

**文件**: `backend/apps/core/sync_engine.py`

```python
def replicate(self, event: SyncEvent, targets: Iterable[str]):
    """将事件复制到目标数据库"""
    for target in targets:
        with db_manager.session_scope(target) as session:
            session.execute(event.payload['statement'], params)
            # 检测冲突
            if result.rowcount == 0:
                self._record_conflict(event, target)
```

---

## 📊 性能优化

### 1. 连接池配置

```python
# MySQL/MariaDB/PostgreSQL
POOL_SIZE = 10           # 常驻连接
MAX_OVERFLOW = 20        # 峰值临时连接
POOL_RECYCLE = 3600      # 连接回收(防止 MySQL gone away)

# SQLite(单写入器)
POOL_SIZE = 1            # 独占连接
MAX_OVERFLOW = 0         # 无溢出
```

### 2. 批量操作优化

```python
# ❌ 慢: 逐条同步
for item in items:
    db_operation_service.insert_with_sync(session, 'items', item)

# ✅ 快: 批量同步
db_operation_service.bulk_insert_with_sync('items', items)
```

### 3. 读写分离

```python
# 写操作: 主库 + 四库同步
db_operation_service.insert_with_sync(session, ...)

# 读操作: 仅从主库读取(避免同步延迟)
with db_manager.session_scope("mysql") as session:
    items = session.query(Item).all()
```

---

## 🔍 监控与调试

### 1. 查看事务指标

```python
from apps.core.transaction import transaction_metrics

stats = transaction_metrics.get_stats()
# {
#     'total_transactions': 1523,
#     'total_retries': 47,
#     'total_deadlocks': 12,
#     'retry_rate': 0.031,
#     'avg_duration_seconds': 0.085
# }
```

### 2. 同步冲突查询

```sql
-- 查看未解决的冲突
SELECT * FROM conflict_records 
WHERE resolved = FALSE 
ORDER BY created_at DESC;

-- 冲突统计
SELECT 
    table_name,
    COUNT(*) as conflict_count,
    MIN(created_at) as first_conflict,
    MAX(created_at) as last_conflict
FROM conflict_records
GROUP BY table_name;
```

### 3. 事务日志

```sql
-- 查看最近的同步日志
SELECT * FROM sync_logs 
ORDER BY started_at DESC 
LIMIT 20;

-- 每日统计
SELECT 
    stat_date,
    sync_success_count,
    sync_conflict_count,
    (sync_success_count * 100.0 / (sync_success_count + sync_conflict_count)) as success_rate
FROM daily_stats
ORDER BY stat_date DESC;
```

---

## ✅ 最佳实践总结

### DO ✅

1. **使用统一服务**: 所有数据库操作通过 `db_operation_service`
2. **启用四库同步**: `sync_to_all=True` (默认)
3. **验证一致性**: 关键操作后调用 `verify_sync_consistency()`
4. **监控指标**: 定期检查 `transaction_metrics` 和冲突记录
5. **处理冲突**: 及时处理 `conflict_records` 表中的记录

### DON'T ❌

1. **直接操作单个数据库**: 绕过同步机制会导致数据不一致
2. **忽略事务**: 所有写操作必须在事务中执行
3. **长事务**: 避免在事务内调用外部 API 或长时间计算
4. **硬编码数据库**: 使用 `PRIMARY_DATABASE` 常量
5. **忽略冲突告警**: 邮件告警需及时处理

---

## 📚 相关文档

- [事务管理详细文档](transaction-management.md)
- [数据库编程对象](../sql/README.md)
- [同步引擎实现](../apps/core/sync_engine.py)
- [统一操作服务](../apps/services/db_operations.py)

---

**文档版本**: v1.0  
**最后更新**: 2025-11-18  
**状态**: ✅ 生产就绪
