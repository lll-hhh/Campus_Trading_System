## 数据库脚本说明

本目录包含四种数据库的完整初始化脚本,包括建表、索引、触发器、存储过程、函数和视图。

### 📁 文件列表

| 文件 | 数据库类型 | 说明 |
|------|-----------|------|
| `mysql_schema.sql` | MySQL 8.0+ | MySQL 专用脚本 |
| `mariadb_schema.sql` | MariaDB 10.6+ | MariaDB 专用脚本 |
| `postgres_schema.sql` | PostgreSQL 14+ | PostgreSQL 专用脚本 |
| `sqlite_schema.sql` | SQLite 3.35+ | SQLite 专用脚本 |

---

### 🎯 包含的数据库对象

#### 1. **表结构** (示例核心表)
- `users` - 用户表
- `items` - 商品表
- `transactions` - 交易表 (包含分区表设计)
- `audit_logs` - 审计日志表
- `conflict_records` - 同步冲突记录表
- `sync_logs` - 同步日志表

#### 2. **触发器** (Triggers)
| 触发器名称 | 作用表 | 功能 |
|-----------|--------|------|
| `trg_users_after_insert` | users | 自动记录用户新增到审计日志 |
| `trg_users_after_update` | users | 自动记录用户更新到审计日志 |
| `trg_users_after_delete` | users | 自动记录用户删除到审计日志 |
| `trg_items_before_update` | items | 更新前自动增加 sync_version |
| `trg_items_after_update` | items | 更新后记录变更到审计日志 |
| `trg_transactions_after_update` | transactions | 交易状态变更时自动审计 |

**触发器作用:**
- ✅ 自动维护数据一致性
- ✅ 实现乐观锁版本控制 (sync_version)
- ✅ 全面审计日志记录 (insert/update/delete)
- ✅ 满足任务书"触发器实现数据一致性维护"要求

#### 3. **存储过程** (Stored Procedures)
| 过程名称 | 参数 | 功能 |
|---------|------|------|
| `sp_sync_table_data` | table_name, target_db, start_id, end_id | 批量同步数据到其他数据库 |
| `sp_calculate_user_reputation` | user_id, OUT reputation_score | 计算用户信誉度分数 |
| `sp_cleanup_old_conflicts` | days_old | 清理指定天数前的已解决冲突记录 |
| `sp_generate_test_users` (MariaDB) | count | 批量生成测试用户数据 |

**存储过程作用:**
- ✅ 封装复杂业务逻辑
- ✅ 提高数据处理性能 (减少网络往返)
- ✅ 实现跨表复杂计算 (信誉度、统计等)
- ✅ 满足任务书"编写存储过程实现业务逻辑"要求

#### 4. **存储函数** (Stored Functions)
| 函数名称 | 参数 | 返回值 | 功能 |
|---------|------|--------|------|
| `fn_get_user_transaction_count` | user_id | INT | 获取用户完成交易总数 |
| `fn_avg_price_by_category` | category_id | DECIMAL(10,2) | 计算分类平均价格 |
| `fn_check_version_conflict` | table_name, record_id, expected_version | BOOLEAN | 检查数据版本是否冲突 |

**存储函数作用:**
- ✅ 提供可复用的计算逻辑
- ✅ 在 SQL 查询中直接调用
- ✅ 简化应用层代码
- ✅ 满足任务书"存储函数"要求

#### 5. **视图** (Views)
| 视图名称 | 功能 |
|---------|------|
| `vw_active_listings` | 活跃商品列表 (关联用户信息) |
| `vw_transaction_summary` | 每日交易汇总统计 |
| `vw_user_transaction_stats` (SQLite) | 用户交易统计和信誉度 |
| `vw_category_avg_price` (SQLite) | 分类价格统计 |

#### 6. **索引优化**
```sql
-- 复合索引示例
CREATE INDEX idx_items_category_status ON items(category_id, status);
CREATE INDEX idx_transactions_buyer_status ON transactions(buyer_id, status);

-- 全文索引 (MySQL/MariaDB)
ALTER TABLE items ADD FULLTEXT INDEX ft_title_desc (title, description);

-- PostgreSQL GIN 索引
CREATE INDEX idx_items_title_fts ON items USING gin(to_tsvector('english', title));
```

#### 7. **分区表设计**
```sql
-- transactions 表按年份分区 (MySQL/MariaDB)
PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- PostgreSQL 分区表
CREATE TABLE transactions_2024 PARTITION OF transactions
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

---

### 🚀 使用方式

#### 方式一: 自动初始化 (推荐)
后端服务启动时会自动执行所有数据库的初始化脚本:

```bash
# 启动 API Gateway
cd backend
poetry run uvicorn apps.api_gateway.main:app --reload
```

启动日志示例:
```
INFO:     应用启动中...开始初始化数据库对象
INFO:     mysql: 执行 45 条成功, 2 条失败
INFO:     postgres: 执行 38 条成功, 0 条失败
INFO:     mariadb: 执行 47 条成功, 1 条失败
INFO:     sqlite: 执行 32 条成功, 0 条失败
```

#### 方式二: 手动 API 调用
使用管理员账户调用初始化接口:

```bash
# 初始化所有数据库
curl -X POST http://localhost:8000/api/v1/admin/database/initialize \
  -H "Authorization: Bearer <admin_token>"

# 初始化单个数据库
curl -X POST http://localhost:8000/api/v1/admin/database/initialize/mysql \
  -H "Authorization: Bearer <admin_token>"

# 验证数据库对象创建情况
curl http://localhost:8000/api/v1/admin/database/verify/mysql \
  -H "Authorization: Bearer <admin_token>"

