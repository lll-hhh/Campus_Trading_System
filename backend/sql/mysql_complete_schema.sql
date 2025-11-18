-- ============================================
-- MySQL/MariaDB 校园交易系统完整数据库脚本
-- ============================================
-- 版本: 2.0
-- 日期: 2025-11-18
-- 说明: 包含所有表、索引、触发器、存储过程、事务示例

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 核心业务表
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '校园邮箱',
    student_id VARCHAR(20) UNIQUE COMMENT '学号',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    phone VARCHAR(20) COMMENT '手机号',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    real_name VARCHAR(50) COMMENT '真实姓名',
    
    -- 状态字段
    is_active BOOLEAN DEFAULT TRUE COMMENT '账号是否激活',
    is_verified BOOLEAN DEFAULT FALSE COMMENT '是否实名认证',
    is_banned BOOLEAN DEFAULT FALSE COMMENT '是否被封禁',
    
    -- 信用评分
    credit_score INT DEFAULT 100 COMMENT '信用分(0-100)',
    seller_rating DECIMAL(3,2) DEFAULT 5.00 COMMENT '卖家评分(0-5)',
    buyer_rating DECIMAL(3,2) DEFAULT 5.00 COMMENT '买家评分(0-5)',
    
    -- 统计字段
    total_sales INT DEFAULT 0 COMMENT '总销售数',
    total_purchases INT DEFAULT 0 COMMENT '总购买数',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    
    -- 同步字段
    sync_version INT DEFAULT 0 COMMENT '同步版本号',
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_student_id (student_id),
    INDEX idx_credit (credit_score),
    INDEX idx_active (is_active, is_banned)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 商品分类表
CREATE TABLE IF NOT EXISTS categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '分类名称',
    slug VARCHAR(50) UNIQUE NOT NULL COMMENT '分类标识',
    description TEXT COMMENT '分类描述',
    icon VARCHAR(100) COMMENT '图标',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 0,
    INDEX idx_slug (slug),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';

-- 商品表
CREATE TABLE IF NOT EXISTS items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    seller_id BIGINT NOT NULL COMMENT '卖家ID',
    category_id BIGINT COMMENT '分类ID',
    
    -- 商品信息
    title VARCHAR(200) NOT NULL COMMENT '商品标题',
    description TEXT COMMENT '商品描述',
    price DECIMAL(10, 2) NOT NULL COMMENT '价格',
    original_price DECIMAL(10, 2) COMMENT '原价',
    
    -- 商品属性
    condition_type ENUM('全新', '99新', '95新', '9成新', '二手') DEFAULT '二手' COMMENT '成色',
    location VARCHAR(100) COMMENT '交易地点',
    contact_info VARCHAR(200) COMMENT '联系方式(加密)',
    
    -- 标签
    tags JSON COMMENT '商品标签数组',
    
    -- 状态
    status ENUM('available', 'reserved', 'sold', 'deleted') DEFAULT 'available' COMMENT '商品状态',
    is_negotiable BOOLEAN DEFAULT FALSE COMMENT '是否可议价',
    is_shipped BOOLEAN DEFAULT FALSE COMMENT '是否包邮',
    
    -- 统计
    view_count INT DEFAULT 0 COMMENT '浏览量',
    favorite_count INT DEFAULT 0 COMMENT '收藏量',
    inquiry_count INT DEFAULT 0 COMMENT '咨询量',
    
    -- 时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sold_at TIMESTAMP NULL COMMENT '售出时间',
    
    sync_version INT DEFAULT 0,
    
    INDEX idx_seller (seller_id),
    INDEX idx_category (category_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at),
    INDEX idx_price (price),
    FULLTEXT idx_title_desc (title, description),
    
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';

