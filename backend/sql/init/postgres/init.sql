-- ============================================
-- PostgreSQL 校园交易系统完整数据库脚本
-- ============================================
-- 版本: 2.1
-- 日期: 2025-12-01
-- 说明: 修复分区表外键问题

-- ============================================
-- 1. 核心业务表
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    student_id VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    real_name VARCHAR(50),
    
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    
    credit_score INTEGER DEFAULT 100 CHECK (credit_score >= 0 AND credit_score <= 100),
    seller_rating DECIMAL(3,2) DEFAULT 5.00 CHECK (seller_rating >= 0 AND seller_rating <= 5),
    buyer_rating DECIMAL(3,2) DEFAULT 5.00 CHECK (buyer_rating >= 0 AND buyer_rating <= 5),
    
    total_sales INTEGER DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id);
CREATE INDEX IF NOT EXISTS idx_users_credit ON users(credit_score);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active, is_banned);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.credit_score IS '信用分(0-100)';

-- 角色表 (RBAC)
CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
COMMENT ON TABLE roles IS '角色表';

-- 权限表 (RBAC)
CREATE TABLE IF NOT EXISTS permissions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_permissions_name ON permissions(name);
CREATE INDEX IF NOT EXISTS idx_permissions_resource_action ON permissions(resource, action);
COMMENT ON TABLE permissions IS '权限表';

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 1,
    UNIQUE (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);
COMMENT ON TABLE user_roles IS '用户角色关联表';

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id BIGSERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 1,
    UNIQUE (role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions(permission_id);
COMMENT ON TABLE role_permissions IS '角色权限关联表';

-- 用户资料表
CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR(120) NOT NULL,
    phone VARCHAR(32),
    campus VARCHAR(120),
    bio VARCHAR(500),
    avatar_url VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON user_profiles(user_id);
COMMENT ON TABLE user_profiles IS '用户资料表';

-- 商品分类表
CREATE TABLE IF NOT EXISTS categories (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active);

-- 商品表
CREATE TABLE IF NOT EXISTS items (
    id BIGSERIAL PRIMARY KEY,
    seller_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id BIGINT REFERENCES categories(id) ON DELETE SET NULL,
    
    title VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    
    condition_type VARCHAR(20) DEFAULT '二手' CHECK (condition_type IN ('全新', '99新', '95新', '9成新', '二手')),
    location VARCHAR(100),
    contact_info VARCHAR(200),
    
    tags JSONB,
    
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'reserved', 'sold', 'deleted')),
    is_negotiable BOOLEAN DEFAULT FALSE,
    is_shipped BOOLEAN DEFAULT FALSE,
    
    view_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    inquiry_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sold_at TIMESTAMP,
    
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_items_seller ON items(seller_id);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category_id);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_created ON items(created_at);
CREATE INDEX IF NOT EXISTS idx_items_price ON items(price);
CREATE INDEX IF NOT EXISTS idx_items_tags ON items USING GIN(tags);

