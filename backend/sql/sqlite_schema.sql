-- SQLite 数据库完整脚本
-- SQLite 功能较简化，不支持存储过程，使用触发器实现部分逻辑

-- ============================================
-- 1. 建表语句
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,  -- SQLite 使用 INTEGER 表示 BOOLEAN
    is_verified INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_value TEXT,  -- SQLite 使用 TEXT 存储 JSON
    new_value TEXT,
    ip_address TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_table ON audit_logs(table_name, operation);
CREATE INDEX idx_audit_created ON audit_logs(created_at);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER,
    status TEXT DEFAULT 'available' CHECK (status IN ('available', 'sold', 'reserved', 'deleted')),
    view_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_items_seller ON items(seller_id);
CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_created ON items(created_at);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    buyer_id INTEGER NOT NULL REFERENCES users(id),
    seller_id INTEGER NOT NULL REFERENCES users(id),
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'shipped', 'completed', 'cancelled')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_trans_buyer ON transactions(buyer_id);
CREATE INDEX idx_trans_seller ON transactions(seller_id);
CREATE INDEX idx_trans_item ON transactions(item_id);
CREATE INDEX idx_trans_status ON transactions(status);

-- SQLite 不直接支持分区表，使用视图模拟
CREATE VIEW IF NOT EXISTS transactions_2024 AS
SELECT * FROM transactions 
WHERE strftime('%Y', created_at) = '2024';

CREATE VIEW IF NOT EXISTS transactions_2025 AS
SELECT * FROM transactions 
WHERE strftime('%Y', created_at) = '2025';

CREATE TABLE IF NOT EXISTS conflict_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    source_db TEXT NOT NULL,
    target_db TEXT NOT NULL,
    conflict_type TEXT NOT NULL CHECK (conflict_type IN ('version_mismatch', 'data_inconsistency', 'constraint_violation')),
    local_data TEXT,
    remote_data TEXT,
    resolved INTEGER DEFAULT 0,
    resolved_by INTEGER,
    resolved_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_conflict_resolved ON conflict_records(resolved);
CREATE INDEX idx_conflict_table ON conflict_records(table_name, record_id);

CREATE TABLE IF NOT EXISTS sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db TEXT NOT NULL,
    target_db TEXT NOT NULL,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    record_count INTEGER DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    error_message TEXT,
    duration_ms INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_sync_status ON sync_logs(status);
CREATE INDEX idx_sync_created ON sync_logs(created_at);

-- ============================================
-- 2. 触发器 (SQLite 的核心功能补偿机制)
-- ============================================

-- users 表触发器 - 自动更新 updated_at
CREATE TRIGGER IF NOT EXISTS trg_users_updated
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- users 表审计触发器 - INSERT
CREATE TRIGGER IF NOT EXISTS trg_users_audit_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, new_value, ip_address)
    VALUES (
        NEW.id,
        'users',
        'INSERT',
        json_object('id', NEW.id, 'username', NEW.username, 'email', NEW.email),
        'system'
    );
END;

-- users 表审计触发器 - UPDATE
CREATE TRIGGER IF NOT EXISTS trg_users_audit_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, new_value, ip_address)
    VALUES (
        NEW.id,
        'users',
        'UPDATE',
        json_object('username', OLD.username, 'is_active', OLD.is_active),
        json_object('username', NEW.username, 'is_active', NEW.is_active),
        'system'
    );
END;

-- users 表审计触发器 - DELETE
CREATE TRIGGER IF NOT EXISTS trg_users_audit_delete
AFTER DELETE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, ip_address)
    VALUES (
        OLD.id,
        'users',
        'DELETE',
        json_object('id', OLD.id, 'username', OLD.username),
        'system'
    );
END;

-- items 表触发器 - 自动增加 sync_version
CREATE TRIGGER IF NOT EXISTS trg_items_before_update
BEFORE UPDATE ON items
FOR EACH ROW
BEGIN
    SELECT RAISE(IGNORE) WHERE NEW.sync_version != OLD.sync_version;
END;

CREATE TRIGGER IF NOT EXISTS trg_items_update_version
AFTER UPDATE ON items
FOR EACH ROW
BEGIN
    UPDATE items 
    SET sync_version = OLD.sync_version + 1,
        updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- items 表审计触发器
CREATE TRIGGER IF NOT EXISTS trg_items_audit_update
AFTER UPDATE ON items
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, new_value)
    VALUES (
        NEW.seller_id,
        'items',
        'UPDATE',
        json_object('title', OLD.title, 'price', OLD.price, 'status', OLD.status),
        json_object('title', NEW.title, 'price', NEW.price, 'status', NEW.status)
    );
END;

-- transactions 表触发器 - 自动增加 sync_version
CREATE TRIGGER IF NOT EXISTS trg_trans_update_version
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
    UPDATE transactions 
    SET sync_version = OLD.sync_version + 1,
        updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- transactions 表审计触发器 - 状态变更
