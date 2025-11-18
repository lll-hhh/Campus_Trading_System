# CampuSwap Backend

CampuSwap 后端采用 FastAPI + SQLAlchemy 微服务架构,支持多数据库(MySQL/MariaDB/PostgreSQL/SQLite)同步与事务管理。

## 核心服务

- `api_gateway`: 统一入口、鉴权、路由与汇总 API
- `inventory_service`: 分类、物品、收藏、评论模块
- `trade_service`: 报价、交易、支付、配送模块
- `sync_service`: 多库同步、冲突检测、统计
- `ai_service`: 定价建议、风险识别、语义搜索
- `monitoring_service`: 报表、告警、健康检查

## 核心特性

✅ **多数据库支持**: MySQL/MariaDB/PostgreSQL/SQLite 四库同步  
✅ **事务管理**: 可配置隔离级别、自动重试、死锁检测  
✅ **数据库编程**: 触发器、存储过程、函数、视图、分区表  
✅ **Redis Streams**: 事件驱动的跨库同步机制  
✅ **连接池优化**: 预配置参数,支持高并发场景  
✅ **完整文档**: SQL 对象、事务管理、API 使用说明

## 目录结构

```
backend/
  apps/
    api_gateway/          # API 网关
      routers/
        auth.py           # 认证与授权
        database.py       # 数据库管理 API
        market.py         # 市场搜索
        sync.py           # 同步控制
    core/
      models/             # SQLAlchemy ORM 模型
      database.py         # 数据库连接管理
      transaction.py      # 事务管理工具 ⭐ NEW
      security.py         # JWT 鉴权
      sync_engine.py      # 同步引擎
    services/
      db_initializer.py   # 数据库初始化服务 ⭐ NEW
      sync_worker.py      # 同步 Worker
  sql/
    mysql_schema.sql      # MySQL 数据库对象 ⭐ NEW
    mariadb_schema.sql    # MariaDB 数据库对象 ⭐ NEW
    postgres_schema.sql   # PostgreSQL 数据库对象 ⭐ NEW
    sqlite_schema.sql     # SQLite 数据库对象 ⭐ NEW
    README.md             # SQL 对象文档
  docs/
    transaction-management.md  # 事务管理文档 ⭐ NEW
  tests/
```

## 开发环境

```bash
# 安装依赖
poetry install

# 启动 API Gateway
poetry run uvicorn apps.api_gateway.main:app --reload --port 8000

# 启动 Sync Worker(独立终端)
poetry run python -m apps.services.sync_worker
```

### 系统依赖

`mysqlclient` 需要系统级头文件与工具,请在 Debian/Ubuntu 上先安装:

```bash
sudo apt update
sudo apt install -y build-essential pkg-config libmariadb-dev libpq-dev
```

### 环境变量

创建 `.env` 文件(参考 `.env.example`):

```bash
# 数据库连接
MYSQL_DSN=mysql+mysqldb://root:campuswap@localhost:3306/campuswap_mysql
MARIADB_DSN=mysql+mysqldb://root:campuswap@localhost:3307/campuswap_mariadb
POSTGRES_DSN=postgresql+psycopg2://postgres:campuswap@localhost:5432/campuswap_postgres
SQLITE_DSN=sqlite:///./campuswap.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Sync Worker
SYNC_STREAM_GROUP=campuswap-sync-group
SYNC_CONSUMER_NAME=worker-1

# JWT
SECRET_KEY=your-secret-key-change-in-production
```

## Docker 部署

### 快速启动

```bash
# 启动所有服务(MySQL/MariaDB/PostgreSQL/Redis + Backend)
docker compose up -d

# 查看日志
docker compose logs -f api-gateway
docker compose logs -f sync-worker

# 停止服务
docker compose down
```

### 数据库初始化

后端启动时自动执行 SQL 脚本(触发器、存储过程、函数):

```python
# apps/api_gateway/main.py
@app.on_event("startup")
async def startup_event():
    from apps.services.db_initializer import initialize_databases
    await initialize_databases()  # 自动初始化所有数据库
```

手动初始化 API:

```bash
# 初始化所有数据库
curl -X POST http://localhost:8000/admin/database/initialize

# 初始化单个数据库
curl -X POST http://localhost:8000/admin/database/initialize/mysql

# 验证数据库对象
curl http://localhost:8000/admin/database/verify/mysql
```

