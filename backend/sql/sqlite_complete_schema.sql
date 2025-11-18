-- ============================================
-- SQLite 校园交易系统完整数据库脚本
-- ============================================
-- 版本: 2.0
-- 日期: 2025-11-18
-- 说明: SQLite轻量级版本,适用于本地开发和测试

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ============================================
-- 1. 核心业务表
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    student_id TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    phone TEXT,
    avatar_url TEXT,
    real_name TEXT,
    
    is_active INTEGER DEFAULT 1,
    is_verified INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0,
    
    credit_score INTEGER DEFAULT 100 CHECK (credit_score >= 0 AND credit_score <= 100),
    seller_rating REAL DEFAULT 5.00 CHECK (seller_rating >= 0 AND seller_rating <= 5),
    buyer_rating REAL DEFAULT 5.00 CHECK (buyer_rating >= 0 AND buyer_rating <= 5),
    
    total_sales INTEGER DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,
    
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_login_at TEXT,
    
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_student_id ON users(student_id);
CREATE INDEX idx_users_credit ON users(credit_score);
CREATE INDEX idx_users_active ON users(is_active, is_banned);

-- 商品分类表
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_active ON categories(is_active);

-- 商品表
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    category_id INTEGER,
    
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    original_price REAL,
    
    condition_type TEXT DEFAULT '二手' CHECK (condition_type IN ('全新', '99新', '95新', '9成新', '二手')),
    location TEXT,
    contact_info TEXT,
    
    tags TEXT, -- JSON array as text
    
    status TEXT DEFAULT 'available' CHECK (status IN ('available', 'reserved', 'sold', 'deleted')),
    is_negotiable INTEGER DEFAULT 0,
    is_shipped INTEGER DEFAULT 0,
    
    view_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    inquiry_count INTEGER DEFAULT 0,
    
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sold_at TEXT,
    
    sync_version INTEGER DEFAULT 0,
    
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE INDEX idx_items_seller ON items(seller_id);
CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_created ON items(created_at);
CREATE INDEX idx_items_price ON items(price);

-- SQLite全文搜索 (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    title, description, 
    content='items',
    content_rowid='id'
);

-- 商品图片表
CREATE TABLE IF NOT EXISTS item_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_cover INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0,
    
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX idx_item_images_item ON item_images(item_id);
CREATE INDEX idx_item_images_cover ON item_images(item_id, is_cover);

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    parent_id INTEGER,
    
    content TEXT NOT NULL,
    
    is_deleted INTEGER DEFAULT 0,
    is_reported INTEGER DEFAULT 0,
    
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0,
    
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
);

CREATE INDEX idx_comments_item ON comments(item_id);
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
CREATE INDEX idx_comments_created ON comments(created_at);

-- 交易表
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    buyer_id INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    
    item_price REAL NOT NULL,
    final_amount REAL NOT NULL,
    
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'contacted', 'meeting', 'completed', 'cancelled')),
    
    buyer_contact TEXT,
    seller_contact TEXT,
    meeting_location TEXT,
    meeting_time TEXT,
    
    buyer_rating INTEGER CHECK (buyer_rating >= 1 AND buyer_rating <= 5),
    seller_rating INTEGER CHECK (seller_rating >= 1 AND seller_rating <= 5),
    buyer_review TEXT,
    seller_review TEXT,
    
    created_at TEXT DEFAULT (datetime('now')),
    contacted_at TEXT,
    completed_at TEXT,
    cancelled_at TEXT,
    
    sync_version INTEGER DEFAULT 0,
    
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (buyer_id) REFERENCES users(id),
    FOREIGN KEY (seller_id) REFERENCES users(id)
);

CREATE INDEX idx_transactions_buyer ON transactions(buyer_id);
CREATE INDEX idx_transactions_seller ON transactions(seller_id);
CREATE INDEX idx_transactions_item ON transactions(item_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created ON transactions(created_at);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    item_id INTEGER,
    
    content TEXT NOT NULL,
    
    is_read INTEGER DEFAULT 0,
    is_deleted_by_sender INTEGER DEFAULT 0,
    is_deleted_by_receiver INTEGER DEFAULT 0,
    
    created_at TEXT DEFAULT (datetime('now')),
    read_at TEXT,
    sync_version INTEGER DEFAULT 0,
    
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL
);

CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_receiver ON messages(receiver_id);
CREATE INDEX idx_messages_conversation ON messages(sender_id, receiver_id);
CREATE INDEX idx_messages_item ON messages(item_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0,
    
    UNIQUE (user_id, item_id),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX idx_favorites_user ON favorites(user_id);
CREATE INDEX idx_favorites_item ON favorites(item_id);

-- 举报表
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL,
    reported_user_id INTEGER,
    item_id INTEGER,
    comment_id INTEGER,
    
    report_type TEXT NOT NULL CHECK (report_type IN ('fraud', 'fake_item', 'harassment', 'spam', 'other')),
    reason TEXT NOT NULL,
    
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'resolved', 'rejected')),
    admin_note TEXT,
    
    created_at TEXT DEFAULT (datetime('now')),
    resolved_at TEXT,
    sync_version INTEGER DEFAULT 0,
    
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (reported_user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE
);

CREATE INDEX idx_reports_reporter ON reports(reporter_id);
CREATE INDEX idx_reports_reported_user ON reports(reported_user_id);
CREATE INDEX idx_reports_status ON reports(status);

-- ============================================
-- 2. 系统管理表
-- ============================================

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id INTEGER,
    old_value TEXT, -- JSON as text
    new_value TEXT, -- JSON as text
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name, operation);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_record ON audit_logs(table_name, record_id);

-- 同步冲突表
CREATE TABLE IF NOT EXISTS conflict_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    source_db TEXT NOT NULL,
    target_db TEXT NOT NULL,
    conflict_type TEXT NOT NULL CHECK (conflict_type IN ('version_mismatch', 'data_inconsistency', 'constraint_violation')),
    local_data TEXT, -- JSON as text
    remote_data TEXT, -- JSON as text
    resolved INTEGER DEFAULT 0,
    resolved_by INTEGER,
    resolution_strategy TEXT,
    resolved_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_conflict_records_resolved ON conflict_records(resolved);
CREATE INDEX idx_conflict_records_table ON conflict_records(table_name, record_id);
CREATE INDEX idx_conflict_records_created ON conflict_records(created_at);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    is_public INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_system_configs_key ON system_configs(config_key);

-- ============================================
-- 3. 触发器 (SQLite版本)
-- ============================================

-- 更新updated_at触发器
CREATE TRIGGER trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER trg_items_updated_at
AFTER UPDATE ON items
FOR EACH ROW
BEGIN
    UPDATE items SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER trg_comments_updated_at
AFTER UPDATE ON comments
FOR EACH ROW
BEGIN
    UPDATE comments SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER trg_system_configs_updated_at
AFTER UPDATE ON system_configs
FOR EACH ROW
BEGIN
    UPDATE system_configs SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- 用户创建审计日志
CREATE TRIGGER trg_after_user_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, record_id, new_value)
    VALUES (NEW.id, 'users', 'INSERT', NEW.id, json_object(
        'username', NEW.username,
        'email', NEW.email
    ));
END;

-- 评论后更新商品咨询量
CREATE TRIGGER trg_after_comment_insert
AFTER INSERT ON comments
FOR EACH ROW
BEGIN
    UPDATE items SET inquiry_count = inquiry_count + 1 WHERE id = NEW.item_id;
END;

-- 收藏后更新商品收藏量
CREATE TRIGGER trg_after_favorite_insert
AFTER INSERT ON favorites
FOR EACH ROW
BEGIN
    UPDATE items SET favorite_count = favorite_count + 1 WHERE id = NEW.item_id;
END;

CREATE TRIGGER trg_after_favorite_delete
AFTER DELETE ON favorites
FOR EACH ROW
BEGIN
    UPDATE items SET favorite_count = favorite_count - 1 WHERE id = OLD.item_id;
END;

-- 交易完成后更新统计
CREATE TRIGGER trg_after_transaction_complete
AFTER UPDATE OF status ON transactions
FOR EACH ROW
WHEN NEW.status = 'completed' AND OLD.status != 'completed'
BEGIN
    UPDATE users SET total_sales = total_sales + 1 WHERE id = NEW.seller_id;
    UPDATE users SET total_purchases = total_purchases + 1 WHERE id = NEW.buyer_id;
    UPDATE items SET status = 'sold', sold_at = datetime('now') WHERE id = NEW.item_id;
END;

-- 评分更新触发器
CREATE TRIGGER trg_after_seller_rating
AFTER UPDATE OF seller_rating ON transactions
FOR EACH ROW
WHEN NEW.seller_rating IS NOT NULL AND (OLD.seller_rating IS NULL OR OLD.seller_rating != NEW.seller_rating)
BEGIN
    UPDATE users 
    SET seller_rating = (
        SELECT AVG(seller_rating) 
        FROM transactions 
        WHERE seller_id = NEW.seller_id AND seller_rating IS NOT NULL
    )
    WHERE id = NEW.seller_id;
