-- ============================================
-- SQLite 补充缺失表
-- ============================================
-- 版本: 1.0
-- 日期: 2025-11-19
-- 说明: 添加购物车、搜索历史、会话表

-- ============================================
-- 1. 购物车表
-- ============================================
DROP TABLE IF EXISTS cart_items;
CREATE TABLE cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, item_id)
);

CREATE INDEX idx_cart_user_id ON cart_items(user_id);
CREATE INDEX idx_cart_item_id ON cart_items(item_id);
CREATE INDEX idx_cart_created ON cart_items(created_at);

-- ============================================
-- 2. 搜索历史表
-- ============================================
DROP TABLE IF EXISTS search_history;
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    keyword VARCHAR(200) NOT NULL,
    result_count INTEGER DEFAULT 0,
    search_type VARCHAR(20) DEFAULT 'keyword' CHECK (search_type IN ('keyword', 'category', 'advanced')),
    filters TEXT, -- JSON存储为TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_user_id ON search_history(user_id);
CREATE INDEX idx_search_keyword ON search_history(keyword);
CREATE INDEX idx_search_created ON search_history(created_at);
CREATE INDEX idx_search_user_created ON search_history(user_id, created_at);

-- ============================================
-- 3. 会话表（消息聊天）
-- ============================================
DROP TABLE IF EXISTS conversations;
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    item_id INTEGER,
    
    last_message_id INTEGER,
    last_message_content TEXT,
    last_message_at TIMESTAMP,
    
    user1_unread_count INTEGER DEFAULT 0,
    user2_unread_count INTEGER DEFAULT 0,
    
    user1_deleted INTEGER DEFAULT 0, -- SQLite用INTEGER代替BOOLEAN
    user2_deleted INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user1_id, user2_id)
);

CREATE INDEX idx_conv_user1 ON conversations(user1_id, user1_deleted);
CREATE INDEX idx_conv_user2 ON conversations(user2_id, user2_deleted);
CREATE INDEX idx_conv_item ON conversations(item_id);
CREATE INDEX idx_conv_updated ON conversations(updated_at);

-- ============================================
-- 4. 热门搜索表（用于统计）
-- ============================================
DROP TABLE IF EXISTS search_trending;
CREATE TABLE search_trending (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword VARCHAR(200) NOT NULL,
    search_count INTEGER DEFAULT 1,
    last_searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date DATE NOT NULL,
    
    UNIQUE(keyword, date)
);

CREATE INDEX idx_trending_count ON search_trending(search_count DESC);
CREATE INDEX idx_trending_date ON search_trending(date);
CREATE INDEX idx_trending_last_searched ON search_trending(last_searched_at);

-- ============================================
-- 5. 刷新Token表（用于JWT刷新）
-- ============================================
DROP TABLE IF EXISTS refresh_tokens;
CREATE TABLE refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token VARCHAR(500) NOT NULL UNIQUE,
    access_token VARCHAR(500),
    
    expires_at TIMESTAMP NOT NULL,
    
    device_info VARCHAR(500),
    ip_address VARCHAR(50),
    user_agent TEXT,
    
    is_revoked INTEGER DEFAULT 0, -- SQLite用INTEGER代替BOOLEAN
    revoked_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rtoken_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_rtoken_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_rtoken_revoked ON refresh_tokens(is_revoked);

-- ============================================
-- SQLite 更新触发器
-- ============================================

-- cart_items 更新触发器
DROP TRIGGER IF EXISTS trigger_cart_items_timestamp;
CREATE TRIGGER trigger_cart_items_timestamp
AFTER UPDATE ON cart_items
FOR EACH ROW
BEGIN
    UPDATE cart_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- conversations 更新触发器
DROP TRIGGER IF EXISTS trigger_conversations_timestamp;
CREATE TRIGGER trigger_conversations_timestamp
AFTER UPDATE ON conversations
FOR EACH ROW
BEGIN
    UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- refresh_tokens 更新触发器
DROP TRIGGER IF EXISTS trigger_refresh_tokens_timestamp;
CREATE TRIGGER trigger_refresh_tokens_timestamp
AFTER UPDATE ON refresh_tokens
FOR EACH ROW
BEGIN
    UPDATE refresh_tokens SET last_used_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
