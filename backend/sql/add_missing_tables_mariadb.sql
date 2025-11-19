-- ============================================
-- MySQL/MariaDB 补充缺失表
-- ============================================
-- 版本: 1.0
-- 日期: 2025-11-19
-- 说明: 添加购物车、搜索历史、会话表

SET NAMES utf8mb4;

-- ============================================
-- 1. 购物车表
-- ============================================
DROP TABLE IF EXISTS cart_items;
CREATE TABLE cart_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    item_id BIGINT NOT NULL COMMENT '商品ID',
    quantity INT NOT NULL DEFAULT 1 COMMENT '数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_item (user_id, item_id),
    INDEX idx_user_id (user_id),
    INDEX idx_item_id (item_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='购物车表';

-- ============================================
-- 2. 搜索历史表
-- ============================================
DROP TABLE IF EXISTS search_history;
CREATE TABLE search_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    keyword VARCHAR(200) NOT NULL COMMENT '搜索关键词',
    result_count INT DEFAULT 0 COMMENT '搜索结果数量',
    search_type ENUM('keyword', 'category', 'advanced') DEFAULT 'keyword' COMMENT '搜索类型',
    filters JSON COMMENT '搜索过滤条件(JSON)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_keyword (keyword),
    INDEX idx_created (created_at),
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='搜索历史表';

-- ============================================
-- 3. 会话表（消息聊天）
-- ============================================
DROP TABLE IF EXISTS conversations;
CREATE TABLE conversations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user1_id BIGINT NOT NULL COMMENT '用户1 ID',
    user2_id BIGINT NOT NULL COMMENT '用户2 ID',
    item_id BIGINT COMMENT '关联商品ID（可选）',
    
    -- 最后消息信息
    last_message_id BIGINT COMMENT '最后一条消息ID',
    last_message_content TEXT COMMENT '最后消息内容',
    last_message_at TIMESTAMP NULL COMMENT '最后消息时间',
    
    -- 未读计数（分别记录两个用户的未读数）
    user1_unread_count INT DEFAULT 0 COMMENT '用户1未读消息数',
    user2_unread_count INT DEFAULT 0 COMMENT '用户2未读消息数',
    
    -- 删除标记（软删除）
    user1_deleted BOOLEAN DEFAULT FALSE COMMENT '用户1是否删除',
    user2_deleted BOOLEAN DEFAULT FALSE COMMENT '用户2是否删除',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_users (user1_id, user2_id),
    INDEX idx_user1 (user1_id, user1_deleted),
    INDEX idx_user2 (user2_id, user2_deleted),
    INDEX idx_item (item_id),
    INDEX idx_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';

-- ============================================
-- 4. 热门搜索表（用于统计）
-- ============================================
DROP TABLE IF EXISTS search_trending;
CREATE TABLE search_trending (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    keyword VARCHAR(200) NOT NULL COMMENT '搜索关键词',
    search_count INT DEFAULT 1 COMMENT '搜索次数',
    last_searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '最后搜索时间',
    date DATE NOT NULL COMMENT '统计日期',
    
    UNIQUE KEY unique_keyword_date (keyword, date),
    INDEX idx_search_count (search_count DESC),
    INDEX idx_date (date),
    INDEX idx_last_searched (last_searched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='热门搜索统计表';

-- ============================================
-- 5. 刷新Token表（用于JWT刷新）
-- ============================================
DROP TABLE IF EXISTS refresh_tokens;
CREATE TABLE refresh_tokens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    token VARCHAR(500) NOT NULL COMMENT '刷新令牌',
    access_token VARCHAR(500) COMMENT '关联的访问令牌',
    
    -- Token有效期
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    
    -- 设备和IP信息
    device_info VARCHAR(500) COMMENT '设备信息',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    
    -- 状态
    is_revoked BOOLEAN DEFAULT FALSE COMMENT '是否已撤销',
    revoked_at TIMESTAMP NULL COMMENT '撤销时间',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_token (token),
    INDEX idx_user_id (user_id),
    INDEX idx_expires (expires_at),
    INDEX idx_revoked (is_revoked)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='刷新令牌表';

-- ============================================
-- 说明：
-- 1. cart_items: 购物车表，存储用户添加的商品
-- 2. search_history: 用户搜索历史记录
-- 3. conversations: 会话表，用于管理用户间的聊天会话
-- 4. search_trending: 热门搜索统计，用于展示热门搜索词
-- 5. refresh_tokens: JWT刷新令牌管理
-- ============================================