# 查看所有数据库状态
curl http://localhost:8000/api/v1/admin/database/status \
  -H "Authorization: Bearer <admin_token>"
```

#### 方式三: 直接执行 SQL 文件
如需手动执行 (例如在数据库客户端中):

**MySQL:**
```bash
mysql -u root -p campuswap < backend/sql/mysql_schema.sql
```

**PostgreSQL:**
```bash
psql -U campuswap -d campuswap -f backend/sql/postgres_schema.sql
```

**MariaDB:**
```bash
mariadb -u root -p campuswap < backend/sql/mariadb_schema.sql
```

**SQLite:**
```bash
sqlite3 /data/sqlite/campuswap.db < backend/sql/sqlite_schema.sql
```

---

### 📊 复杂 SQL 查询示例

脚本中包含了多个复杂查询示例,展示:
- ✅ 多表 JOIN
- ✅ 嵌套子查询
- ✅ 窗口函数 (RANK, ROW_NUMBER)
- ✅ 聚合分组 (GROUP BY, HAVING)

示例 1: **查询每个分类下交易量 TOP5 商品**
```sql
SELECT 
    c.name AS category_name,
    i.title,
    u.username AS seller_name,
    COUNT(t.id) AS transaction_count,
    SUM(t.total_amount) AS total_revenue
FROM items i
INNER JOIN users u ON i.seller_id = u.id
LEFT JOIN categories c ON i.category_id = c.id
LEFT JOIN transactions t ON i.id = t.item_id AND t.status = 'completed'
GROUP BY c.id, i.id, u.username
ORDER BY c.id, transaction_count DESC
LIMIT 5;
```

示例 2: **使用窗口函数计算销售排名**
```sql
SELECT 
    seller_id,
    username,
    total_sales,
    RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
FROM (
    SELECT 
        u.id AS seller_id,
        u.username,
        COUNT(t.id) AS total_sales
    FROM users u
    LEFT JOIN transactions t ON u.id = t.seller_id AND t.status = 'completed'
    GROUP BY u.id, u.username
) AS user_sales;
```

---

### 🔧 数据库差异处理

| 特性 | MySQL | MariaDB | PostgreSQL | SQLite |
|-----|-------|---------|-----------|---------|
| 存储过程 | ✅ | ✅ | ✅ (函数) | ❌ (触发器替代) |
| 存储函数 | ✅ | ✅ | ✅ | ❌ (视图替代) |
| 触发器 | ✅ | ✅ | ✅ | ✅ |
| 分区表 | ✅ | ✅ | ✅ | ❌ (视图模拟) |
| JSON 支持 | JSON | JSON | JSONB | TEXT + json_* |
| 全文搜索 | FULLTEXT | FULLTEXT | GIN 索引 | FTS5 虚拟表 |

**SQLite 限制补偿方案:**
- 用**触发器**替代存储过程完成复杂逻辑
- 用**视图**替代函数提供计算结果
- 用**视图**模拟分区表 (按年份过滤)

---

### ✅ 任务书要求对照

| 要求 | 实现方式 | 文件位置 |
|-----|---------|---------|
| 编写触发器 | ✅ 6+ 触发器实现审计、版本控制 | 所有 SQL 文件 |
| 编写存储过程 | ✅ 4+ 存储过程实现业务逻辑 | MySQL/MariaDB/PostgreSQL |
| 编写存储函数 | ✅ 3+ 函数提供计算逻辑 | MySQL/MariaDB/PostgreSQL |
| 数据一致性维护 | ✅ 触发器自动维护 sync_version | 所有 SQL 文件 |
| 复杂 SQL 查询 | ✅ 多表 JOIN、子查询、窗口函数 | 注释示例 |
| 索引优化 | ✅ 复合索引、全文索引 | 所有 SQL 文件 |
| 分区表设计 | ✅ transactions 按年份分区 | MySQL/MariaDB/PostgreSQL |

---

### 🧪 测试验证

1. **检查触发器是否生效:**
```sql
-- 插入测试用户
INSERT INTO users (username, email, password_hash) 
VALUES ('test_trigger', 'test@example.com', 'hash');

-- 查看审计日志
SELECT * FROM audit_logs WHERE table_name = 'users' ORDER BY created_at DESC LIMIT 1;
```

2. **调用存储过程:**
```sql
-- 计算用户信誉度
CALL sp_calculate_user_reputation(1, @score);
SELECT @score;  -- MySQL/MariaDB

-- PostgreSQL
SELECT sp_calculate_user_reputation(1);
```

3. **使用存储函数:**
```sql
SELECT fn_get_user_transaction_count(1);
SELECT fn_avg_price_by_category(5);
```

---

### 📝 维护说明

- **新增触发器**: 在对应数据库的 SQL 文件中添加,然后调用 `/admin/database/initialize/{db_name}` 重新执行
- **修改存储过程**: 使用 `CREATE OR REPLACE` (PostgreSQL/MariaDB) 或先 `DROP` 再 `CREATE` (MySQL)
- **性能优化**: 定期运行 `ANALYZE TABLE` (MySQL) 或 `VACUUM ANALYZE` (PostgreSQL) 更新统计信息

---

### 📚 参考资料

- MySQL 触发器文档: https://dev.mysql.com/doc/refman/8.0/en/triggers.html
- PostgreSQL 函数文档: https://www.postgresql.org/docs/14/plpgsql.html
- SQLite 触发器文档: https://www.sqlite.org/lang_createtrigger.html
- MariaDB 存储过程: https://mariadb.com/kb/en/stored-procedures/
