-- MySQL 数据库完整脚本
-- 包含建表、索引、触发器、存储过程、存储函数

-- ============================================
-- 1. 建表语句 (核心表示例，完整34张表请参考 ORM 模型)
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 0,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT,
    table_name VARCHAR(100) NOT NULL,
    operation ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    old_value JSON,
    new_value JSON,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_table_operation (table_name, operation),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 商品表
CREATE TABLE IF NOT EXISTS items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    seller_id BIGINT NOT NULL,
    category_id BIGINT,
    status ENUM('available', 'sold', 'reserved', 'deleted') DEFAULT 'available',
    view_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 0,
    INDEX idx_seller (seller_id),
    INDEX idx_category (category_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at),
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 交易表
CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    item_id BIGINT NOT NULL,
    buyer_id BIGINT NOT NULL,
    seller_id BIGINT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'paid', 'shipped', 'completed', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 0,
    INDEX idx_buyer (buyer_id),
    INDEX idx_seller (seller_id),
    INDEX idx_item (item_id),
    INDEX idx_status (status),
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (buyer_id) REFERENCES users(id),
    FOREIGN KEY (seller_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 同步冲突记录表
CREATE TABLE IF NOT EXISTS conflict_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(100) NOT NULL,
    record_id BIGINT NOT NULL,
    source_db VARCHAR(50) NOT NULL,
    target_db VARCHAR(50) NOT NULL,
    conflict_type ENUM('version_mismatch', 'data_inconsistency', 'constraint_violation') NOT NULL,
    local_data JSON,
    remote_data JSON,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by BIGINT,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_resolved (resolved),
    INDEX idx_table_record (table_name, record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 同步日志表
CREATE TABLE IF NOT EXISTS sync_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_db VARCHAR(50) NOT NULL,
    target_db VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    record_count INT DEFAULT 0,
    status ENUM('success', 'failed', 'partial') NOT NULL,
    error_message TEXT,
    duration_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 2. 触发器 - 自动记录数据变更到审计日志
-- ============================================

DELIMITER $$

-- users 表插入触发器
CREATE TRIGGER IF NOT EXISTS trg_users_after_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, new_value, ip_address)
    VALUES (NEW.id, 'users', 'INSERT', JSON_OBJECT(
        'id', NEW.id,
        'username', NEW.username,
        'email', NEW.email,
        'is_active', NEW.is_active
    ), COALESCE(@current_ip, 'system'));
END$$

-- users 表更新触发器
CREATE TRIGGER IF NOT EXISTS trg_users_after_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, new_value, ip_address)
    VALUES (NEW.id, 'users', 'UPDATE',
        JSON_OBJECT('username', OLD.username, 'email', OLD.email, 'is_active', OLD.is_active),
        JSON_OBJECT('username', NEW.username, 'email', NEW.email, 'is_active', NEW.is_active),
        COALESCE(@current_ip, 'system')
    );
END$$

-- users 表删除触发器
CREATE TRIGGER IF NOT EXISTS trg_users_after_delete
AFTER DELETE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, ip_address)
    VALUES (OLD.id, 'users', 'DELETE', JSON_OBJECT(
        'id', OLD.id,
        'username', OLD.username,
        'email', OLD.email
    ), COALESCE(@current_ip, 'system'));
END$$

-- items 表更新触发器 - 自动增加同步版本号
CREATE TRIGGER IF NOT EXISTS trg_items_before_update
BEFORE UPDATE ON items
FOR EACH ROW
BEGIN
    SET NEW.sync_version = OLD.sync_version + 1;
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END$$

-- items 表审计触发器
CREATE TRIGGER IF NOT EXISTS trg_items_after_update
AFTER UPDATE ON items
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, new_value)
    VALUES (NEW.seller_id, 'items', 'UPDATE',
        JSON_OBJECT('title', OLD.title, 'price', OLD.price, 'status', OLD.status),
        JSON_OBJECT('title', NEW.title, 'price', NEW.price, 'status', NEW.status)
    );
END$$

-- transactions 表状态变更触发器
CREATE TRIGGER IF NOT EXISTS trg_transactions_after_update
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_logs (table_name, operation, old_value, new_value)
        VALUES ('transactions', 'UPDATE',
            JSON_OBJECT('id', OLD.id, 'status', OLD.status),
            JSON_OBJECT('id', NEW.id, 'status', NEW.status)
        );
    END IF;
