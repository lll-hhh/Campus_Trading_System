-- PostgreSQL 数据库完整脚本
-- 包含建表、索引、触发器、存储过程(函数)

-- ============================================
-- 1. 建表语句
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_table ON audit_logs(table_name, operation);
CREATE INDEX idx_audit_created ON audit_logs(created_at);

CREATE TABLE IF NOT EXISTS items (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    seller_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id BIGINT,
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'sold', 'reserved', 'deleted')),
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
);

CREATE INDEX idx_items_seller ON items(seller_id);
CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_created ON items(created_at);

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(id),
    buyer_id BIGINT NOT NULL REFERENCES users(id),
    seller_id BIGINT NOT NULL REFERENCES users(id),
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'shipped', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_version INTEGER DEFAULT 0
) PARTITION BY RANGE (created_at);

-- 创建分区表
CREATE TABLE IF NOT EXISTS transactions_2024 PARTITION OF transactions
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE IF NOT EXISTS transactions_2025 PARTITION OF transactions
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS transactions_default PARTITION OF transactions DEFAULT;

CREATE INDEX idx_trans_buyer ON transactions(buyer_id);
CREATE INDEX idx_trans_seller ON transactions(seller_id);
CREATE INDEX idx_trans_item ON transactions(item_id);
CREATE INDEX idx_trans_status ON transactions(status);

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
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conflict_resolved ON conflict_records(resolved);
CREATE INDEX idx_conflict_table ON conflict_records(table_name, record_id);

CREATE TABLE IF NOT EXISTS sync_logs (
    id BIGSERIAL PRIMARY KEY,
    source_db VARCHAR(50) NOT NULL,
    target_db VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    record_count INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sync_status ON sync_logs(status);
CREATE INDEX idx_sync_created ON sync_logs(created_at);

-- ============================================
-- 2. 触发器函数 (PostgreSQL 使用函数+触发器模式)
-- ============================================

-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION trg_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 自动增加 sync_version
CREATE OR REPLACE FUNCTION trg_increment_sync_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.sync_version = OLD.sync_version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 审计日志函数 - 通用版本
CREATE OR REPLACE FUNCTION trg_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (user_id, table_name, operation, new_value, ip_address)
        VALUES (
            COALESCE(NEW.id, NULL),
            TG_TABLE_NAME,
            'INSERT',
            to_jsonb(NEW),
            current_setting('application.current_ip', TRUE)
        );
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (user_id, table_name, operation, old_value, new_value, ip_address)
        VALUES (
            COALESCE(NEW.id, NULL),
            TG_TABLE_NAME,
            'UPDATE',
            to_jsonb(OLD),
            to_jsonb(NEW),
            current_setting('application.current_ip', TRUE)
        );
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_logs (user_id, table_name, operation, old_value, ip_address)
        VALUES (
            COALESCE(OLD.id, NULL),
            TG_TABLE_NAME,
            'DELETE',
            to_jsonb(OLD),
            current_setting('application.current_ip', TRUE)
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 3. 绑定触发器到表
-- ============================================

-- users 表触发器
DROP TRIGGER IF EXISTS trg_users_updated ON users;
CREATE TRIGGER trg_users_updated
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION trg_update_timestamp();

DROP TRIGGER IF EXISTS trg_users_audit ON users;
CREATE TRIGGER trg_users_audit
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW
    EXECUTE FUNCTION trg_audit_log();

-- items 表触发器
DROP TRIGGER IF EXISTS trg_items_updated ON items;
CREATE TRIGGER trg_items_updated
    BEFORE UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION trg_update_timestamp();

DROP TRIGGER IF EXISTS trg_items_version ON items;
CREATE TRIGGER trg_items_version
    BEFORE UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION trg_increment_sync_version();

DROP TRIGGER IF EXISTS trg_items_audit ON items;
CREATE TRIGGER trg_items_audit
    AFTER INSERT OR UPDATE OR DELETE ON items
    FOR EACH ROW
    EXECUTE FUNCTION trg_audit_log();

-- transactions 表触发器
DROP TRIGGER IF EXISTS trg_transactions_updated ON transactions;
CREATE TRIGGER trg_transactions_updated
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION trg_update_timestamp();

DROP TRIGGER IF EXISTS trg_transactions_version ON transactions;
CREATE TRIGGER trg_transactions_version
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION trg_increment_sync_version();

DROP TRIGGER IF EXISTS trg_transactions_audit ON transactions;
CREATE TRIGGER trg_transactions_audit
    AFTER INSERT OR UPDATE OR DELETE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION trg_audit_log();

-- ============================================
-- 4. 存储函数 (PostgreSQL 不区分存储过程和函数)
-- ============================================

-- 批量同步记录函数
CREATE OR REPLACE FUNCTION sp_sync_table_data(
    p_table_name VARCHAR,
    p_target_db VARCHAR,
    p_start_id BIGINT,
    p_end_id BIGINT
) RETURNS TEXT AS $$
DECLARE
    v_record_count INTEGER;
    v_start_time TIMESTAMP;
    v_duration INTEGER;
    v_error_msg TEXT;
BEGIN
    v_start_time := CURRENT_TIMESTAMP;
    v_record_count := p_end_id - p_start_id + 1;
    
    BEGIN
        -- 记录同步日志
        v_duration := EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - v_start_time))::INTEGER * 1000;
        
        INSERT INTO sync_logs (source_db, target_db, table_name, operation, record_count, status, duration_ms)
        VALUES ('postgres', p_target_db, p_table_name, 'BATCH_SYNC', v_record_count, 'success', v_duration);
        
        RETURN '同步完成: ' || v_record_count || ' 条记录';
        
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error_msg = MESSAGE_TEXT;
        v_duration := EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - v_start_time))::INTEGER * 1000;
        
        INSERT INTO sync_logs (source_db, target_db, table_name, operation, record_count, status, error_message, duration_ms)
        VALUES ('postgres', p_target_db, p_table_name, 'BATCH_SYNC', 0, 'failed', v_error_msg, v_duration);
        
        RETURN '同步失败: ' || v_error_msg;
    END;
