-- 购物车表（适用于 MySQL/MariaDB）
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
    INDEX idx_item_id (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='购物车表';