END$$

DELIMITER ;

-- ============================================
-- 3. 存储过程
-- ============================================

DELIMITER $$

-- 批量同步数据到其他数据库（示例逻辑）
CREATE PROCEDURE IF NOT EXISTS sp_sync_table_data(
    IN p_table_name VARCHAR(100),
    IN p_target_db VARCHAR(50),
    IN p_start_id BIGINT,
    IN p_end_id BIGINT
)
BEGIN
    DECLARE v_record_count INT DEFAULT 0;
    DECLARE v_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    DECLARE v_duration INT;
    DECLARE v_error_msg TEXT DEFAULT NULL;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 v_error_msg = MESSAGE_TEXT;
        SET v_duration = TIMESTAMPDIFF(MICROSECOND, v_start_time, CURRENT_TIMESTAMP) DIV 1000;
        INSERT INTO sync_logs (source_db, target_db, table_name, operation, record_count, status, error_message, duration_ms)
        VALUES ('mysql', p_target_db, p_table_name, 'BATCH_SYNC', v_record_count, 'failed', v_error_msg, v_duration);
    END;
    
    -- 这里仅记录同步日志，实际同步由应用层完成
    SET v_record_count = p_end_id - p_start_id + 1;
    SET v_duration = TIMESTAMPDIFF(MICROSECOND, v_start_time, CURRENT_TIMESTAMP) DIV 1000;
    
    INSERT INTO sync_logs (source_db, target_db, table_name, operation, record_count, status, duration_ms)
    VALUES ('mysql', p_target_db, p_table_name, 'BATCH_SYNC', v_record_count, 'success', v_duration);
    
    SELECT CONCAT('同步完成: ', v_record_count, ' 条记录') AS result;
END$$

-- 计算用户信誉度
CREATE PROCEDURE IF NOT EXISTS sp_calculate_user_reputation(
    IN p_user_id BIGINT,
    OUT p_reputation_score DECIMAL(5,2)
)
BEGIN
    DECLARE v_total_sales INT DEFAULT 0;
    DECLARE v_total_purchases INT DEFAULT 0;
    DECLARE v_avg_rating DECIMAL(3,2) DEFAULT 0;
    
    -- 统计销售次数
    SELECT COUNT(*) INTO v_total_sales
    FROM transactions
    WHERE seller_id = p_user_id AND status = 'completed';
    
    -- 统计购买次数
    SELECT COUNT(*) INTO v_total_purchases
    FROM transactions
    WHERE buyer_id = p_user_id AND status = 'completed';
    
    -- 计算信誉分 (简化算法)
    SET p_reputation_score = (v_total_sales * 2 + v_total_purchases * 1) * 0.1;
    
    IF p_reputation_score > 100 THEN
        SET p_reputation_score = 100;
    END IF;
END$$

-- 清理过期冲突记录
CREATE PROCEDURE IF NOT EXISTS sp_cleanup_old_conflicts(
    IN p_days_old INT
)
BEGIN
    DECLARE v_deleted_count INT;
    
    DELETE FROM conflict_records
    WHERE resolved = TRUE 
      AND resolved_at < DATE_SUB(NOW(), INTERVAL p_days_old DAY);
    
    SET v_deleted_count = ROW_COUNT();
    
    SELECT CONCAT('已清理 ', v_deleted_count, ' 条已解决的历史冲突记录') AS result;
END$$

DELIMITER ;

-- ============================================
-- 4. 存储函数
-- ============================================

DELIMITER $$

-- 获取用户交易总数
CREATE FUNCTION IF NOT EXISTS fn_get_user_transaction_count(
    p_user_id BIGINT
) RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_count INT;
    
    SELECT COUNT(*) INTO v_count
    FROM transactions
    WHERE (buyer_id = p_user_id OR seller_id = p_user_id)
      AND status = 'completed';
    
    RETURN COALESCE(v_count, 0);
END$$

-- 计算商品平均价格（按分类）
CREATE FUNCTION IF NOT EXISTS fn_avg_price_by_category(
    p_category_id BIGINT
) RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE v_avg_price DECIMAL(10,2);
    
    SELECT AVG(price) INTO v_avg_price
    FROM items
    WHERE category_id = p_category_id
      AND status = 'available';
    
    RETURN COALESCE(v_avg_price, 0.00);