END;
$$ LANGUAGE plpgsql;

-- 计算用户信誉度
CREATE OR REPLACE FUNCTION sp_calculate_user_reputation(p_user_id BIGINT)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    v_total_sales INTEGER;
    v_total_purchases INTEGER;
    v_reputation_score DECIMAL(5,2);
BEGIN
    -- 统计销售次数
    SELECT COUNT(*) INTO v_total_sales
    FROM transactions
    WHERE seller_id = p_user_id AND status = 'completed';
    
    -- 统计购买次数
    SELECT COUNT(*) INTO v_total_purchases
    FROM transactions
    WHERE buyer_id = p_user_id AND status = 'completed';
    
    -- 计算信誉分
    v_reputation_score := (v_total_sales * 2 + v_total_purchases * 1) * 0.1;
    
    IF v_reputation_score > 100 THEN
        v_reputation_score := 100;
    END IF;
    
    RETURN v_reputation_score;
END;
$$ LANGUAGE plpgsql;

-- 清理过期冲突记录
CREATE OR REPLACE FUNCTION sp_cleanup_old_conflicts(p_days_old INTEGER)
RETURNS TEXT AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM conflict_records
    WHERE resolved = TRUE 
      AND resolved_at < CURRENT_TIMESTAMP - (p_days_old || ' days')::INTERVAL;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    RETURN '已清理 ' || v_deleted_count || ' 条已解决的历史冲突记录';
END;
$$ LANGUAGE plpgsql;

-- 获取用户交易总数
CREATE OR REPLACE FUNCTION fn_get_user_transaction_count(p_user_id BIGINT)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM transactions
    WHERE (buyer_id = p_user_id OR seller_id = p_user_id)
      AND status = 'completed';
    
    RETURN COALESCE(v_count, 0);
END;
$$ LANGUAGE plpgsql STABLE;

-- 计算分类平均价格
CREATE OR REPLACE FUNCTION fn_avg_price_by_category(p_category_id BIGINT)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    v_avg_price DECIMAL(10,2);
BEGIN
    SELECT AVG(price) INTO v_avg_price
    FROM items
    WHERE category_id = p_category_id
      AND status = 'available';
    
    RETURN COALESCE(v_avg_price, 0.00);
END;
$$ LANGUAGE plpgsql STABLE;

-- 检查版本冲突
CREATE OR REPLACE FUNCTION fn_check_version_conflict(
    p_table_name VARCHAR,
    p_record_id BIGINT,
    p_expected_version INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_version INTEGER;
BEGIN
    IF p_table_name = 'items' THEN
        SELECT sync_version INTO v_current_version
        FROM items WHERE id = p_record_id;
    ELSIF p_table_name = 'transactions' THEN
        SELECT sync_version INTO v_current_version
        FROM transactions WHERE id = p_record_id;
    END IF;
    
    RETURN v_current_version IS NOT NULL AND v_current_version != p_expected_version;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================
-- 5. 视图定义
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
-- 6. 复合索引优化
-- ============================================

CREATE INDEX idx_items_category_status ON items(category_id, status);
CREATE INDEX idx_transactions_buyer_status ON transactions(buyer_id, status);
CREATE INDEX idx_transactions_created_status ON transactions(created_at, status);

-- 全文搜索索引
CREATE INDEX idx_items_title_fts ON items USING gin(to_tsvector('english', title));
CREATE INDEX idx_items_desc_fts ON items USING gin(to_tsvector('english', description));

-- ============================================
-- 说明:
-- PostgreSQL 特性:
-- 1. 使用 BIGSERIAL 替代 AUTO_INCREMENT
-- 2. 使用 JSONB 类型存储 JSON 数据（支持索引和查询）
-- 3. 触发器需先创建函数，再绑定到表
-- 4. 支持分区表（PARTITION BY RANGE）
-- 5. 支持全文搜索索引（GIN）
-- 6. 存储过程和函数统一为 FUNCTION
-- ============================================
