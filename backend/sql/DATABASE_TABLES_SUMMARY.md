# 数据库表结构完整清单

## 📋 概述

本文档记录了校园交易系统的所有数据库表结构。系统支持4种数据库：**MySQL**、**PostgreSQL**、**MariaDB**、**SQLite**。

**总表数：30个**（原有25个 + 新增5个）

---

## 🆕 新增表（2025-11-19）

### 1. cart_items（购物车表）

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | BIGINT | 主键 | PRIMARY |
| user_id | BIGINT | 用户ID | UNIQUE(user_id, item_id), INDEX |
| item_id | BIGINT | 商品ID | INDEX |
| quantity | INT | 数量（默认1） | - |
| created_at | TIMESTAMP | 创建时间 | INDEX |
| updated_at | TIMESTAMP | 更新时间 | - |

**用途**：存储用户添加到购物车的商品  
**关联**：user_id → users.id, item_id → items.id

---

### 2. search_history（搜索历史表）

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | BIGINT | 主键 | PRIMARY |
| user_id | BIGINT | 用户ID | INDEX |
| keyword | VARCHAR(200) | 搜索关键词 | INDEX |
| result_count | INT | 搜索结果数量 | - |
| search_type | ENUM | 搜索类型(keyword/category/advanced) | - |
| filters | JSON | 搜索过滤条件 | - |
| created_at | TIMESTAMP | 搜索时间 | INDEX(user_id, created_at) |

**用途**：记录用户的搜索行为  
**关联**：user_id → users.id

---

### 3. conversations（会话表）

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | BIGINT | 主键 | PRIMARY |
| user1_id | BIGINT | 用户1 ID | UNIQUE(user1_id, user2_id), INDEX |
| user2_id | BIGINT | 用户2 ID | INDEX |
| item_id | BIGINT | 关联商品ID（可选） | INDEX |
| last_message_id | BIGINT | 最后一条消息ID | - |
| last_message_content | TEXT | 最后消息内容 | - |
| last_message_at | TIMESTAMP | 最后消息时间 | - |
| user1_unread_count | INT | 用户1未读数（默认0） | - |
| user2_unread_count | INT | 用户2未读数（默认0） | - |
| user1_deleted | BOOLEAN | 用户1是否删除 | INDEX(user1_id, user1_deleted) |
| user2_deleted | BOOLEAN | 用户2是否删除 | INDEX(user2_id, user2_deleted) |
| created_at | TIMESTAMP | 创建时间 | - |
| updated_at | TIMESTAMP | 更新时间 | INDEX |

**用途**：管理用户间的聊天会话  
**关联**：user1_id, user2_id → users.id, item_id → items.id, last_message_id → messages.id

---

### 4. search_trending（热门搜索统计表）

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | BIGINT | 主键 | PRIMARY |
| keyword | VARCHAR(200) | 搜索关键词 | UNIQUE(keyword, date) |
| search_count | INT | 搜索次数（默认1） | INDEX DESC |
| last_searched_at | TIMESTAMP | 最后搜索时间 | INDEX |
| date | DATE | 统计日期 | INDEX |

**用途**：统计每日热门搜索词  
**特性**：按日期聚合，用于展示热搜榜

---

### 5. refresh_tokens（刷新令牌表）

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | BIGINT | 主键 | PRIMARY |
| user_id | BIGINT | 用户ID | INDEX |
| token | VARCHAR(500) | 刷新令牌 | UNIQUE |
| access_token | VARCHAR(500) | 关联的访问令牌 | - |
| expires_at | TIMESTAMP | 过期时间 | INDEX |
| device_info | VARCHAR(500) | 设备信息 | - |
| ip_address | VARCHAR(50) | IP地址 | - |
| user_agent | TEXT | 用户代理 | - |
| is_revoked | BOOLEAN | 是否已撤销（默认FALSE） | INDEX |
| revoked_at | TIMESTAMP | 撤销时间 | - |
| created_at | TIMESTAMP | 创建时间 | - |
| last_used_at | TIMESTAMP | 最后使用时间 | - |

**用途**：JWT刷新令牌管理，支持撤销和过期控制  
**关联**：user_id → users.id

---

## 📊 原有表分类（25个）

### 核心业务表（9个）
1. **users** - 用户表
2. **categories** - 商品分类表
3. **items** - 商品表
4. **item_images** - 商品图片表
5. **comments** - 评论表
6. **transactions** - 交易订单表
7. **messages** - 消息表
8. **favorites** - 收藏表
9. **reports** - 举报表

