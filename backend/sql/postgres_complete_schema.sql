-- ============================================
-- PostgreSQL 校园交易系统完整数据库脚本
-- ============================================
-- 版本: 2.0
-- 日期: 2025-11-18
-- 说明: 包含所有表、索引、触发器、函数、事务示例

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

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_student_id ON users(student_id);
CREATE INDEX idx_users_credit ON users(credit_score);
CREATE INDEX idx_users_active ON users(is_active, is_banned);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.credit_score IS '信用分(0-100)';

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
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_active ON categories(is_active);

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

CREATE INDEX idx_items_seller ON items(seller_id);
CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_created ON items(created_at);
CREATE INDEX idx_items_price ON items(price);
CREATE INDEX idx_items_tags ON items USING GIN(tags);

-- 全文搜索索引
CREATE INDEX idx_items_search ON items USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- 商品图片表
CREATE TABLE IF NOT EXISTS item_images (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_cover BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_item_images_item ON item_images(item_id);
CREATE INDEX idx_item_images_cover ON item_images(item_id, is_cover);

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

CREATE INDEX idx_comments_item ON comments(item_id);
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
CREATE INDEX idx_comments_created ON comments(created_at);

-- 交易表 (带分区)
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL,
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
    contacted_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    sync_version INTEGER DEFAULT 0,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE IF NOT EXISTS transactions_2024 PARTITION OF transactions
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE IF NOT EXISTS transactions_2025 PARTITION OF transactions
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS transactions_2026 PARTITION OF transactions
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE TABLE IF NOT EXISTS transactions_default PARTITION OF transactions DEFAULT;

CREATE INDEX idx_transactions_buyer ON transactions(buyer_id);
CREATE INDEX idx_transactions_seller ON transactions(seller_id);
CREATE INDEX idx_transactions_item ON transactions(item_id);
CREATE INDEX idx_transactions_status ON transactions(status);

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
    read_at TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_receiver ON messages(receiver_id);
CREATE INDEX idx_messages_conversation ON messages(sender_id, receiver_id);
CREATE INDEX idx_messages_item ON messages(item_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0,
    
    UNIQUE (user_id, item_id)
);

CREATE INDEX idx_favorites_user ON favorites(user_id);
CREATE INDEX idx_favorites_item ON favorites(item_id);

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
    resolved_at TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_reports_reporter ON reports(reporter_id);
CREATE INDEX idx_reports_reported_user ON reports(reported_user_id);
CREATE INDEX idx_reports_status ON reports(status);

-- ============================================
-- 2. 系统管理表
-- ============================================

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id BIGINT,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name, operation);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_record ON audit_logs(table_name, record_id);

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
    resolved_by BIGINT,
    resolution_strategy VARCHAR(50),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conflict_records_resolved ON conflict_records(resolved);
CREATE INDEX idx_conflict_records_table ON conflict_records(table_name, record_id);
CREATE INDEX idx_conflict_records_created ON conflict_records(created_at);

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

CREATE INDEX idx_system_configs_key ON system_configs(config_key);

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

-- 应用到各表
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_comments_updated_at BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

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

CREATE TRIGGER trg_favorite_insert
AFTER INSERT ON favorites
FOR EACH ROW EXECUTE FUNCTION update_item_favorite_count();

CREATE TRIGGER trg_favorite_delete
AFTER DELETE ON favorites
FOR EACH ROW EXECUTE FUNCTION update_item_favorite_count();

-- 交易完成后更新统计
CREATE OR REPLACE FUNCTION update_transaction_complete()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND (OLD.status IS NULL OR OLD.status != 'completed') THEN
        -- 更新卖家销售数
        UPDATE users SET total_sales = total_sales + 1 WHERE id = NEW.seller_id;
        -- 更新买家购买数
        UPDATE users SET total_purchases = total_purchases + 1 WHERE id = NEW.buyer_id;
        -- 更新商品状态
        UPDATE items SET status = 'sold', sold_at = CURRENT_TIMESTAMP WHERE id = NEW.item_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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