-- 商品图片表
CREATE TABLE IF NOT EXISTS item_images (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    item_id BIGINT NOT NULL,
    image_url VARCHAR(500) NOT NULL COMMENT '图片URL',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_cover BOOLEAN DEFAULT FALSE COMMENT '是否封面',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 0,
    
    INDEX idx_item (item_id),
    INDEX idx_cover (item_id, is_cover),
    
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品图片表';

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    item_id BIGINT NOT NULL COMMENT '商品ID',
    user_id BIGINT NOT NULL COMMENT '评论用户ID',
    parent_id BIGINT NULL COMMENT '父评论ID(回复)',
    
    content TEXT NOT NULL COMMENT '评论内容',
    
    -- 状态
    is_deleted BOOLEAN DEFAULT FALSE,
    is_reported BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 0,
    
    INDEX idx_item (item_id),
    INDEX idx_user (user_id),
    INDEX idx_parent (parent_id),
    INDEX idx_created (created_at),
    
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论表';

-- 交易表
CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    item_id BIGINT NOT NULL,
    buyer_id BIGINT NOT NULL,
    seller_id BIGINT NOT NULL,
    
    -- 金额
    item_price DECIMAL(10, 2) NOT NULL COMMENT '商品价格',
    final_amount DECIMAL(10, 2) NOT NULL COMMENT '最终成交价',
    
    -- 交易状态
    status ENUM('pending', 'contacted', 'meeting', 'completed', 'cancelled') DEFAULT 'pending' COMMENT '交易状态',
    
    -- 联系信息
    buyer_contact VARCHAR(200) COMMENT '买家联系方式(加密)',
    seller_contact VARCHAR(200) COMMENT '卖家联系方式(加密)',
    meeting_location VARCHAR(200) COMMENT '约定见面地点',
    meeting_time TIMESTAMP NULL COMMENT '约定见面时间',
    
    -- 评价
    buyer_rating TINYINT COMMENT '买家评分1-5',
    seller_rating TINYINT COMMENT '卖家评分1-5',
    buyer_review TEXT COMMENT '买家评价',
    seller_review TEXT COMMENT '卖家评价',
    
    -- 时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '交易创建时间',
    contacted_at TIMESTAMP NULL COMMENT '获取联系方式时间',
    completed_at TIMESTAMP NULL COMMENT '交易完成时间',
    cancelled_at TIMESTAMP NULL COMMENT '取消时间',
    
    sync_version INT DEFAULT 0,
    
    INDEX idx_buyer (buyer_id),
    INDEX idx_seller (seller_id),
    INDEX idx_item (item_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at),
    
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (buyer_id) REFERENCES users(id),
    FOREIGN KEY (seller_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易表'
PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sender_id BIGINT NOT NULL,
    receiver_id BIGINT NOT NULL,
    item_id BIGINT COMMENT '关联商品',
    
    content TEXT NOT NULL COMMENT '消息内容',
    
    is_read BOOLEAN DEFAULT FALSE,
    is_deleted_by_sender BOOLEAN DEFAULT FALSE,
    is_deleted_by_receiver BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    sync_version INT DEFAULT 0,
    
    INDEX idx_sender (sender_id),
    INDEX idx_receiver (receiver_id),
    INDEX idx_conversation (sender_id, receiver_id),
    INDEX idx_item (item_id),
    INDEX idx_created (created_at),
    
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表';

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 0,
    
    UNIQUE KEY uk_user_item (user_id, item_id),
    INDEX idx_user (user_id),
    INDEX idx_item (item_id),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏表';

-- 举报表
CREATE TABLE IF NOT EXISTS reports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reporter_id BIGINT NOT NULL COMMENT '举报人',
    reported_user_id BIGINT COMMENT '被举报用户',
    item_id BIGINT COMMENT '被举报商品',
    comment_id BIGINT COMMENT '被举报评论',
    
    report_type ENUM('fraud', 'fake_item', 'harassment', 'spam', 'other') NOT NULL,
    reason TEXT NOT NULL,
    
    status ENUM('pending', 'processing', 'resolved', 'rejected') DEFAULT 'pending',
    admin_note TEXT COMMENT '管理员备注',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    sync_version INT DEFAULT 0,
    
    INDEX idx_reporter (reporter_id),
    INDEX idx_reported_user (reported_user_id),
    INDEX idx_status (status),
    
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (reported_user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='举报表';

-- ============================================
-- 2. 系统管理表
-- ============================================

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT,
    table_name VARCHAR(100) NOT NULL,
    operation ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    record_id BIGINT,
    old_value JSON,
    new_value JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user (user_id),
    INDEX idx_table (table_name, operation),
    INDEX idx_created (created_at),
    INDEX idx_record (table_name, record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志表';

-- 同步冲突表
CREATE TABLE IF NOT EXISTS conflict_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(100) NOT NULL,
    record_id BIGINT NOT NULL,
    source_db VARCHAR(50) NOT NULL COMMENT '源数据库',
    target_db VARCHAR(50) NOT NULL COMMENT '目标数据库',
    conflict_type ENUM('version_mismatch', 'data_inconsistency', 'constraint_violation') NOT NULL,
    local_data JSON,
    remote_data JSON,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by BIGINT,
    resolution_strategy VARCHAR(50) COMMENT '解决策略',
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_resolved (resolved),
    INDEX idx_table_record (table_name, record_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='同步冲突表';

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- ============================================
-- 3. 触发器
-- ============================================

-- 用户创建后初始化
DELIMITER //
CREATE TRIGGER trg_after_user_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, record_id, new_value)
    VALUES (NEW.id, 'users', 'INSERT', NEW.id, JSON_OBJECT(
        'username', NEW.username,
        'email', NEW.email
    ));
END//
DELIMITER ;

-- 商品浏览量更新触发器
DELIMITER //
CREATE TRIGGER trg_before_item_view_update
BEFORE UPDATE ON items
FOR EACH ROW
BEGIN
    IF NEW.view_count != OLD.view_count THEN
        SET NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;
END//
DELIMITER ;

-- 交易完成后更新用户统计
DELIMITER //
CREATE TRIGGER trg_after_transaction_complete
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- 更新卖家销售数
        UPDATE users SET total_sales = total_sales + 1 WHERE id = NEW.seller_id;
        -- 更新买家购买数
        UPDATE users SET total_purchases = total_purchases + 1 WHERE id = NEW.buyer_id;
        -- 更新商品状态
        UPDATE items SET status = 'sold', sold_at = CURRENT_TIMESTAMP WHERE id = NEW.item_id;
    END IF;
END//
DELIMITER ;

-- 评论后更新商品咨询量
DELIMITER //
CREATE TRIGGER trg_after_comment_insert
AFTER INSERT ON comments
FOR EACH ROW
BEGIN
    UPDATE items SET inquiry_count = inquiry_count + 1 WHERE id = NEW.item_id;
END//
DELIMITER ;

-- 收藏后更新商品收藏量
DELIMITER //
CREATE TRIGGER trg_after_favorite_insert
AFTER INSERT ON favorites
FOR EACH ROW
BEGIN
    UPDATE items SET favorite_count = favorite_count + 1 WHERE id = NEW.item_id;
END//
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_after_favorite_delete
AFTER DELETE ON favorites
FOR EACH ROW
BEGIN
    UPDATE items SET favorite_count = favorite_count - 1 WHERE id = OLD.item_id;
END//
DELIMITER ;

-- 用户评分更新触发器
DELIMITER //
CREATE TRIGGER trg_after_transaction_rating
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
    IF NEW.seller_rating IS NOT NULL AND OLD.seller_rating IS NULL THEN
        -- 更新卖家评分
        UPDATE users 
        SET seller_rating = (
            SELECT AVG(seller_rating) 
            FROM transactions 
            WHERE seller_id = NEW.seller_id AND seller_rating IS NOT NULL
        )
        WHERE id = NEW.seller_id;
    END IF;
    
    IF NEW.buyer_rating IS NOT NULL AND OLD.buyer_rating IS NULL THEN
        -- 更新买家评分
        UPDATE users 
        SET buyer_rating = (
            SELECT AVG(buyer_rating) 
            FROM transactions 
            WHERE buyer_id = NEW.buyer_id AND buyer_rating IS NOT NULL
        )
        WHERE id = NEW.buyer_id;
    END IF;
END//
DELIMITER ;

-- ============================================
-- 4. 存储过程
-- ============================================

-- 创建交易(带事务)
DELIMITER //
CREATE PROCEDURE sp_create_transaction(
    IN p_item_id BIGINT,
    IN p_buyer_id BIGINT,
    IN p_buyer_contact VARCHAR(200),
    OUT p_transaction_id BIGINT,
    OUT p_error_msg VARCHAR(500)
)
BEGIN
    DECLARE v_seller_id BIGINT;
    DECLARE v_item_price DECIMAL(10,2);
    DECLARE v_item_status VARCHAR(20);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_error_msg = 'Transaction failed';
        SET p_transaction_id = NULL;
    END;
    
    START TRANSACTION;
    
    -- 检查商品状态
    SELECT seller_id, price, status INTO v_seller_id, v_item_price, v_item_status
    FROM items WHERE id = p_item_id FOR UPDATE;
    
    IF v_item_status != 'available' THEN
        ROLLBACK;
        SET p_error_msg = '商品已下架或售出';
        SET p_transaction_id = NULL;
    ELSE
        -- 创建交易记录
        INSERT INTO transactions (
            item_id, buyer_id, seller_id, item_price, final_amount, 
            buyer_contact, status, contacted_at
        ) VALUES (
            p_item_id, p_buyer_id, v_seller_id, v_item_price, v_item_price,
            p_buyer_contact, 'contacted', CURRENT_TIMESTAMP
        );
        
        SET p_transaction_id = LAST_INSERT_ID();
        
        -- 更新商品状态为预定
        UPDATE items SET status = 'reserved' WHERE id = p_item_id;
        
        COMMIT;
        SET p_error_msg = NULL;
    END IF;
END//
DELIMITER ;

-- 获取用户统计信息
DELIMITER //
CREATE PROCEDURE sp_get_user_stats(
    IN p_user_id BIGINT
)
BEGIN
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
    GROUP BY u.id;
END//
DELIMITER ;

-- 搜索商品
DELIMITER //
CREATE PROCEDURE sp_search_items(
    IN p_keyword VARCHAR(200),
    IN p_category_id BIGINT,
    IN p_min_price DECIMAL(10,2),
    IN p_max_price DECIMAL(10,2),
    IN p_condition_type VARCHAR(20),
    IN p_offset INT,
    IN p_limit INT
)
BEGIN
    SELECT 
        i.*,
        u.username AS seller_username,
        u.seller_rating,
        u.is_verified,
        c.name AS category_name,
        (SELECT image_url FROM item_images WHERE item_id = i.id AND is_cover = TRUE LIMIT 1) AS cover_image
    FROM items i
    INNER JOIN users u ON i.seller_id = u.id
    LEFT JOIN categories c ON i.category_id = c.id
    WHERE i.status = 'available'
        AND (p_keyword IS NULL OR MATCH(i.title, i.description) AGAINST(p_keyword IN NATURAL LANGUAGE MODE))
        AND (p_category_id IS NULL OR i.category_id = p_category_id)
        AND (p_min_price IS NULL OR i.price >= p_min_price)
        AND (p_max_price IS NULL OR i.price <= p_max_price)
        AND (p_condition_type IS NULL OR i.condition_type = p_condition_type)
    ORDER BY i.created_at DESC
    LIMIT p_offset, p_limit;
END//
DELIMITER ;

-- ============================================
-- 5. 初始化数据
-- ============================================

-- 插入分类
INSERT INTO categories (name, slug, description, sort_order) VALUES
('全部', 'all', '所有商品', 0),
('数码产品', 'electronics', '电脑、手机、平板等', 1),
('图书教材', 'books', '教材、课外书、杂志等', 2),
('生活用品', 'daily', '日用品、家居用品', 3),
('运动装备', 'sports', '运动器材、健身用品', 4),
('服装鞋包', 'fashion', '衣服、鞋子、包包', 5),
('美妆护肤', 'beauty', '化妆品、护肤品', 6),
('其他', 'other', '其他商品', 99)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 插入系统配置
INSERT INTO system_configs (config_key, config_value, description, is_public) VALUES
('platform_name', '校园交易平台', '平台名称', TRUE),
('max_item_images', '5', '商品最多图片数', TRUE),
('min_credit_score', '60', '最低信用分', TRUE),
('transaction_timeout_hours', '24', '交易超时时间(小时)', FALSE),
('ban_credit_score', '30', '封号信用分阈值', FALSE)
ON DUPLICATE KEY UPDATE config_value=VALUES(config_value);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 6. 常用查询视图
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
GROUP BY u.id;

-- 完成
SELECT 'MySQL/MariaDB schema created successfully!' AS message;
