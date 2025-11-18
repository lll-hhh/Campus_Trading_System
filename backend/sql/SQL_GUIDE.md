# 📊 数据库SQL脚本说明

## 📁 文件结构

```
sql/
├── README.md                          # 本文档
├── mysql_complete_schema.sql          # MySQL完整schema
├── postgres_complete_schema.sql       # PostgreSQL完整schema  
├── mariadb_complete_schema.sql        # MariaDB完整schema
└── sqlite_complete_schema.sql         # SQLite完整schema
```

## 🎯 四库同步架构

本系统采用**四数据库同步架构**,确保数据一致性和高可用性:

- **MySQL** - 主数据库,适合高并发读写
- **PostgreSQL** - 辅助数据库,提供高级查询功能
- **MariaDB** - MySQL兼容数据库,增强特性
- **SQLite** - 轻量级数据库,用于本地开发和测试

## 📋 数据表清单

### 核心业务表 (9张)

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `users` | 用户表 | 用户名、邮箱、信用分、评分 |
| `categories` | 商品分类 | 名称、标识slug |
| `items` | 商品表 | 标题、价格、成色、状态 |
| `item_images` | 商品图片 | 图片URL、排序 |
| `comments` | 评论表 | 内容、回复关系 |
| `transactions` | 交易表 | 买卖双方、金额、状态、评价 |
| `messages` | 消息表 | 发送者、接收者、内容 |
| `favorites` | 收藏表 | 用户-商品关联 |
| `reports` | 举报表 | 举报类型、原因、状态 |

### 系统管理表 (3张)

| 表名 | 说明 | 用途 |
|------|------|------|
| `audit_logs` | 审计日志 | 记录所有操作历史 |
| `conflict_records` | 同步冲突 | 四库同步冲突处理 |
| `system_configs` | 系统配置 | 平台参数配置 |

**总计:** 12张核心表

## 🔧 触发器清单

### 1. 更新时间戳触发器
- `trg_users_updated_at` - 用户表更新时间
- `trg_items_updated_at` - 商品表更新时间
- `trg_comments_updated_at` - 评论表更新时间

### 2. 业务逻辑触发器
- `trg_after_user_insert` - 用户创建审计日志
- `trg_after_comment_insert` - 评论后更新商品咨询量
- `trg_after_favorite_insert/delete` - 收藏后更新收藏量
- `trg_after_transaction_complete` - 交易完成后更新统计
- `trg_after_transaction_rating` - 评分更新后重算用户评分

### 3. 全文搜索触发器 (SQLite)
- `trg_items_fts_insert/update/delete` - 同步FTS索引

**总计:** 10+ 触发器

## 📦 存储过程/函数

### MySQL/MariaDB 存储过程

#### 1. `sp_create_transaction` - 创建交易
```sql
CALL sp_create_transaction(
    p_item_id BIGINT,        -- 商品ID
    p_buyer_id BIGINT,       -- 买家ID
    p_buyer_contact VARCHAR, -- 买家联系方式
    OUT p_transaction_id,    -- 返回:交易ID
    OUT p_error_msg          -- 返回:错误消息
);
```

**功能:**
- 检查商品状态(必须available)
- 创建交易记录
- 更新商品状态为reserved
- 事务保证原子性

#### 2. `sp_get_user_stats` - 获取用户统计
```sql
CALL sp_get_user_stats(p_user_id BIGINT);
```

**返回字段:**
- 信用分、评分
- 销售/购买总数
- 在售商品数
- 收藏数、交易数

#### 3. `sp_search_items` - 搜索商品
```sql
CALL sp_search_items(
    p_keyword VARCHAR,       -- 关键词
    p_category_id BIGINT,    -- 分类ID
    p_min_price DECIMAL,     -- 最低价
    p_max_price DECIMAL,     -- 最高价
    p_condition_type VARCHAR,-- 成色
    p_offset INT,            -- 分页偏移
    p_limit INT              -- 每页数量
);
```

### PostgreSQL 函数

#### 1. `create_transaction()` - 创建交易
```sql
SELECT * FROM create_transaction(
    p_item_id BIGINT,
    p_buyer_id BIGINT,
    p_buyer_contact VARCHAR
);
```

返回: `(transaction_id, error_msg)`

#### 2. `get_user_stats()` - 用户统计
```sql
SELECT * FROM get_user_stats(p_user_id BIGINT);
```