CREATE TRIGGER trg_after_transaction_rating
AFTER UPDATE ON transactions
FOR EACH ROW EXECUTE FUNCTION update_user_rating();

-- ============================================
-- 4. 存储函数(相当于MySQL的存储过程)
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
    -- 检查商品状态
    SELECT seller_id, price, status INTO v_seller_id, v_item_price, v_item_status
    FROM items WHERE id = p_item_id FOR UPDATE;
    
    IF v_item_status != 'available' THEN
        RETURN QUERY SELECT NULL::BIGINT, '商品已下架或售出'::TEXT;
        RETURN;
    END IF;
    
    -- 创建交易记录
    INSERT INTO transactions (
        item_id, buyer_id, seller_id, item_price, final_amount, 
        buyer_contact, status, contacted_at
    ) VALUES (
        p_item_id, p_buyer_id, v_seller_id, v_item_price, v_item_price,
        p_buyer_contact, 'contacted', CURRENT_TIMESTAMP
    ) RETURNING id INTO v_transaction_id;
    
    -- 更新商品状态
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

-- 搜索商品
CREATE OR REPLACE FUNCTION search_items(
    p_keyword TEXT,
    p_category_id BIGINT,
    p_min_price DECIMAL,
    p_max_price DECIMAL,
    p_condition_type VARCHAR,
    p_offset INTEGER,
    p_limit INTEGER
) RETURNS TABLE(
    id BIGINT,
    title VARCHAR,
    price DECIMAL,
    seller_username VARCHAR,
    seller_rating DECIMAL,
    is_verified BOOLEAN,
    category_name VARCHAR,
    cover_image VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.title,
        i.price,
        u.username AS seller_username,
        u.seller_rating,
        u.is_verified,
        c.name AS category_name,
        (SELECT image_url FROM item_images WHERE item_id = i.id AND is_cover = TRUE LIMIT 1) AS cover_image
    FROM items i
    INNER JOIN users u ON i.seller_id = u.id
    LEFT JOIN categories c ON i.category_id = c.id
    WHERE i.status = 'available'
        AND (p_keyword IS NULL OR to_tsvector('english', i.title || ' ' || COALESCE(i.description, '')) @@ plainto_tsquery('english', p_keyword))
        AND (p_category_id IS NULL OR i.category_id = p_category_id)
        AND (p_min_price IS NULL OR i.price >= p_min_price)
        AND (p_max_price IS NULL OR i.price <= p_max_price)
        AND (p_condition_type IS NULL OR i.condition_type = p_condition_type)
    ORDER BY i.created_at DESC
    OFFSET p_offset LIMIT p_limit;
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

-- 商品详情视图
CREATE OR REPLACE VIEW v_item_details AS
SELECT 
    i.id,
    i.title,
    i.description,
    i.price,
    i.original_price,
    i.condition_type,
    i.location,
    i.status,
    i.is_negotiable,
    i.is_shipped,
    i.view_count,
    i.favorite_count,
    i.inquiry_count,
    i.created_at,
    u.id AS seller_id,
    u.username AS seller_username,
    u.avatar_url AS seller_avatar,
    u.seller_rating,
    u.is_verified AS seller_verified,
    u.total_sales AS seller_total_sales,
    c.name AS category_name,
    c.slug AS category_slug
FROM items i
INNER JOIN users u ON i.seller_id = u.id
LEFT JOIN categories c ON i.category_id = c.id;

-- 交易统计视图
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

-- 用户活跃度视图
CREATE OR REPLACE VIEW v_user_activity AS
SELECT 
    u.id,
    u.username,
    u.credit_score,
    u.seller_rating,
    u.total_sales,
    u.total_purchases,
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

-- 完成
SELECT 'PostgreSQL schema created successfully!' AS message;