### 系统管理表（3个）
10. **audit_logs** - 审计日志表
11. **conflict_records** - 冲突记录表
12. **system_configs** - 系统配置表

### 扩展功能表（13个）
13. **user_follows** - 用户关注表
14. **item_view_history** - 商品浏览历史
15. **user_addresses** - 用户地址表
16. **item_price_history** - 商品价格历史
17. **comment_likes** - 评论点赞表
18. **message_attachments** - 消息附件表
19. **report_actions** - 举报处理记录
20. **transaction_review_images** - 交易评价图片
21. **notifications** - 通知表
22. **user_profiles** - 用户详情表
23. **roles** - 角色表
24. **permissions** - 权限表
25. **role_permissions** - 角色权限关联表

---

## 🔧 SQL脚本文件清单

### MySQL/MariaDB
- **主脚本**：`mysql_complete_schema.sql` / `mariadb_complete_schema.sql`
- **补充脚本**：`add_missing_tables_mysql.sql` / `add_missing_tables_mariadb.sql`

### PostgreSQL
- **主脚本**：`postgres_complete_schema.sql`
- **补充脚本**：`add_missing_tables_postgres.sql`

### SQLite
- **主脚本**：`sqlite_complete_schema.sql`
- **补充脚本**：`add_missing_tables_sqlite.sql`

---

## 📝 执行顺序

### 1. 初次安装（执行主脚本）
```bash
# MySQL
mysql -h 127.0.0.1 -P 3306 -u root -pcampuswap_root campuswap < mysql_complete_schema.sql

# MariaDB
mysql -h 127.0.0.1 -P 3307 -u root -pcampuswap_root campuswap < mariadb_complete_schema.sql

# PostgreSQL
PGPASSWORD=campuswap_root psql -h 127.0.0.1 -p 5432 -U campuswap -d campuswap < postgres_complete_schema.sql

# SQLite
sqlite3 campuswap.db < sqlite_complete_schema.sql
```

### 2. 更新补充表（执行补充脚本）
```bash
# MySQL
mysql -h 127.0.0.1 -P 3306 -u root -pcampuswap_root campuswap < add_missing_tables_mysql.sql

# MariaDB
mysql -h 127.0.0.1 -P 3307 -u root -pcampuswap_root campuswap < add_missing_tables_mariadb.sql

# PostgreSQL
PGPASSWORD=campuswap_root psql -h 127.0.0.1 -p 5432 -U campuswap -d campuswap < add_missing_tables_postgres.sql

# SQLite
sqlite3 campuswap.db < add_missing_tables_sqlite.sql
```

---

## ✅ 验证表创建

```bash
# MySQL/MariaDB
mysql -h 127.0.0.1 -P 3306 -u root -pcampuswap_root campuswap -e "SHOW TABLES;"

# PostgreSQL
PGPASSWORD=campuswap_root psql -h 127.0.0.1 -p 5432 -U campuswap -d campuswap -c "\dt"

# SQLite
sqlite3 campuswap.db ".tables"
```

---

## 🎯 ORM模型文件

新增模型位于：`backend/apps/core/models/additional.py`

包含以下类：
- `CartItem` - 购物车模型
- `SearchHistory` - 搜索历史模型
- `SearchTrending` - 热门搜索模型
- `Conversation` - 会话模型
- `RefreshToken` - 刷新令牌模型

已导入到：`backend/apps/core/models/__init__.py`

---

## ⚠️ 重要说明

1. **外键约束**：为了支持多数据库同步，部分表未使用外键约束，改为应用层验证
2. **时间戳**：所有时间字段使用UTC时间
3. **软删除**：conversations表使用软删除标记
4. **唯一约束**：
   - cart_items: (user_id, item_id)
   - conversations: (user1_id, user2_id)
   - search_trending: (keyword, date)
   - refresh_tokens: (token)

---

## 📅 版本历史

- **v1.0** (2025-11-18): 创建25个核心表
- **v1.1** (2025-11-19): 新增5个补充表（购物车、搜索、会话、刷新令牌）

---

## 🔒 安全建议

1. **refresh_tokens表**：定期清理过期token
2. **search_history表**：实施数据保留策略（如90天）
3. **cart_items表**：定期清理30天未更新的记录
4. **索引优化**：根据实际查询模式调整索引

---

**最后更新**：2025-11-19  
**维护者**：Campus Trading System Team