## 事务管理

### 快速开始

```python
from apps.core.transaction import with_transaction
from apps.core.database import db_manager

@with_transaction("mysql", max_retries=3)
def create_item(session, seller_id: int, title: str, price: float):
    item = Item(seller_id=seller_id, title=title, price=price)
    session.add(item)
    session.flush()
    return item.id

# 使用
with db_manager.session_scope("mysql") as session:
    item_id = create_item(session=session, seller_id=1, title="iPhone", price=4999.0)
```

### 隔离级别配置

各数据库默认隔离级别(已优化):

| 数据库 | 隔离级别 | 理由 |
|-------|---------|------|
| MySQL/MariaDB | `REPEATABLE READ` | InnoDB 默认,Next-Key Lock 防幻读 |
| PostgreSQL | `READ COMMITTED` | MVCC 优势,减少锁竞争 |
| SQLite | `SERIALIZABLE` | 单写入器模型,最强一致性 |

详细文档: [docs/transaction-management.md](docs/transaction-management.md)

### 核心特性

✅ **自动重试**: 检测死锁/序列化失败自动重试(指数退避)  
✅ **嵌套事务**: SAVEPOINT 支持部分回滚  
✅ **只读优化**: 显式声明只读事务减少锁开销  
✅ **死锁预防**: 按主键升序加锁避免循环等待  
✅ **连接池**: 预配置 `pool_size=10`, `max_overflow=20`  
✅ **超时保护**: 事务 30s、锁 10s 超时防止长时间阻塞

## 数据库编程对象

### 触发器

自动维护审计日志和同步版本:

```sql
-- 用户插入触发器(审计日志)
CREATE TRIGGER trg_users_after_insert AFTER INSERT ON users
FOR EACH ROW
INSERT INTO audit_logs (table_name, operation, record_id, changed_data)
VALUES ('users', 'INSERT', NEW.id, JSON_OBJECT('email', NEW.email));

-- 商品更新触发器(同步版本)
CREATE TRIGGER trg_items_after_update AFTER UPDATE ON items
FOR EACH ROW
SET NEW.sync_version = OLD.sync_version + 1;
```

### 存储过程

```sql
-- 表同步存储过程
CALL sp_sync_table_data('items', 1, 100);  -- 同步 items 表第 1-100 条

-- 用户信誉计算
CALL sp_calculate_user_reputation(123);    -- 计算用户 123 的信誉分

-- 冲突清理(定时任务)
CALL sp_cleanup_old_conflicts(30);         -- 清理 30 天前的冲突记录
```

### 函数

```sql
-- 查询用户交易次数
SELECT fn_get_user_transaction_count(123);  -- 返回用户 123 的交易数

-- 分类平均价格
SELECT fn_avg_price_by_category('electronics');

-- 版本冲突检测
SELECT fn_check_version_conflict('items', 456, 10);  -- 检查 items 表记录 456 版本是否为 10
```

### 视图

```sql
-- 活跃商品列表
SELECT * FROM vw_active_listings WHERE category = 'electronics' LIMIT 10;

-- 交易摘要
SELECT * FROM vw_transaction_summary WHERE buyer_id = 123;
```

详细文档: [sql/README.md](sql/README.md)

## 角色与权限

- `market_admin`：可触发手动同步、查看/处理冲突、访问高级筛选的全部字段。
- `trader`：可使用高级筛选、查看同步状态（但不可处理冲突）。

在 `users` / `roles` / `user_roles` 表中插入对应数据即可。当管理员登录 `/auth/login` 后将收到带角色声明的 JWT，前端会根据角色动态展示按钮。

## 邮件告警配置

设置以下环境变量即可启用同步冲突邮件提醒：

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_USE_TLS`（默认 `true`）
- `ALERT_SENDER`（可选）
- `ALERT_RECIPIENTS`（逗号分隔列表）

当同步冲突被记录时，系统会向上述收件人发送告警，并在管理端提供“冲突处理”接口。

## 代码规范

- `poetry run black .`
- `poetry run isort .`
- `poetry run flake8`
- `poetry run mypy apps`
- `poetry run pytest`

所有公共函数/类需编写 Google-style docstring，并遵循 zh-google-styleguide。