#### 3. `search_items()` - 搜索商品
```sql
SELECT * FROM search_items(
    p_keyword TEXT,
    p_category_id BIGINT,
    p_min_price DECIMAL,
    p_max_price DECIMAL,
    p_condition_type VARCHAR,
    p_offset INTEGER,
    p_limit INTEGER
);
```

## 📊 视图清单

### 1. `v_item_details` - 商品详情视图
展示商品完整信息,包含:
- 商品基本信息
- 卖家信息(用户名、头像、评分)
- 分类信息
- 封面图

### 2. `v_transaction_stats` - 交易统计视图
按日期统计:
- 总交易数
- 完成交易数
- 取消交易数
- 总金额、平均金额

### 3. `v_user_activity` - 用户活跃度视图
展示用户活跃指标:
- 在售商品数
- 评论数
- 消息数
- 最后活跃时间

## 🚀 使用方法

### 1. MySQL/MariaDB 初始化

```bash
# MySQL
mysql -u root -p < mysql_complete_schema.sql

# MariaDB
mysql -u root -p < mariadb_complete_schema.sql
```

### 2. PostgreSQL 初始化

```bash
psql -U postgres -d campus_trading < postgres_complete_schema.sql
```

### 3. SQLite 初始化

```bash
sqlite3 campus_trading.db < sqlite_complete_schema.sql
```

### 4. Docker环境初始化

```bash
# 使用docker-compose自动初始化所有数据库
docker-compose up -d
```

## 🔐 事务示例

### 1. 创建交易事务 (MySQL)

```sql
START TRANSACTION;

-- 锁定商品
SELECT id, status FROM items WHERE id = 123 FOR UPDATE;

-- 创建交易
INSERT INTO transactions (item_id, buyer_id, seller_id, ...)
VALUES (123, 456, 789, ...);

-- 更新商品状态
UPDATE items SET status = 'reserved' WHERE id = 123;

COMMIT;
```

### 2. 批量导入商品 (PostgreSQL)

```sql
BEGIN;

-- 插入商品
INSERT INTO items (title, price, seller_id, category_id)
SELECT * FROM json_populate_recordset(null::items, '[
    {"title": "iPhone 13", "price": 3999.00, "seller_id": 1, "category_id": 2},
    {"title": "MacBook Pro", "price": 9999.00, "seller_id": 1, "category_id": 2}
]');

-- 插入图片
INSERT INTO item_images (item_id, image_url, is_cover)
SELECT id, '/images/cover.jpg', true FROM items WHERE seller_id = 1;

COMMIT;
```

### 3. 数据同步事务

```sql
-- 检测冲突并记录
BEGIN;

UPDATE items SET sync_version = sync_version + 1 
WHERE id = 123 AND sync_version = 5;

IF ROW_COUNT() = 0 THEN
    -- 版本冲突,记录到冲突表
    INSERT INTO conflict_records (table_name, record_id, conflict_type, ...)
    VALUES ('items', 123, 'version_mismatch', ...);
    ROLLBACK;
ELSE
    COMMIT;
END IF;
```

## 📈 性能优化

### 1. 索引策略

- **单列索引:** 常用查询字段 (status, created_at, price)
- **复合索引:** 多字段组合查询 (seller_id + status)
- **全文索引:** 商品标题、描述搜索
- **唯一索引:** 用户名、邮箱

### 2. 分区策略

**交易表分区 (按年份):**
- MySQL/MariaDB: `PARTITION BY RANGE (YEAR(created_at))`
- PostgreSQL: `PARTITION BY RANGE (created_at)`
- 优势: 查询性能提升、历史数据归档

### 3. 特定数据库优化

**MySQL:**
- 使用InnoDB引擎 (支持事务、外键)
- FULLTEXT索引 (ngram全文搜索)

**PostgreSQL:**
- GIN索引 (JSON字段tags)
- FTS全文搜索 (to_tsvector)
- JSONB类型 (高效JSON存储)

**MariaDB:**
- 系统版本化表 (自动历史记录)
- 动态列 (灵活扩展)
- ARCHIVE引擎 (审计日志压缩)

**SQLite:**
- FTS5全文搜索
- WAL模式 (并发性能)
- PRAGMA优化

## 🔄 四库同步机制

### 同步字段
所有业务表包含 `sync_version` 字段:
- 每次更新 `sync_version += 1`
- 同步时比较版本号
- 冲突记录到 `conflict_records` 表

### 冲突类型
1. **version_mismatch** - 版本号不匹配
2. **data_inconsistency** - 数据不一致
3. **constraint_violation** - 约束冲突

