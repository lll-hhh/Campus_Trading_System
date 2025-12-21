-- ============================================
-- PostgreSQL 补充缺失表
-- ============================================
-- 版本: 1.0
-- 日期: 2025-11-19
-- 说明: 添加购物车、搜索历史、会话表

-- ============================================
-- 1. 购物车表
-- ============================================
DROP TABLE IF EXISTS cart_items CASCADE;
CREATE TABLE cart_items (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_item UNIQUE (user_id, item_id)
);

CREATE INDEX idx_cart_user_id ON cart_items(user_id);
CREATE INDEX idx_cart_item_id ON cart_items(item_id);
CREATE INDEX idx_cart_created ON cart_items(created_at);

COMMENT ON TABLE cart_items IS '购物车表';
COMMENT ON COLUMN cart_items.user_id IS '用户ID';
COMMENT ON COLUMN cart_items.item_id IS '商品ID';
COMMENT ON COLUMN cart_items.quantity IS '数量';

-- ============================================
-- 2. 搜索历史表
-- ============================================
DROP TABLE IF EXISTS search_history CASCADE;
CREATE TABLE search_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    keyword VARCHAR(200) NOT NULL,
    result_count INT DEFAULT 0,
    search_type VARCHAR(20) DEFAULT 'keyword' CHECK (search_type IN ('keyword', 'category', 'advanced')),
    filters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_user_id ON search_history(user_id);
CREATE INDEX idx_search_keyword ON search_history(keyword);
CREATE INDEX idx_search_created ON search_history(created_at);
CREATE INDEX idx_search_user_created ON search_history(user_id, created_at);

COMMENT ON TABLE search_history IS '搜索历史表';
COMMENT ON COLUMN search_history.user_id IS '用户ID';
COMMENT ON COLUMN search_history.keyword IS '搜索关键词';
COMMENT ON COLUMN search_history.result_count IS '搜索结果数量';
COMMENT ON COLUMN search_history.search_type IS '搜索类型';
COMMENT ON COLUMN search_history.filters IS '搜索过滤条件(JSON)';

-- ============================================
-- 3. 会话表（消息聊天）
-- ============================================
DROP TABLE IF EXISTS conversations CASCADE;
CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    user1_id BIGINT NOT NULL,
    user2_id BIGINT NOT NULL,
    item_id BIGINT,
    
    last_message_id BIGINT,
    last_message_content TEXT,
    last_message_at TIMESTAMP,
    
    user1_unread_count INT DEFAULT 0,
    user2_unread_count INT DEFAULT 0,
    
    user1_deleted BOOLEAN DEFAULT FALSE,
    user2_deleted BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_users UNIQUE (user1_id, user2_id)
);

CREATE INDEX idx_conv_user1 ON conversations(user1_id, user1_deleted);
CREATE INDEX idx_conv_user2 ON conversations(user2_id, user2_deleted);
CREATE INDEX idx_conv_item ON conversations(item_id);
CREATE INDEX idx_conv_updated ON conversations(updated_at);

COMMENT ON TABLE conversations IS '会话表';
COMMENT ON COLUMN conversations.user1_id IS '用户1 ID';
COMMENT ON COLUMN conversations.user2_id IS '用户2 ID';
COMMENT ON COLUMN conversations.item_id IS '关联商品ID（可选）';
COMMENT ON COLUMN conversations.user1_unread_count IS '用户1未读消息数';
COMMENT ON COLUMN conversations.user2_unread_count IS '用户2未读消息数';

-- ============================================
-- 4. 热门搜索表（用于统计）
-- ============================================
DROP TABLE IF EXISTS search_trending CASCADE;
CREATE TABLE search_trending (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(200) NOT NULL,
    search_count INT DEFAULT 1,
    last_searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date DATE NOT NULL,
    
    CONSTRAINT unique_keyword_date UNIQUE (keyword, date)
);

CREATE INDEX idx_trending_count ON search_trending(search_count DESC);
CREATE INDEX idx_trending_date ON search_trending(date);
CREATE INDEX idx_trending_last_searched ON search_trending(last_searched_at);

COMMENT ON TABLE search_trending IS '热门搜索统计表';
COMMENT ON COLUMN search_trending.keyword IS '搜索关键词';
COMMENT ON COLUMN search_trending.search_count IS '搜索次数';
COMMENT ON COLUMN search_trending.last_searched_at IS '最后搜索时间';

-- ============================================
-- 5. 刷新Token表（用于JWT刷新）
-- ============================================
DROP TABLE IF EXISTS refresh_tokens CASCADE;
CREATE TABLE refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    token VARCHAR(500) NOT NULL,
    access_token VARCHAR(500),
    
    expires_at TIMESTAMP NOT NULL,
    
    device_info VARCHAR(500),
    ip_address VARCHAR(50),
    user_agent TEXT,
    
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_token UNIQUE (token)
);

CREATE INDEX idx_rtoken_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_rtoken_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_rtoken_revoked ON refresh_tokens(is_revoked);

COMMENT ON TABLE refresh_tokens IS '刷新令牌表';
COMMENT ON COLUMN refresh_tokens.user_id IS '用户ID';
COMMENT ON COLUMN refresh_tokens.token IS '刷新令牌';
COMMENT ON COLUMN refresh_tokens.expires_at IS '过期时间';
COMMENT ON COLUMN refresh_tokens.is_revoked IS '是否已撤销';

-- ============================================
-- 创建更新时间触发器
-- ============================================

-- cart_items 更新触发器
CREATE OR REPLACE FUNCTION update_cart_items_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cart_items_timestamp
BEFORE UPDATE ON cart_items
FOR EACH ROW
EXECUTE FUNCTION update_cart_items_timestamp();

-- conversations 更新触发器
CREATE OR REPLACE FUNCTION update_conversations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_conversations_timestamp
BEFORE UPDATE ON conversations
FOR EACH ROW
EXECUTE FUNCTION update_conversations_timestamp();

-- refresh_tokens 更新触发器
CREATE OR REPLACE FUNCTION update_refresh_tokens_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_used_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_refresh_tokens_timestamp
BEFORE UPDATE ON refresh_tokens
FOR EACH ROW
EXECUTE FUNCTION update_refresh_tokens_timestamp();
