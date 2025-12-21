-- ============================================
-- SQLite 校园交易系统完整数据库脚本
-- ============================================
-- 版本: 2.1
-- 日期: 2025-12-01
-- 说明: SQLite专用语法，无触发器和存储过程

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

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_credit ON users(credit_score);

-- 角色表 (RBAC)
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- 权限表 (RBAC)
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_permissions_name ON permissions(name);
CREATE INDEX IF NOT EXISTS idx_permissions_resource_action ON permissions(resource, action);

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 1,
    UNIQUE (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 1,
    UNIQUE (role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions(permission_id);

-- 用户资料表
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    phone TEXT,
    campus TEXT,
    bio TEXT,
    avatar_url TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON user_profiles(user_id);

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
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);

-- 商品表
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    original_price REAL,
    condition_type TEXT DEFAULT '二手' CHECK (condition_type IN ('全新', '99新', '95新', '9成新', '二手')),
    location TEXT,
    contact_info TEXT,
    tags TEXT,
    status TEXT DEFAULT 'available' CHECK (status IN ('available', 'reserved', 'sold', 'deleted')),
    is_negotiable INTEGER DEFAULT 0,
    is_shipped INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    inquiry_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sold_at TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_items_seller ON items(seller_id);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category_id);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_created ON items(created_at);

-- 商品图片表
CREATE TABLE IF NOT EXISTS item_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_cover INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_item_images_item ON item_images(item_id);

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0,
    is_reported INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_comments_item ON comments(item_id);
CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(user_id);

-- 交易表
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    buyer_id INTEGER NOT NULL REFERENCES users(id),
    seller_id INTEGER NOT NULL REFERENCES users(id),
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
    updated_at TEXT DEFAULT (datetime('now')),
    contacted_at TEXT,
    completed_at TEXT,
    cancelled_at TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_transactions_buyer ON transactions(buyer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_seller ON transactions(seller_id);
CREATE INDEX IF NOT EXISTS idx_transactions_item ON transactions(item_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES items(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    is_deleted_by_sender INTEGER DEFAULT 0,
    is_deleted_by_receiver INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    read_at TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id);

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0,
    UNIQUE (user_id, item_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_item ON favorites(item_id);

-- 举报表
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL REFERENCES users(id),
    reported_user_id INTEGER REFERENCES users(id),
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL CHECK (report_type IN ('fraud', 'fake_item', 'harassment', 'spam', 'other')),
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'resolved', 'rejected')),
    admin_note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    resolved_at TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

-- ============================================
-- 2. 系统管理表
-- ============================================

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table ON audit_logs(table_name);

-- 同步冲突表
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
    resolved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolution_strategy TEXT,
    resolved_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conflict_records_resolved ON conflict_records(resolved);

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

-- ============================================
-- 3. 扩展关联表
-- ============================================

CREATE TABLE IF NOT EXISTS user_follows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0,
    UNIQUE (follower_id, following_id),
    CHECK (follower_id != following_id)
);

CREATE TABLE IF NOT EXISTS item_view_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    view_duration INTEGER DEFAULT 0,
    viewed_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address_type TEXT DEFAULT 'dormitory' CHECK (address_type IN ('dormitory', 'home', 'other')),
    building TEXT,
    room TEXT,
    detail_address TEXT,
    contact_name TEXT,
    contact_phone TEXT,
    is_default INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS item_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    old_price REAL,
    new_price REAL NOT NULL,
    change_reason TEXT,
    changed_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS comment_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id INTEGER NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0,
    UNIQUE (comment_id, user_id)
);

CREATE TABLE IF NOT EXISTS message_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_type TEXT DEFAULT 'image' CHECK (file_type IN ('image', 'video', 'document', 'other')),
    file_url TEXT NOT NULL,
    file_name TEXT,
    file_size INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS report_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    admin_id INTEGER NOT NULL REFERENCES users(id),
    action_type TEXT NOT NULL CHECK (action_type IN ('warn', 'delete_content', 'suspend_user', 'ban_user', 'reject')),
    action_note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transaction_review_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    reviewer_type TEXT NOT NULL CHECK (reviewer_type IN ('buyer', 'seller')),
    image_url TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('system', 'transaction', 'message', 'comment', 'follow', 'like')),
    title TEXT NOT NULL,
    content TEXT,
    related_id INTEGER,
    related_type TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    keyword TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    clicked_item_id INTEGER REFERENCES items(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS credit_score_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_score INTEGER NOT NULL,
    new_score INTEGER NOT NULL,
    change_amount INTEGER NOT NULL,
    change_reason TEXT NOT NULL,
    related_transaction_id INTEGER REFERENCES transactions(id) ON DELETE SET NULL,
    related_report_id INTEGER REFERENCES reports(id) ON DELETE SET NULL,
    admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL CHECK (task_type IN ('full_sync', 'incremental_sync', 'conflict_resolution')),
    source_db TEXT NOT NULL,
    target_db TEXT NOT NULL,
    table_name TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    total_records INTEGER DEFAULT 0,
    synced_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL CHECK (metric_type IN ('query_time', 'connection_pool', 'sync_latency', 'error_rate')),
    db_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    threshold_value REAL,
    is_alert INTEGER DEFAULT 0,
    details TEXT,
    recorded_at TEXT DEFAULT (datetime('now'))
);

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

SELECT 'SQLite schema created successfully!' AS message;