### 解决策略
- **最新优先:** 取最大sync_version
- **手动解决:** 管理员审核
- **回滚:** 恢复到冲突前状态

## 📝 数据字典

### 用户表 (users)

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 用户ID | PK, AUTO_INCREMENT |
| username | VARCHAR(50) | 用户名 | UNIQUE, NOT NULL |
| email | VARCHAR(100) | 校园邮箱 | UNIQUE, NOT NULL |
| student_id | VARCHAR(20) | 学号 | UNIQUE |
| credit_score | INT | 信用分 | 0-100 |
| seller_rating | DECIMAL(3,2) | 卖家评分 | 0-5 |
| is_banned | BOOLEAN | 是否封禁 | DEFAULT FALSE |
| sync_version | INT | 同步版本 | DEFAULT 0 |

### 商品表 (items)

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 商品ID | PK |
| title | VARCHAR(200) | 商品标题 | NOT NULL |
| price | DECIMAL(10,2) | 价格 | NOT NULL |
| condition_type | ENUM | 成色 | 全新/99新/95新/9成新/二手 |
| status | ENUM | 状态 | available/reserved/sold/deleted |
| tags | JSON | 标签 | 可小刀/包邮/急出等 |
| view_count | INT | 浏览量 | DEFAULT 0 |

### 交易表 (transactions)

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 交易ID | PK |
| buyer_id | BIGINT | 买家 | FK -> users.id |
| seller_id | BIGINT | 卖家 | FK -> users.id |
| status | ENUM | 状态 | pending/contacted/meeting/completed/cancelled |
| buyer_rating | TINYINT | 买家评分 | 1-5 |
| seller_rating | TINYINT | 卖家评分 | 1-5 |

## 🎓 初始化数据

### 分类数据 (8个)
1. 全部 (all)
2. 数码产品 (electronics)
3. 图书教材 (books)
4. 生活用品 (daily)
5. 运动装备 (sports)
6. 服装鞋包 (fashion)
7. 美妆护肤 (beauty)
8. 其他 (other)

### 系统配置
- `platform_name`: 校园交易平台
- `max_item_images`: 5 (最多图片数)
- `min_credit_score`: 60 (最低信用分)
- `transaction_timeout_hours`: 24
- `ban_credit_score`: 30 (封号阈值)

## 🛠️ 维护命令

### 查看表结构
```sql
-- MySQL/MariaDB
DESCRIBE users;
SHOW CREATE TABLE items;

-- PostgreSQL
\d users
\d+ items

-- SQLite
.schema users
```

### 查看索引
```sql
-- MySQL/MariaDB
SHOW INDEX FROM items;

-- PostgreSQL
\di items*

-- SQLite
.indexes items
```

### 查看触发器
```sql
-- MySQL/MariaDB
SHOW TRIGGERS;

-- PostgreSQL
\dS trg_*

-- SQLite
.schema triggers
```

### 清空测试数据
```sql
-- 保留结构,清空数据
TRUNCATE TABLE transactions;
TRUNCATE TABLE messages;
TRUNCATE TABLE comments;
TRUNCATE TABLE item_images;
TRUNCATE TABLE items;
TRUNCATE TABLE favorites;
TRUNCATE TABLE reports;
TRUNCATE TABLE users;
```

## 📌 注意事项

1. **外键约束:** 
   - MySQL/MariaDB/PostgreSQL默认开启
   - SQLite需要 `PRAGMA foreign_keys = ON;`

2. **字符集:**
   - MySQL/MariaDB使用 `utf8mb4` (支持emoji)
   - PostgreSQL默认UTF8

3. **时间戳:**
   - MySQL/MariaDB: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
   - PostgreSQL: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
   - SQLite: `TEXT DEFAULT (datetime('now'))`

4. **自增ID:**
   - MySQL/MariaDB: `AUTO_INCREMENT`
   - PostgreSQL: `BIGSERIAL`
   - SQLite: `AUTOINCREMENT`

5. **JSON类型:**
   - MySQL 5.7+: `JSON`
   - PostgreSQL: `JSONB` (二进制,性能更好)
   - SQLite: `TEXT` (存储为文本)

## 🔗 相关文档

- [数据库同步文档](../docs/4-DATABASE-SYNC.md)
- [交易流程说明](../../TRANSACTION_FLOW.md)
- [系统架构](../../SYSTEM_OVERVIEW.md)

---

**版本:** 2.0  
**更新日期:** 2025-11-18  
**维护者:** Campus Trading System Team