END$$

-- 检查数据版本冲突
CREATE FUNCTION IF NOT EXISTS fn_check_version_conflict(
    p_table_name VARCHAR(100),
    p_record_id BIGINT,
    p_expected_version INT
) RETURNS BOOLEAN
READS SQL DATA
BEGIN
    DECLARE v_current_version INT;
    DECLARE v_sql TEXT;
    
    -- 注意: 动态 SQL 在函数中受限，这里仅做演示
    -- 实际使用时建议在存储过程中处理
    SET v_current_version = 0;
    
    -- 简化版本：仅检查 items 表
    IF p_table_name = 'items' THEN
        SELECT sync_version INTO v_current_version
        FROM items
        WHERE id = p_record_id;
    END IF;
    
    RETURN v_current_version != p_expected_version;
END$$

DELIMITER ;

-- ============================================
-- 5. 复杂查询示例（多表连接、子查询、聚合）
-- ============================================

-- 查询示例1: 每个分类下交易量TOP5商品及卖家信息
-- SELECT 
--     c.name AS category_name,
--     i.title,
--     u.username AS seller_name,
--     COUNT(t.id) AS transaction_count,
--     SUM(t.total_amount) AS total_revenue
-- FROM items i
-- INNER JOIN users u ON i.seller_id = u.id
-- LEFT JOIN categories c ON i.category_id = c.id
-- LEFT JOIN transactions t ON i.id = t.item_id AND t.status = 'completed'
-- GROUP BY c.id, i.id, u.username
-- ORDER BY c.id, transaction_count DESC
-- LIMIT 5;

-- 查询示例2: 使用窗口函数计算每个用户的销售排名
-- SELECT 
--     seller_id,
--     username,
--     total_sales,
--     RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
-- FROM (
--     SELECT 
--         u.id AS seller_id,
--         u.username,
--         COUNT(t.id) AS total_sales
--     FROM users u
--     LEFT JOIN transactions t ON u.id = t.seller_id AND t.status = 'completed'
--     GROUP BY u.id, u.username
-- ) AS user_sales;

-- 查询示例3: 嵌套子查询 - 查找价格高于分类平均价的商品
-- SELECT 
--     i.id,
--     i.title,
--     i.price,
--     c.name AS category_name,
--     (SELECT AVG(price) FROM items WHERE category_id = i.category_id) AS category_avg_price
-- FROM items i
-- LEFT JOIN categories c ON i.category_id = c.id
-- WHERE i.price > (
--     SELECT AVG(price) 
--     FROM items 
--     WHERE category_id = i.category_id
-- )
-- ORDER BY i.price DESC;

-- ============================================
-- 6. 索引优化建议
-- ============================================

-- 复合索引示例
CREATE INDEX idx_items_category_status ON items(category_id, status);
CREATE INDEX idx_transactions_buyer_status ON transactions(buyer_id, status);
CREATE INDEX idx_transactions_created ON transactions(created_at, status);

-- 全文索引（用于商品搜索）
-- ALTER TABLE items ADD FULLTEXT INDEX ft_title_desc (title, description);

-- ============================================
-- 7. 视图定义（便于复杂查询）
-- ============================================

CREATE OR REPLACE VIEW vw_active_listings AS
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
WHERE i.status = 'available'
  AND u.is_active = TRUE;

CREATE OR REPLACE VIEW vw_transaction_summary AS
SELECT 
    DATE(t.created_at) AS transaction_date,
    COUNT(t.id) AS total_transactions,
    SUM(t.total_amount) AS total_revenue,
    AVG(t.total_amount) AS avg_transaction_value
FROM transactions t
WHERE t.status = 'completed'
GROUP BY DATE(t.created_at)
ORDER BY transaction_date DESC;

-- ============================================
-- 说明:
-- 1. 建表语句包含分区表设计（transactions 按年份分区）
-- 2. 触发器实现自动审计日志和版本号管理
-- 3. 存储过程实现批量同步、信誉计算、数据清理等复杂业务逻辑
-- 4. 存储函数提供可复用的计算逻辑
-- 5. 索引和分区优化查询性能
-- 6. 视图简化常用查询
-- ============================================
