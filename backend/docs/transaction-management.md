# 事务管理与隔离级别配置文档

## 📋 目录

1. [概述](#概述)
2. [事务隔离级别设计](#事务隔离级别设计)
3. [ACID 保证](#acid-保证)
4. [并发控制策略](#并发控制策略)
5. [死锁检测与重试](#死锁检测与重试)
6. [性能优化](#性能优化)
7. [使用示例](#使用示例)
8. [监控与调试](#监控与调试)

---

## 概述

CampuSwap 多数据库同步系统采用分层事务管理策略,针对不同数据库特性配置最优隔离级别,确保跨库同步的一致性、并发性和性能。

### 核心特性

- ✅ **多级隔离**: 根据数据库类型和业务场景动态选择隔离级别
- ✅ **自动重试**: 检测死锁/序列化失败并自动重试(指数退避)
- ✅ **嵌套事务**: 支持 SAVEPOINT 实现细粒度事务控制
- ✅ **只读优化**: 显式声明只读事务减少锁开销
- ✅ **连接池管理**: 预配置连接池参数防止连接泄漏
- ✅ **超时保护**: 事务级和语句级超时防止长事务阻塞

---

## 事务隔离级别设计

### 隔离级别对比

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 并发性 | 适用场景 |
|---------|------|-----------|------|--------|---------|
| READ UNCOMMITTED | ❌ 可能 | ❌ 可能 | ❌ 可能 | ⭐⭐⭐⭐⭐ | 统计分析(容忍脏数据) |
| READ COMMITTED | ✅ 避免 | ❌ 可能 | ❌ 可能 | ⭐⭐⭐⭐ | **PostgreSQL 默认** |
| REPEATABLE READ | ✅ 避免 | ✅ 避免 | ❌ 可能 | ⭐⭐⭐ | **MySQL 默认** |
| SERIALIZABLE | ✅ 避免 | ✅ 避免 | ✅ 避免 | ⭐⭐ | 银行转账/库存扣减 |

### 各数据库配置策略

#### 1️⃣ MySQL / MariaDB: `REPEATABLE READ`

**选择理由**:
- InnoDB 默认隔离级别,经过充分优化
- 通过 **Next-Key Locking** 机制避免幻读
- 适合多表同步场景(如 users → items → transactions 级联更新)
- Gap Lock 防止并发插入导致的主键冲突

**配置代码**:
```python
# 连接时自动设置
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET SESSION innodb_lock_wait_timeout = 10;  # 锁等待超时 10 秒
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE';
```

**适用场景**:
- 跨表事务(如创建交易记录 + 更新库存)
- 数据同步任务(确保快照一致性)
- 审计日志写入(防止中间读取到不完整数据)

#### 2️⃣ PostgreSQL: `READ COMMITTED`

**选择理由**:
- **MVCC (Multi-Version Concurrency Control)** 优势:每个事务看到快照版本
- 减少锁竞争,提升并发性能(适合高频读写)
- 避免 REPEATABLE READ 下的序列化失败(serialization failure)
- PostgreSQL 的 READ COMMITTED 已足够强(比 MySQL 的严格)

**配置代码**:
```sql
SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET statement_timeout = '30s';  # 语句超时 30 秒
SET lock_timeout = '10s';       # 锁超时 10 秒
```

**适用场景**:
- 高并发 API 请求(如市场搜索、商品列表)
- 用户信息更新(不需要跨行一致性)
- 监控数据采集(每次读取最新状态)

#### 3️⃣ SQLite: `SERIALIZABLE`

**选择理由**:
- SQLite **单写入器模型**:同一时刻仅允许一个写事务
- SERIALIZABLE 不会额外降低性能(已经是串行写入)
- 提供最强一致性保证(适合本地缓存/测试环境)
- WAL 模式支持并发读取

**配置代码**:
```sql
PRAGMA journal_mode = WAL;       # Write-Ahead Logging
PRAGMA synchronous = NORMAL;     # 平衡性能与安全
PRAGMA busy_timeout = 10000;     # 锁等待 10 秒(毫秒)
```

**适用场景**:
- 单元测试(确保测试结果可重现)
- 本地开发环境
- 嵌入式部署(边缘计算节点)

---

## ACID 保证

### Atomicity (原子性)

**实现机制**:
- 使用 SQLAlchemy 的 `session.commit()` 确保全或无
- 异常时自动 `session.rollback()` 回滚所有操作
- 嵌套事务通过 `SAVEPOINT` 实现部分回滚

**代码示例**:
```python
from apps.core.transaction import with_transaction

@with_transaction("mysql")
def create_transaction_with_inventory_update(session: Session, data: dict):
    # 创建交易记录
    transaction = Transaction(**data)
    session.add(transaction)
    
    # 更新库存(原子操作)
    item = session.query(Item).filter_by(id=data['item_id']).with_for_update().one()
    item.status = 'sold'
    
    # 任何异常都会触发完整回滚
    session.flush()
```

### Consistency (一致性)

**保证方式**:
1. **数据库约束**: 外键、唯一索引、CHECK 约束
2. **触发器验证**: 如 `trg_items_before_update` 检查状态转换合法性
3. **应用层校验**: Pydantic 模型验证输入数据
4. **跨库一致性**: Redis Streams 保证事件有序传播

**触发器示例** (MySQL):
```sql
-- 确保价格非负
DELIMITER $$
CREATE TRIGGER trg_items_price_check BEFORE INSERT ON items
FOR EACH ROW
BEGIN
    IF NEW.price < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Price cannot be negative';
    END IF;
END$$
DELIMITER ;
```

### Isolation (隔离性)

**隔离级别与并发异常对照**:

| 异常类型 | MySQL (RR) | PostgreSQL (RC) | SQLite (S) |
|---------|-----------|----------------|-----------|
| 脏读 | ✅ 避免 | ✅ 避免 | ✅ 避免 |
| 不可重复读 | ✅ 避免 | ⚠️ 可能 | ✅ 避免 |
| 幻读 | ✅ 避免 (Next-Key Lock) | ⚠️ 可能 | ✅ 避免 |
| 写偏斜 | ⚠️ 可能 | ⚠️ 可能 | ✅ 避免 |

**处理不可重复读**:
```python
from apps.core.transaction import transactional_scope, IsolationLevel

# 需要快照一致性时临时提升隔离级别
with transactional_scope(session, isolation_level=IsolationLevel.REPEATABLE_READ):
    # 同一事务内多次读取保证看到相同版本
    items_v1 = session.query(Item).filter_by(status='active').all()
    time.sleep(1)  # 模拟其他事务修改数据
    items_v2 = session.query(Item).filter_by(status='active').all()
    assert items_v1 == items_v2  # REPEATABLE READ 保证一致
```

### Durability (持久性)

**持久化机制**:
1. **MySQL/MariaDB**: InnoDB `innodb_flush_log_at_trx_commit=1` (每次事务刷盘)
2. **PostgreSQL**: `synchronous_commit=on` (WAL 同步写入)
3. **SQLite**: `PRAGMA synchronous=FULL` (生产环境) / `NORMAL` (开发环境)

**配置验证**:
```bash
# MySQL
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';  # 应为 1

# PostgreSQL
SHOW synchronous_commit;  # 应为 on

# SQLite
PRAGMA synchronous;  # 应为 2 (FULL) 或 1 (NORMAL)
```

---

## 并发控制策略

### 1. 悲观锁 (Pessimistic Locking)

**适用场景**: 高冲突率场景(如库存扣减、余额更新)

**实现方式**:
```python
# FOR UPDATE 锁定行
item = session.query(Item).filter_by(id=item_id).with_for_update().one()
item.quantity -= 1  # 其他事务必须等待此事务提交

# FOR UPDATE NOWAIT (立即失败,不等待)
try:
    user = session.query(User).filter_by(id=user_id).with_for_update(nowait=True).one()
except OperationalError:
    raise ConflictError("Resource is locked by another transaction")
```

**注意事项**:
- 锁定顺序一致(按主键升序)避免死锁
- 尽快提交事务释放锁
- 使用 `SKIP LOCKED` 跳过已锁定行(任务队列场景)

### 2. 乐观锁 (Optimistic Locking)

**适用场景**: 低冲突率场景(如用户资料更新、商品描述编辑)

**实现方式**:
```python
from sqlalchemy import Column, Integer
from sqlalchemy.orm import version_id_col

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    version = Column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": version}  # 自动版本控制

# 更新时自动检查版本号
item = session.query(Item).filter_by(id=1).one()  # version = 5
item.title = "New Title"
session.commit()  # 自动 WHERE version = 5, SET version = 6

# 如果其他事务已提交(version = 6),此事务抛出 StaleDataError
```

### 3. 无锁读取 (Lock-Free Reads)

**实现方式**:
```python
from apps.core.transaction import read_only_transaction

# 只读事务不加锁,利用 MVCC
with read_only_transaction(session):
    items = session.query(Item).filter_by(status='active').all()
    # PostgreSQL: 读取快照版本,不阻塞写事务
    # MySQL: 一致性非锁定读(Consistent Non-Locking Read)
```

---

## 死锁检测与重试

### 死锁产生原因

**示例场景**:
```
事务 A: LOCK user_id=1 → WAIT FOR user_id=2
事务 B: LOCK user_id=2 → WAIT FOR user_id=1
```

### 自动重试机制

**配置参数** (`apps/core/transaction.py`):
```python
class TransactionConfig:
    MAX_RETRIES = 3          # 最大重试次数
    RETRY_DELAY = 0.1        # 初始延迟 100ms
    RETRY_BACKOFF = 2.0      # 指数退避倍数 (100ms → 200ms → 400ms)
```

**装饰器使用**:
```python
from apps.core.transaction import with_transaction

@with_transaction("mysql", max_retries=5)
def transfer_balance(session: Session, from_id: int, to_id: int, amount: float):
    # 按 ID 升序加锁(避免死锁)
    user_ids = sorted([from_id, to_id])
    users = session.query(User).filter(User.id.in_(user_ids)).with_for_update().all()
    
    # 死锁时自动重试
    users[0].balance -= amount
    users[1].balance += amount
```

**重试日志**:
```
2025-11-18 10:30:15 WARNING Retryable error in transfer_balance (attempt 1/5): 
    Deadlock found when trying to get lock; try restarting transaction
2025-11-18 10:30:15.200 INFO Retry succeeded on attempt 2
```

### 死锁预防策略

1. **锁定顺序一致**: 总是按主键升序加锁
2. **减少事务大小**: 拆分长事务为多个小事务
3. **使用索引**: 避免表锁升级为全表扫描
4. **超时机制**: `innodb_lock_wait_timeout=10` 避免无限等待

---

## 性能优化

### 1. 连接池配置

**参数说明** (`apps/core/transaction.py`):
```python
POOL_SIZE = 10           # 常驻连接数
MAX_OVERFLOW = 20        # 峰值时临时连接数
POOL_TIMEOUT = 30        # 获取连接超时(秒)
POOL_RECYCLE = 3600      # 连接回收时间(秒),防止 "MySQL has gone away"
```

**SQLite 特殊处理**:
```python
# SQLite 单写入器,使用独占连接池
"sqlite": create_engine(
    settings.sqlite_dsn,
    pool_size=1,        # 单连接
    max_overflow=0,     # 无溢出
)
```

### 2. 事务超时

**MySQL/MariaDB**:
```sql
SET SESSION innodb_lock_wait_timeout = 10;  -- 锁等待 10 秒超时
```

**PostgreSQL**:
```sql
SET statement_timeout = '30s';  -- 单条语句 30 秒超时
SET lock_timeout = '10s';       -- 锁等待 10 秒超时
```

### 3. 索引优化

**覆盖索引**:
```sql
-- 避免回表查询
CREATE INDEX idx_items_status_category ON items(status, category_id) INCLUDE (price, title);

-- 查询完全使用索引
SELECT price, title FROM items WHERE status = 'active' AND category_id = 5;
```

### 4. 批量操作

**使用 `bulk_insert_mappings` 减少往返**:
```python
# ❌ 慢:逐条插入
for item in items:
    session.add(Item(**item))
session.commit()  # N 次数据库往返

# ✅ 快:批量插入
session.bulk_insert_mappings(Item, items)
session.commit()  # 1 次数据库往返
```

---

## 使用示例

### 示例 1: 创建交易(跨表事务)

```python
from apps.core.database import db_manager
from apps.core.transaction import with_transaction
from apps.core.models import Transaction, Item

@with_transaction("mysql", max_retries=3)
def create_transaction_and_update_item(
    session,
    buyer_id: int,
    seller_id: int,
    item_id: int,
    price: float,
):
    """
    创建交易记录并更新商品状态(原子操作)
    
    隔离级别: REPEATABLE READ (MySQL 默认)
    锁策略: 悲观锁 (FOR UPDATE)
    重试: 自动检测死锁并重试
    """
    # 1. 锁定商品(防止重复售卖)
    item = session.query(Item).filter_by(id=item_id).with_for_update().one()
    
    if item.status != 'active':
        raise ValueError(f"Item {item_id} is not available for sale")
    
    # 2. 创建交易记录
    transaction = Transaction(
        buyer_id=buyer_id,
        seller_id=seller_id,
        item_id=item_id,
        amount=price,
        status='pending',
    )
    session.add(transaction)
    
    # 3. 更新商品状态
    item.status = 'sold'
    item.sold_at = datetime.utcnow()
    
    # 4. 提交(触发器自动更新 sync_version, audit_logs)
    session.flush()
    
    return transaction.id

# 使用
with db_manager.session_scope("mysql") as session:
    tx_id = create_transaction_and_update_item(
        session=session,
        buyer_id=10,
        seller_id=5,
        item_id=123,
        price=99.99,
    )
    print(f"Transaction created: {tx_id}")
```

### 示例 2: 嵌套事务(SAVEPOINT)

```python
from apps.core.transaction import transactional_scope

def process_bulk_orders(session, orders: list):
    """
    批量处理订单,失败订单回滚但不影响成功订单
    """
    results = []
    
    for order in orders:
        # 使用 SAVEPOINT 实现部分回滚
        with transactional_scope(session, savepoint=True):
            try:
                # 处理单个订单
                item = session.query(Item).filter_by(id=order['item_id']).one()
                item.status = 'reserved'
                results.append({'order_id': order['id'], 'status': 'success'})
            except Exception as e:
                # 仅回滚当前订单,不影响其他订单
                results.append({'order_id': order['id'], 'status': 'failed', 'error': str(e)})
    
    return results
```

### 示例 3: 只读事务优化

```python
from apps.core.transaction import read_only_transaction

def get_market_statistics(session):
    """
    市场统计查询(只读事务,无锁开销)
    """
    with read_only_transaction(session):
        active_count = session.query(Item).filter_by(status='active').count()
        avg_price = session.query(func.avg(Item.price)).scalar()
        
        return {
            'active_items': active_count,
            'average_price': float(avg_price or 0),
        }
```

---

## 监控与调试

### 1. 事务指标

**查看统计**:
```python
from apps.core.transaction import transaction_metrics

stats = transaction_metrics.get_stats()
print(stats)
# {
#     'total_transactions': 1523,
#     'total_retries': 47,
#     'total_deadlocks': 12,
#     'avg_duration_seconds': 0.085,
#     'retry_rate': 0.031
# }
```

### 2. 数据库锁监控

**MySQL 锁等待查询**:
```sql
-- 查看当前锁等待
SELECT 
    r.trx_id AS waiting_trx,
    r.trx_mysql_thread_id AS waiting_thread,
    TIMESTAMPDIFF(SECOND, r.trx_wait_started, NOW()) AS wait_time,
    r.trx_query AS waiting_query,
    b.trx_id AS blocking_trx,
    b.trx_mysql_thread_id AS blocking_thread,
    b.trx_query AS blocking_query
FROM information_schema.innodb_lock_waits w
INNER JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
INNER JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id;
```

**PostgreSQL 锁查询**:
```sql
-- 查看阻塞会话
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

### 3. 慢查询日志

**MySQL 配置**:
```ini
# my.cnf
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1  # 记录超过 1 秒的查询
log_queries_not_using_indexes = 1
```

**PostgreSQL 配置**:
```ini
# postgresql.conf
log_min_duration_statement = 1000  # 记录超过 1 秒的查询
log_lock_waits = on                # 记录锁等待
deadlock_timeout = 1s              # 死锁检测超时
```

---

## 最佳实践总结

### ✅ DO

1. **使用装饰器**: `@with_transaction` 自动处理提交/回滚
2. **按序加锁**: 避免死锁,总是按主键升序锁定
3. **快速事务**: 事务内仅包含必要的数据库操作
4. **显式隔离级别**: 特殊场景临时提升隔离级别
5. **监控指标**: 定期检查 `transaction_metrics` 发现异常

### ❌ DON'T

1. **长事务**: 避免在事务内调用外部 API / 执行耗时计算
2. **嵌套提交**: 不要在装饰器内手动 `commit()`
3. **忽略异常**: 捕获异常后必须重新抛出或记录
4. **过度加锁**: 优先使用乐观锁,仅高冲突场景使用悲观锁
5. **硬编码隔离级别**: 使用 `TransactionConfig` 统一配置

---

## 参考资料

- [MySQL InnoDB 事务模型](https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-model.html)
- [PostgreSQL MVCC 详解](https://www.postgresql.org/docs/current/mvcc.html)
- [SQLite WAL 模式](https://www.sqlite.org/wal.html)
- [SQLAlchemy Session 管理](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)

---

**文档版本**: v1.0  
**最后更新**: 2025-11-18  
**维护者**: CampuSwap 开发团队
