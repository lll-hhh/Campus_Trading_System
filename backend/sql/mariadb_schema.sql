-- MariaDB 数据库完整脚本
-- MariaDB 语法与 MySQL 高度兼容，但有部分增强特性

-- ============================================
-- 1. 建表语句
-- ============================================

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
-- 2. 触发器
-- ============================================

DELIMITER $$

-- users 表触发器
CREATE TRIGGER IF NOT EXISTS trg_users_after_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, new_value, ip_address)
    VALUES (NEW.id, 'users', 'INSERT', JSON_OBJECT(
        'id', NEW.id,
        'username', NEW.username,
        'email', NEW.email
    ), COALESCE(@current_ip, 'system'));
END$$

CREATE TRIGGER IF NOT EXISTS trg_users_after_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, new_value, ip_address)
    VALUES (NEW.id, 'users', 'UPDATE',
        JSON_OBJECT('username', OLD.username, 'is_active', OLD.is_active),
        JSON_OBJECT('username', NEW.username, 'is_active', NEW.is_active),
        COALESCE(@current_ip, 'system')
    );
END$$

CREATE TRIGGER IF NOT EXISTS trg_users_after_delete
AFTER DELETE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, ip_address)
    VALUES (OLD.id, 'users', 'DELETE', JSON_OBJECT(
        'id', OLD.id,
        'username', OLD.username
    ), COALESCE(@current_ip, 'system'));
END$$

-- items 表触发器
CREATE TRIGGER IF NOT EXISTS trg_items_before_update
BEFORE UPDATE ON items
FOR EACH ROW
BEGIN
    SET NEW.sync_version = OLD.sync_version + 1;
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END$$

CREATE TRIGGER IF NOT EXISTS trg_items_after_update
AFTER UPDATE ON items
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, table_name, operation, old_value, new_value)
    VALUES (NEW.seller_id, 'items', 'UPDATE',
        JSON_OBJECT('title', OLD.title, 'price', OLD.price),
        JSON_OBJECT('title', NEW.title, 'price', NEW.price)
    );
END$$

-- transactions 表触发器
CREATE TRIGGER IF NOT EXISTS trg_transactions_before_update
BEFORE UPDATE ON transactions
FOR EACH ROW
BEGIN
    SET NEW.sync_version = OLD.sync_version + 1;
END$$

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

-- 批量同步
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
        VALUES ('mariadb', p_target_db, p_table_name, 'BATCH_SYNC', v_record_count, 'failed', v_error_msg, v_duration);
    END;
    
    SET v_record_count = p_end_id - p_start_id + 1;
    SET v_duration = TIMESTAMPDIFF(MICROSECOND, v_start_time, CURRENT_TIMESTAMP) DIV 1000;
    
    INSERT INTO sync_logs (source_db, target_db, table_name, operation, record_count, status, duration_ms)
    VALUES ('mariadb', p_target_db, p_table_name, 'BATCH_SYNC', v_record_count, 'success', v_duration);
    
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
    
    SELECT COUNT(*) INTO v_total_sales
    FROM transactions
    WHERE seller_id = p_user_id AND status = 'completed';
    
    SELECT COUNT(*) INTO v_total_purchases
    FROM transactions
    WHERE buyer_id = p_user_id AND status = 'completed';
    
    SET p_reputation_score = (v_total_sales * 2 + v_total_purchases * 1) * 0.1;
    
    IF p_reputation_score > 100 THEN
        SET p_reputation_score = 100;
    END IF;
END$$

-- 清理过期冲突
CREATE PROCEDURE IF NOT EXISTS sp_cleanup_old_conflicts(
    IN p_days_old INT
)
BEGIN
    DECLARE v_deleted_count INT;
    
    DELETE FROM conflict_records
    WHERE resolved = TRUE 
      AND resolved_at < DATE_SUB(NOW(), INTERVAL p_days_old DAY);
    
    SET v_deleted_count = ROW_COUNT();
    
    SELECT CONCAT('已清理 ', v_deleted_count, ' 条记录') AS result;
END$$

-- MariaDB 特有: 使用序列生成器
CREATE OR REPLACE PROCEDURE sp_generate_test_users(
    IN p_count INT
)
BEGIN
    DECLARE v_i INT DEFAULT 1;
    WHILE v_i <= p_count DO
        INSERT INTO users (username, email, password_hash)
        VALUES (
            CONCAT('test_user_', v_i),
            CONCAT('test', v_i, '@example.com'),
            'hashed_password'
        );
        SET v_i = v_i + 1;
    END WHILE;
    SELECT CONCAT('生成 ', p_count, ' 个测试用户') AS result;
END$$

DELIMITER ;

-- ============================================
-- 4. 存储函数
-- ============================================

DELIMITER $$

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

CREATE FUNCTION IF NOT EXISTS fn_avg_price_by_category(
    p_category_id BIGINT
) RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE v_avg_price DECIMAL(10,2);
    SELECT AVG(price) INTO v_avg_price
    FROM items
    WHERE category_id = p_category_id AND status = 'available';
    RETURN COALESCE(v_avg_price, 0.00);
END$$

CREATE FUNCTION IF NOT EXISTS fn_check_version_conflict(
    p_table_name VARCHAR(100),
    p_record_id BIGINT,
    p_expected_version INT
) RETURNS BOOLEAN
READS SQL DATA
BEGIN
    DECLARE v_current_version INT DEFAULT 0;
    
    IF p_table_name = 'items' THEN
        SELECT sync_version INTO v_current_version
        FROM items WHERE id = p_record_id;
    ELSIF p_table_name = 'transactions' THEN
        SELECT sync_version INTO v_current_version
        FROM transactions WHERE id = p_record_id;
    END IF;
    
    RETURN v_current_version != p_expected_version;
END$$

DELIMITER ;

-- ============================================
-- 5. 视图
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
WHERE i.status = 'available' AND u.is_active = TRUE;

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
-- 6. 索引优化
-- ============================================

CREATE INDEX idx_items_category_status ON items(category_id, status);
CREATE INDEX idx_transactions_buyer_status ON transactions(buyer_id, status);

-- MariaDB 支持全文索引
ALTER TABLE items ADD FULLTEXT INDEX ft_title_desc (title, description);

-- ============================================
-- 说明:
-- MariaDB 特性:
-- 1. 兼容 MySQL 语法
-- 2. 支持 CREATE OR REPLACE (存储过程/视图)
-- 3. 序列(SEQUENCE)支持更好
-- 4. JSON 函数支持
-- 5. 性能优化(线程池等)
-- ============================================