CREATE TRIGGER IF NOT EXISTS trg_trans_audit_update
AFTER UPDATE ON transactions
FOR EACH ROW
WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO audit_logs (table_name, operation, old_value, new_value)
    VALUES (
        'transactions',
        'UPDATE',
        json_object('id', OLD.id, 'status', OLD.status),
        json_object('id', NEW.id, 'status', NEW.status)
    );
END;

-- ============================================
-- 3. 视图 (替代存储过程/函数)
-- ============================================

-- 用户交易统计视图
CREATE VIEW IF NOT EXISTS vw_user_transaction_stats AS
SELECT 
    u.id AS user_id,
    u.username,
    COUNT(DISTINCT CASE WHEN t.buyer_id = u.id THEN t.id END) AS purchases,
    COUNT(DISTINCT CASE WHEN t.seller_id = u.id THEN t.id END) AS sales,
    (COUNT(DISTINCT CASE WHEN t.seller_id = u.id THEN t.id END) * 2 + 
     COUNT(DISTINCT CASE WHEN t.buyer_id = u.id THEN t.id END) * 1) * 0.1 AS reputation_score
FROM users u
LEFT JOIN transactions t ON (u.id = t.buyer_id OR u.id = t.seller_id) 
    AND t.status = 'completed'
GROUP BY u.id, u.username;

-- 分类平均价格视图
CREATE VIEW IF NOT EXISTS vw_category_avg_price AS
SELECT 
    category_id,
    COUNT(*) AS item_count,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM items
WHERE status = 'available'
GROUP BY category_id;

-- 活跃商品列表视图
CREATE VIEW IF NOT EXISTS vw_active_listings AS
SELECT 
    i.id,
    i.title,
    i.price,
    i.status,
    u.username AS seller_name,
    u.email AS seller_email,
    i.created_at
FROM items i
INNER JOIN users u ON i.seller_id = u.id
WHERE i.status = 'available' AND u.is_active = 1;

-- 交易汇总视图
CREATE VIEW IF NOT EXISTS vw_transaction_summary AS
SELECT 
    DATE(t.created_at) AS transaction_date,
    COUNT(t.id) AS total_transactions,
    SUM(t.total_amount) AS total_revenue,
    AVG(t.total_amount) AS avg_transaction_value
FROM transactions t
WHERE t.status = 'completed'
GROUP BY DATE(t.created_at)
ORDER BY transaction_date DESC;

-- 同步状态视图
CREATE VIEW IF NOT EXISTS vw_sync_status AS
SELECT 
    target_db,
    COUNT(*) AS total_syncs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    AVG(duration_ms) AS avg_duration_ms
FROM sync_logs
GROUP BY target_db;

-- ============================================
-- 4. 复合索引优化
-- ============================================

CREATE INDEX idx_items_category_status ON items(category_id, status);
CREATE INDEX idx_transactions_buyer_status ON transactions(buyer_id, status);
CREATE INDEX idx_transactions_seller_status ON transactions(seller_id, status);

-- SQLite 全文搜索 (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    title,
    description,
    content=items,
    content_rowid=id
);

-- 触发器保持全文索引同步
CREATE TRIGGER IF NOT EXISTS trg_items_fts_insert
AFTER INSERT ON items
BEGIN
    INSERT INTO items_fts(rowid, title, description)
    VALUES (NEW.id, NEW.title, NEW.description);
END;

CREATE TRIGGER IF NOT EXISTS trg_items_fts_delete
AFTER DELETE ON items
BEGIN
    DELETE FROM items_fts WHERE rowid = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_items_fts_update
AFTER UPDATE ON items
BEGIN
    DELETE FROM items_fts WHERE rowid = OLD.id;
    INSERT INTO items_fts(rowid, title, description)
    VALUES (NEW.id, NEW.title, NEW.description);
END;

-- ============================================
-- 5. 辅助查询示例 (用于测试和演示)
-- ============================================

-- 示例1: 查询用户信誉度 (使用视图)
-- SELECT user_id, username, reputation_score 
-- FROM vw_user_transaction_stats
-- ORDER BY reputation_score DESC;

-- 示例2: 全文搜索商品
-- SELECT i.* FROM items i
-- WHERE i.id IN (
--     SELECT rowid FROM items_fts WHERE items_fts MATCH '笔记本'
-- );

-- 示例3: 检查版本冲突 (应用层调用)
-- SELECT sync_version FROM items WHERE id = ?;

-- 示例4: 清理过期冲突记录 (定期执行)
-- DELETE FROM conflict_records
-- WHERE resolved = 1 
--   AND datetime(resolved_at) < datetime('now', '-30 days');

-- ============================================
-- 说明:
-- SQLite 限制与解决方案:
-- 1. 不支持存储过程 → 使用触发器 + 视图 + 应用层逻辑
-- 2. 不支持分区表 → 使用视图模拟分区
-- 3. JSON 支持有限 → 使用 json_object/json_extract 函数
-- 4. BOOLEAN 类型 → 使用 INTEGER (0/1)
-- 5. 日期时间 → 使用 TEXT 存储 ISO8601 格式
-- 6. 全文搜索 → 使用 FTS5 虚拟表
-- 7. 自增主键 → 使用 AUTOINCREMENT
-- ============================================