-- 商品图片表
CREATE TABLE IF NOT EXISTS item_images (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_cover BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_item_images_item ON item_images(item_id);
CREATE INDEX IF NOT EXISTS idx_item_images_cover ON item_images(item_id, is_cover);

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    
    content TEXT NOT NULL,
    
    is_deleted BOOLEAN DEFAULT FALSE,
    is_reported BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_comments_item ON comments(item_id);
CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_comments_created ON comments(created_at);

-- ✅ 修复：交易表 - 不使用分区，使用普通表以支持外键
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(id),
    buyer_id BIGINT NOT NULL REFERENCES users(id),
    seller_id BIGINT NOT NULL REFERENCES users(id),
    
    item_price DECIMAL(10, 2) NOT NULL,
    final_amount DECIMAL(10, 2) NOT NULL,
    
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'contacted', 'meeting', 'completed', 'cancelled')),
    
    buyer_contact VARCHAR(200),
    seller_contact VARCHAR(200),
    meeting_location VARCHAR(200),
    meeting_time TIMESTAMP,
    
    buyer_rating SMALLINT CHECK (buyer_rating >= 1 AND buyer_rating <= 5),
    seller_rating SMALLINT CHECK (seller_rating >= 1 AND seller_rating <= 5),
    buyer_review TEXT,
    seller_review TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    contacted_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_transactions_buyer ON transactions(buyer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_seller ON transactions(seller_id);
CREATE INDEX IF NOT EXISTS idx_transactions_item ON transactions(item_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id BIGINT REFERENCES items(id) ON DELETE SET NULL,
    
    content TEXT NOT NULL,
    
    is_read BOOLEAN DEFAULT FALSE,
    is_deleted_by_sender BOOLEAN DEFAULT FALSE,
    is_deleted_by_receiver BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(sender_id, receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_item ON messages(item_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0,
    
    UNIQUE (user_id, item_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_item ON favorites(item_id);

-- 举报表
CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    reporter_id BIGINT NOT NULL REFERENCES users(id),
    reported_user_id BIGINT REFERENCES users(id),
    item_id BIGINT REFERENCES items(id) ON DELETE CASCADE,
    comment_id BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('fraud', 'fake_item', 'harassment', 'spam', 'other')),
    reason TEXT NOT NULL,
    
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'resolved', 'rejected')),
    admin_note TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id);
CREATE INDEX IF NOT EXISTS idx_reports_reported_user ON reports(reported_user_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

-- ============================================
-- 2. 系统管理表
-- ============================================

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id BIGINT,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table ON audit_logs(table_name, operation);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_record ON audit_logs(table_name, record_id);

-- 同步冲突表
CREATE TABLE IF NOT EXISTS conflict_records (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id BIGINT NOT NULL,
    source_db VARCHAR(50) NOT NULL,
    target_db VARCHAR(50) NOT NULL,
    conflict_type VARCHAR(50) NOT NULL CHECK (conflict_type IN ('version_mismatch', 'data_inconsistency', 'constraint_violation')),
    local_data JSONB,
    remote_data JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    resolution_strategy VARCHAR(50),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conflict_records_resolved ON conflict_records(resolved);
CREATE INDEX IF NOT EXISTS idx_conflict_records_table ON conflict_records(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_conflict_records_created ON conflict_records(created_at);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_configs_key ON system_configs(config_key);

-- ============================================
-- 3. 触发器函数
-- ============================================

-- 更新 updated_at 字段的通用函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用到各表（使用 DROP IF EXISTS 避免重复创建）
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_items_updated_at ON items;
CREATE TRIGGER trg_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_comments_updated_at ON comments;
CREATE TRIGGER trg_comments_updated_at BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_system_configs_updated_at ON system_configs;
CREATE TRIGGER trg_system_configs_updated_at BEFORE UPDATE ON system_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 用户创建审计日志
CREATE OR REPLACE FUNCTION audit_user_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, record_id, new_value)
    VALUES (NEW.id, 'users', 'INSERT', NEW.id, to_jsonb(NEW));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_after_user_insert ON users;
CREATE TRIGGER trg_after_user_insert
AFTER INSERT ON users
FOR EACH ROW EXECUTE FUNCTION audit_user_insert();

-- 评论后更新商品咨询量
CREATE OR REPLACE FUNCTION update_item_inquiry_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE items SET inquiry_count = inquiry_count + 1 WHERE id = NEW.item_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_after_comment_insert ON comments;
CREATE TRIGGER trg_after_comment_insert
AFTER INSERT ON comments
FOR EACH ROW EXECUTE FUNCTION update_item_inquiry_count();

-- 收藏触发器
CREATE OR REPLACE FUNCTION update_item_favorite_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE items SET favorite_count = favorite_count + 1 WHERE id = NEW.item_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE items SET favorite_count = favorite_count - 1 WHERE id = OLD.item_id;
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_favorite_insert ON favorites;
CREATE TRIGGER trg_favorite_insert
AFTER INSERT ON favorites
FOR EACH ROW EXECUTE FUNCTION update_item_favorite_count();

DROP TRIGGER IF EXISTS trg_favorite_delete ON favorites;
CREATE TRIGGER trg_favorite_delete
AFTER DELETE ON favorites
FOR EACH ROW EXECUTE FUNCTION update_item_favorite_count();

-- 交易完成后更新统计
CREATE OR REPLACE FUNCTION update_transaction_complete()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND (OLD.status IS NULL OR OLD.status != 'completed') THEN
        UPDATE users SET total_sales = total_sales + 1 WHERE id = NEW.seller_id;
        UPDATE users SET total_purchases = total_purchases + 1 WHERE id = NEW.buyer_id;
        UPDATE items SET status = 'sold', sold_at = CURRENT_TIMESTAMP WHERE id = NEW.item_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_after_transaction_update ON transactions;
CREATE TRIGGER trg_after_transaction_update
AFTER UPDATE ON transactions
FOR EACH ROW EXECUTE FUNCTION update_transaction_complete();

-- 用户评分更新
CREATE OR REPLACE FUNCTION update_user_rating()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.seller_rating IS NOT NULL AND (OLD.seller_rating IS NULL OR OLD.seller_rating != NEW.seller_rating) THEN
        UPDATE users 
        SET seller_rating = (
            SELECT AVG(seller_rating) 
            FROM transactions 
            WHERE seller_id = NEW.seller_id AND seller_rating IS NOT NULL
        )
        WHERE id = NEW.seller_id;
    END IF;
    
    IF NEW.buyer_rating IS NOT NULL AND (OLD.buyer_rating IS NULL OR OLD.buyer_rating != NEW.buyer_rating) THEN
        UPDATE users 
        SET buyer_rating = (
            SELECT AVG(buyer_rating) 
            FROM transactions 
            WHERE buyer_id = NEW.buyer_id AND buyer_rating IS NOT NULL
        )
        WHERE id = NEW.buyer_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_after_transaction_rating ON transactions;
CREATE TRIGGER trg_after_transaction_rating
AFTER UPDATE ON transactions
FOR EACH ROW EXECUTE FUNCTION update_user_rating();

-- ============================================
-- 4. 存储函数
-- ============================================

-- 创建交易
CREATE OR REPLACE FUNCTION create_transaction(
    p_item_id BIGINT,
    p_buyer_id BIGINT,
    p_buyer_contact VARCHAR(200)
) RETURNS TABLE(transaction_id BIGINT, error_msg TEXT) AS $$
DECLARE
    v_seller_id BIGINT;
    v_item_price DECIMAL(10,2);
    v_item_status VARCHAR(20);
    v_transaction_id BIGINT;
BEGIN
    SELECT seller_id, price, status INTO v_seller_id, v_item_price, v_item_status
    FROM items WHERE id = p_item_id FOR UPDATE;
    
    IF v_item_status != 'available' THEN
        RETURN QUERY SELECT NULL::BIGINT, '商品已下架或售出'::TEXT;
        RETURN;
    END IF;
    
    INSERT INTO transactions (
        item_id, buyer_id, seller_id, item_price, final_amount, 
        buyer_contact, status, contacted_at
    ) VALUES (
        p_item_id, p_buyer_id, v_seller_id, v_item_price, v_item_price,
        p_buyer_contact, 'contacted', CURRENT_TIMESTAMP
    ) RETURNING id INTO v_transaction_id;
    
    UPDATE items SET status = 'reserved' WHERE id = p_item_id;
    
    RETURN QUERY SELECT v_transaction_id, NULL::TEXT;
END;
$$ LANGUAGE plpgsql;

-- 获取用户统计
CREATE OR REPLACE FUNCTION get_user_stats(p_user_id BIGINT)
RETURNS TABLE(
    username VARCHAR,
    credit_score INTEGER,
    seller_rating DECIMAL,
    buyer_rating DECIMAL,
    total_sales INTEGER,
    total_purchases INTEGER,
    active_items BIGINT,
    favorites_count BIGINT,
    transaction_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.username,
        u.credit_score,
        u.seller_rating,
        u.buyer_rating,
        u.total_sales,
        u.total_purchases,
        COUNT(DISTINCT i.id) AS active_items,
        COUNT(DISTINCT f.id) AS favorites_count,
        COUNT(DISTINCT t.id) AS transaction_count
    FROM users u
    LEFT JOIN items i ON i.seller_id = u.id AND i.status = 'available'
    LEFT JOIN favorites f ON f.user_id = u.id
    LEFT JOIN transactions t ON (t.buyer_id = u.id OR t.seller_id = u.id)
    WHERE u.id = p_user_id
    GROUP BY u.id, u.username, u.credit_score, u.seller_rating, u.buyer_rating, u.total_sales, u.total_purchases;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 5. 初始化数据
-- ============================================

INSERT INTO categories (name, slug, description, sort_order) VALUES
('全部', 'all', '所有商品', 0),
('数码产品', 'electronics', '电脑、手机、平板等', 1),
('图书教材', 'books', '教材、课外书、杂志等', 2),
('生活用品', 'daily', '日用品、家居用品', 3),
('运动装备', 'sports', '运动器材、健身用品', 4),
('服装鞋包', 'fashion', '衣服、鞋子、包包', 5),
('美妆护肤', 'beauty', '化妆品、护肤品', 6),
('其他', 'other', '其他商品', 99)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO system_configs (config_key, config_value, description, is_public) VALUES
('platform_name', '校园交易平台', '平台名称', TRUE),
('max_item_images', '5', '商品最多图片数', TRUE),
('min_credit_score', '60', '最低信用分', TRUE),
('transaction_timeout_hours', '24', '交易超时时间(小时)', FALSE),
('ban_credit_score', '30', '封号信用分阈值', FALSE)
ON CONFLICT (config_key) DO UPDATE SET config_value = EXCLUDED.config_value;

-- ============================================
-- 6. 视图
-- ============================================

CREATE OR REPLACE VIEW v_item_details AS
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

CREATE OR REPLACE VIEW v_transaction_stats AS
SELECT 
    DATE(created_at) AS transaction_date,
    COUNT(*) AS total_count,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_count,
    SUM(final_amount) AS total_amount,
    AVG(final_amount) AS avg_amount
FROM transactions
GROUP BY DATE(created_at);

CREATE OR REPLACE VIEW v_user_activity AS
SELECT 
    u.id, u.username, u.credit_score, u.seller_rating, u.total_sales, u.total_purchases,
    COUNT(DISTINCT i.id) AS active_items,
    COUNT(DISTINCT c.id) AS comment_count,
    COUNT(DISTINCT m.id) AS message_count,
    MAX(u.last_login_at) AS last_active
FROM users u
LEFT JOIN items i ON i.seller_id = u.id AND i.status = 'available'
LEFT JOIN comments c ON c.user_id = u.id
LEFT JOIN messages m ON m.sender_id = u.id
WHERE u.is_active = TRUE AND u.is_banned = FALSE
GROUP BY u.id, u.username, u.credit_score, u.seller_rating, u.total_sales, u.total_purchases;

-- ============================================
-- 7. 扩展关联表
-- ============================================

-- 用户关注表
CREATE TABLE IF NOT EXISTS user_follows (
    id BIGSERIAL PRIMARY KEY,
    follower_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0,
    UNIQUE (follower_id, following_id),
    CHECK (follower_id != following_id)
);
CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following ON user_follows(following_id);

-- 商品浏览历史表
CREATE TABLE IF NOT EXISTS item_view_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    view_duration INTEGER DEFAULT 0,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_item_view_history_user ON item_view_history(user_id);
CREATE INDEX IF NOT EXISTS idx_item_view_history_item ON item_view_history(item_id);

-- 用户地址表
CREATE TABLE IF NOT EXISTS user_addresses (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address_type VARCHAR(20) DEFAULT 'dormitory' CHECK (address_type IN ('dormitory', 'home', 'other')),
    building VARCHAR(50),
    room VARCHAR(20),
    detail_address VARCHAR(200),
    contact_name VARCHAR(50),
    contact_phone VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_user_addresses_user ON user_addresses(user_id);

-- 商品价格历史表
CREATE TABLE IF NOT EXISTS item_price_history (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    old_price DECIMAL(10, 2),
    new_price DECIMAL(10, 2) NOT NULL,
    change_reason VARCHAR(200),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_item_price_history_item ON item_price_history(item_id);

-- 评论点赞表
CREATE TABLE IF NOT EXISTS comment_likes (
    id BIGSERIAL PRIMARY KEY,
    comment_id BIGINT NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0,
    UNIQUE (comment_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_comment_likes_comment ON comment_likes(comment_id);

-- 消息附件表
CREATE TABLE IF NOT EXISTS message_attachments (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_type VARCHAR(20) DEFAULT 'image' CHECK (file_type IN ('image', 'video', 'document', 'other')),
    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(200),
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_message_attachments_message ON message_attachments(message_id);

-- 举报处理记录表
CREATE TABLE IF NOT EXISTS report_actions (
    id BIGSERIAL PRIMARY KEY,
    report_id BIGINT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    admin_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('warn', 'delete_content', 'suspend_user', 'ban_user', 'reject')),
    action_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_report_actions_report ON report_actions(report_id);

-- ✅ 修复：交易评价图片表 - 现在可以正常引用 transactions 表
CREATE TABLE IF NOT EXISTS transaction_review_images (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    reviewer_type VARCHAR(10) NOT NULL CHECK (reviewer_type IN ('buyer', 'seller')),
    image_url VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_transaction_review_images_transaction ON transaction_review_images(transaction_id);

-- 系统通知表
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('system', 'transaction', 'message', 'comment', 'follow', 'like')),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    related_id BIGINT,
    related_type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(user_id, is_read);

-- 搜索历史表
CREATE TABLE IF NOT EXISTS search_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    keyword VARCHAR(200) NOT NULL,
    result_count INTEGER DEFAULT 0,
    clicked_item_id BIGINT REFERENCES items(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_keyword ON search_history(keyword);

-- ✅ 修复：信用分变更记录表 - 现在可以正常引用 transactions 表
CREATE TABLE IF NOT EXISTS credit_score_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_score INTEGER NOT NULL,
    new_score INTEGER NOT NULL,
    change_amount INTEGER NOT NULL,
    change_reason VARCHAR(200) NOT NULL,
    related_transaction_id BIGINT REFERENCES transactions(id) ON DELETE SET NULL,
    related_report_id BIGINT REFERENCES reports(id) ON DELETE SET NULL,
    admin_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_credit_score_history_user ON credit_score_history(user_id);

-- 同步任务表
CREATE TABLE IF NOT EXISTS sync_tasks (
    id BIGSERIAL PRIMARY KEY,
    task_type VARCHAR(30) NOT NULL CHECK (task_type IN ('full_sync', 'incremental_sync', 'conflict_resolution')),
    source_db VARCHAR(50) NOT NULL,
    target_db VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    total_records INTEGER DEFAULT 0,
    synced_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sync_tasks_status ON sync_tasks(status);

-- 性能监控表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_type VARCHAR(30) NOT NULL CHECK (metric_type IN ('query_time', 'connection_pool', 'sync_latency', 'error_rate')),
    db_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 2) NOT NULL,
    threshold_value DECIMAL(10, 2),
    is_alert BOOLEAN DEFAULT FALSE,
    details JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_db ON performance_metrics(db_name);

SELECT 'PostgreSQL schema created successfully!' AS message;

-- ============================================
-- Sync相关表
-- ============================================

-- sync_configs table
CREATE TABLE IF NOT EXISTS sync_configs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(64) NOT NULL,
    target VARCHAR(64) NOT NULL,
    mode VARCHAR(32) NOT NULL DEFAULT 'realtime',
    interval_seconds INTEGER NOT NULL DEFAULT 300,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

-- sync_logs table
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    config_id INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NULL,
    stats JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0,
    FOREIGN KEY (config_id) REFERENCES sync_configs(id)
);

-- conflict_records table
CREATE TABLE IF NOT EXISTS conflict_records (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(128) NOT NULL,
    record_id VARCHAR(64) NOT NULL,
    source VARCHAR(64) NOT NULL,
    target VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    resolved_by INTEGER NULL,
    resolved_at TIMESTAMP NULL,
    resolution_note VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0,
    FOREIGN KEY (resolved_by) REFERENCES users(id)
);

-- daily_stats table
CREATE TABLE IF NOT EXISTS daily_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    sync_success_count INTEGER NOT NULL DEFAULT 0,
    sync_conflict_count INTEGER NOT NULL DEFAULT 0,
    ai_request_count INTEGER NOT NULL DEFAULT 0,
    inventory_changes INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

-- 插入默认角色
INSERT INTO roles (name, description) VALUES
('admin', '系统管理员'),
('moderator', '内容审核员'),
('user', '普通用户'),
('seller', '认证卖家')
ON CONFLICT (name) DO NOTHING;

-- 插入默认权限
INSERT INTO permissions (name, resource, action, description) VALUES
('user:read', 'user', 'read', '查看用户信息'),
('user:write', 'user', 'write', '修改用户信息'),
('user:delete', 'user', 'delete', '删除用户'),
('item:read', 'item', 'read', '查看商品'),
('item:write', 'item', 'write', '发布/修改商品'),
('item:delete', 'item', 'delete', '删除商品'),
('order:read', 'order', 'read', '查看订单'),
('order:write', 'order', 'write', '创建/修改订单'),
('admin:access', 'admin', 'access', '访问管理后台'),
('report:handle', 'report', 'handle', '处理举报')
ON CONFLICT (name) DO NOTHING;

-- 角色权限关联
INSERT INTO role_permissions (role_id, permission_id) VALUES
-- admin 拥有所有权限
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
-- moderator 拥有审核权限
(2, 1), (2, 4), (2, 6), (2, 7), (2, 9), (2, 10),
-- user 拥有基本权限
(3, 1), (3, 4), (3, 5), (3, 7), (3, 8),
-- seller 拥有卖家权限
(4, 1), (4, 4), (4, 5), (4, 6), (4, 7), (4, 8)
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ============================================
-- 同步配置示例数据
-- ============================================
INSERT INTO sync_configs (id, source, target, mode, interval_seconds, enabled, last_run_at) VALUES
(1, 'mysql', 'mariadb', 'realtime', 60, true, NOW() - INTERVAL '5 minutes'),
(2, 'mysql', 'postgres', 'scheduled', 300, true, NOW() - INTERVAL '10 minutes'),
(3, 'mysql', 'sqlite', 'manual', 3600, true, NOW() - INTERVAL '1 hour'),
(4, 'mariadb', 'postgres', 'realtime', 60, true, NOW() - INTERVAL '3 minutes'),
(5, 'postgres', 'sqlite', 'scheduled', 600, false, NOW() - INTERVAL '2 hours')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 同步日志示例数据
-- ============================================
INSERT INTO sync_logs (config_id, status, started_at, completed_at, stats) VALUES
(1, 'completed', NOW() - INTERVAL '5 minutes', NOW() - INTERVAL '4 minutes', '{"rows_synced": 156, "conflicts": 2}'),
(2, 'completed', NOW() - INTERVAL '10 minutes', NOW() - INTERVAL '8 minutes', '{"rows_synced": 89, "conflicts": 0}'),
(1, 'completed', NOW() - INTERVAL '15 minutes', NOW() - INTERVAL '14 minutes', '{"rows_synced": 203, "conflicts": 1}'),
(3, 'completed', NOW() - INTERVAL '1 hour', NOW() - INTERVAL '58 minutes', '{"rows_synced": 45, "conflicts": 0}'),
(4, 'completed', NOW() - INTERVAL '3 minutes', NOW() - INTERVAL '2 minutes', '{"rows_synced": 78, "conflicts": 3}'),
(1, 'completed', NOW() - INTERVAL '20 minutes', NOW() - INTERVAL '19 minutes', '{"rows_synced": 112, "conflicts": 0}'),
(2, 'failed', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour 55 minutes', '{"error": "Connection timeout"}'),
(1, 'completed', NOW() - INTERVAL '25 minutes', NOW() - INTERVAL '24 minutes', '{"rows_synced": 67, "conflicts": 1}'),
(4, 'completed', NOW() - INTERVAL '8 minutes', NOW() - INTERVAL '7 minutes', '{"rows_synced": 134, "conflicts": 0}'),
(1, 'running', NOW() - INTERVAL '1 minute', NULL, '{"rows_synced": 0, "conflicts": 0}');

-- ============================================
-- 每日统计示例数据 (最近14天)
-- ============================================
INSERT INTO daily_stats (stat_date, sync_success_count, sync_conflict_count, ai_request_count, inventory_changes) VALUES
(CURRENT_DATE - INTERVAL '13 days', 245, 12, 89, 156),
(CURRENT_DATE - INTERVAL '12 days', 312, 8, 102, 203),
(CURRENT_DATE - INTERVAL '11 days', 287, 15, 78, 189),
(CURRENT_DATE - INTERVAL '10 days', 198, 5, 134, 145),
(CURRENT_DATE - INTERVAL '9 days', 356, 18, 156, 267),
(CURRENT_DATE - INTERVAL '8 days', 423, 22, 189, 312),
(CURRENT_DATE - INTERVAL '7 days', 389, 9, 167, 278),
(CURRENT_DATE - INTERVAL '6 days', 267, 11, 145, 198),
(CURRENT_DATE - INTERVAL '5 days', 445, 14, 201, 334),
(CURRENT_DATE - INTERVAL '4 days', 378, 7, 178, 289),
(CURRENT_DATE - INTERVAL '3 days', 412, 16, 223, 356),
(CURRENT_DATE - INTERVAL '2 days', 356, 10, 198, 267),
(CURRENT_DATE - INTERVAL '1 day', 489, 13, 245, 398),
(CURRENT_DATE, 234, 6, 112, 178)
ON CONFLICT (stat_date) DO NOTHING;

-- ============================================
-- 冲突记录示例数据
-- ============================================
INSERT INTO conflict_records (table_name, record_id, source, target, status, payload) VALUES
('users', '15', 'mysql', 'mariadb', 'pending', '{"field": "email", "mysql_value": "user15@a.edu", "mariadb_value": "user15@b.edu"}'),
('items', '42', 'mysql', 'postgres', 'pending', '{"field": "price", "mysql_value": 199.00, "postgres_value": 189.00}'),
('items', '78', 'mariadb', 'postgres', 'resolved', '{"field": "status", "mariadb_value": "active", "postgres_value": "sold"}'),
('transactions', '123', 'mysql', 'mariadb', 'pending', '{"field": "status", "mysql_value": "completed", "mariadb_value": "pending"}'),
('users', '88', 'postgres', 'sqlite', 'resolved', '{"field": "credit_score", "postgres_value": 85, "sqlite_value": 90}');

-- ============================================
-- 管理员账户 (密码: admin123)
-- ============================================
INSERT INTO users (id, username, email, password_hash, is_active, is_verified, credit_score) VALUES
(9999, 'admin', 'admin@campus.edu', '$5$rounds=535000$abcdefghijklmnop$Y8L5Y1N3PxM7Q2R4T6V8W0X2Z4A6C8E0G2I4K6M8O0', true, true, 100)
ON CONFLICT (id) DO NOTHING;

-- 为管理员分配admin角色
INSERT INTO user_roles (user_id, role_id) 
SELECT 9999, id FROM roles WHERE name = 'admin'
ON CONFLICT (user_id, role_id) DO NOTHING;

-- ============================================
-- 性能指标示例数据
-- ============================================
INSERT INTO performance_metrics (db_name, metric_type, metric_value, recorded_at) VALUES
('mysql', 'query_time_avg', 12.5, NOW() - INTERVAL '1 hour'),
('mysql', 'connections', 45, NOW() - INTERVAL '1 hour'),
('mysql', 'query_time_avg', 15.2, NOW() - INTERVAL '30 minutes'),
('mysql', 'connections', 52, NOW() - INTERVAL '30 minutes'),
('mysql', 'query_time_avg', 11.8, NOW()),
('mysql', 'connections', 48, NOW()),
('mariadb', 'query_time_avg', 10.3, NOW() - INTERVAL '1 hour'),
('mariadb', 'connections', 38, NOW() - INTERVAL '1 hour'),
('mariadb', 'query_time_avg', 13.1, NOW() - INTERVAL '30 minutes'),
('mariadb', 'connections', 42, NOW() - INTERVAL '30 minutes'),
('mariadb', 'query_time_avg', 9.7, NOW()),
('mariadb', 'connections', 40, NOW()),
('postgres', 'query_time_avg', 8.9, NOW() - INTERVAL '1 hour'),
('postgres', 'connections', 32, NOW() - INTERVAL '1 hour'),
('postgres', 'query_time_avg', 11.2, NOW() - INTERVAL '30 minutes'),
('postgres', 'connections', 35, NOW() - INTERVAL '30 minutes'),
('postgres', 'query_time_avg', 7.5, NOW()),
('postgres', 'connections', 30, NOW()),
('sqlite', 'query_time_avg', 5.2, NOW() - INTERVAL '1 hour'),
('sqlite', 'connections', 1, NOW() - INTERVAL '1 hour'),
('sqlite', 'query_time_avg', 6.1, NOW() - INTERVAL '30 minutes'),
('sqlite', 'connections', 1, NOW() - INTERVAL '30 minutes'),
('sqlite', 'query_time_avg', 4.8, NOW()),
('sqlite', 'connections', 1, NOW());

SELECT 'PostgreSQL sample data inserted successfully!' AS message;