END;

CREATE TRIGGER trg_after_buyer_rating
AFTER UPDATE OF buyer_rating ON transactions
FOR EACH ROW
WHEN NEW.buyer_rating IS NOT NULL AND (OLD.buyer_rating IS NULL OR OLD.buyer_rating != NEW.buyer_rating)
BEGIN
    UPDATE users 
    SET buyer_rating = (
        SELECT AVG(buyer_rating) 
        FROM transactions 
        WHERE buyer_id = NEW.buyer_id AND buyer_rating IS NOT NULL
    )
    WHERE id = NEW.buyer_id;
END;

-- FTS同步触发器
CREATE TRIGGER trg_items_fts_insert
AFTER INSERT ON items
BEGIN
    INSERT INTO items_fts(rowid, title, description) VALUES (new.id, new.title, new.description);
END;

CREATE TRIGGER trg_items_fts_update
AFTER UPDATE ON items
BEGIN
    UPDATE items_fts SET title = new.title, description = new.description WHERE rowid = new.id;
END;

CREATE TRIGGER trg_items_fts_delete
AFTER DELETE ON items
BEGIN
    DELETE FROM items_fts WHERE rowid = old.id;
END;

-- ============================================
-- 4. 初始化数据
-- ============================================

INSERT OR IGNORE INTO categories (name, slug, description, sort_order) VALUES
('全部', 'all', '所有商品', 0),
('数码产品', 'electronics', '电脑、手机、平板等', 1),
('图书教材', 'books', '教材、课外书、杂志等', 2),
('生活用品', 'daily', '日用品、家居用品', 3),
('运动装备', 'sports', '运动器材、健身用品', 4),
('服装鞋包', 'fashion', '衣服、鞋子、包包', 5),
('美妆护肤', 'beauty', '化妆品、护肤品', 6),
('其他', 'other', '其他商品', 99);

INSERT OR IGNORE INTO system_configs (config_key, config_value, description, is_public) VALUES
('platform_name', '校园交易平台', '平台名称', 1),
('max_item_images', '5', '商品最多图片数', 1),
('min_credit_score', '60', '最低信用分', 1),
('transaction_timeout_hours', '24', '交易超时时间(小时)', 0),
('ban_credit_score', '30', '封号信用分阈值', 0);

-- ============================================
-- 5. 视图 (SQLite版本)
-- ============================================

CREATE VIEW IF NOT EXISTS v_item_details AS
SELECT 
    i.id, i.title, i.description, i.price, i.original_price, i.condition_type,
    i.location, i.status, i.is_negotiable, i.is_shipped,
    i.view_count, i.favorite_count, i.inquiry_count, i.created_at,
    u.id AS seller_id, u.username AS seller_username, u.avatar_url AS seller_avatar,
    u.seller_rating, u.is_verified AS seller_verified, u.total_sales AS seller_total_sales,
    c.name AS category_name, c.slug AS category_slug
FROM items i
INNER JOIN users u ON i.seller_id = u.id
LEFT JOIN categories c ON i.category_id = c.id;

CREATE VIEW IF NOT EXISTS v_transaction_stats AS
SELECT 
    DATE(created_at) AS transaction_date,
    COUNT(*) AS total_count,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_count,
    SUM(final_amount) AS total_amount,
    AVG(final_amount) AS avg_amount
FROM transactions
GROUP BY DATE(created_at);

CREATE VIEW IF NOT EXISTS v_user_activity AS
SELECT 
    u.id, u.username, u.credit_score, u.seller_rating,
    u.total_sales, u.total_purchases,
    COUNT(DISTINCT i.id) AS active_items,
    COUNT(DISTINCT c.id) AS comment_count,
    COUNT(DISTINCT m.id) AS message_count,
    MAX(u.last_login_at) AS last_active
FROM users u
LEFT JOIN items i ON i.seller_id = u.id AND i.status = 'available'
LEFT JOIN comments c ON c.user_id = u.id
LEFT JOIN messages m ON m.sender_id = u.id
WHERE u.is_active = 1 AND u.is_banned = 0
GROUP BY u.id, u.username, u.credit_score, u.seller_rating, u.total_sales, u.total_purchases;

-- 完成
SELECT 'SQLite schema created successfully!' AS message;
