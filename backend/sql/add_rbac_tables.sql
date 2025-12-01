-- ============================================
-- 添加 RBAC 相关表的迁移脚本 (MySQL/MariaDB)
-- ============================================
-- 此脚本用于在现有数据库上添加缺失的 RBAC 表
-- 运行方式: mysql -u root -p campuswap < add_rbac_tables.sql

SET FOREIGN_KEY_CHECKS = 0;

-- 角色表 (RBAC)
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名称',
    description VARCHAR(255) COMMENT '角色描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 1,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 权限表 (RBAC)
CREATE TABLE IF NOT EXISTS permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '权限名称',
    resource VARCHAR(50) NOT NULL COMMENT '资源类型',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    description VARCHAR(255) COMMENT '权限描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 1,
    INDEX idx_name (name),
    INDEX idx_resource_action (resource, action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 1,
    UNIQUE KEY uq_user_role (user_id, role_id),
    INDEX idx_user (user_id),
    INDEX idx_role (role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 1,
    UNIQUE KEY uq_role_permission (role_id, permission_id),
    INDEX idx_role (role_id),
    INDEX idx_permission (permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';

-- 用户资料表
CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    display_name VARCHAR(120) NOT NULL COMMENT '显示名称',
    phone VARCHAR(32) COMMENT '联系电话',
    campus VARCHAR(120) COMMENT '校区',
    bio VARCHAR(500) COMMENT '个人简介',
    avatar_url VARCHAR(512) COMMENT '头像URL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    sync_version INT DEFAULT 1,
    INDEX idx_user (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户资料表';

SET FOREIGN_KEY_CHECKS = 1;

-- 插入默认角色
INSERT IGNORE INTO roles (name, description) VALUES
('admin', '系统管理员'),
('moderator', '内容审核员'),
('user', '普通用户'),
('seller', '认证卖家');

-- 插入默认权限
INSERT IGNORE INTO permissions (name, resource, action, description) VALUES
('user:read', 'user', 'read', '查看用户信息'),
('user:write', 'user', 'write', '修改用户信息'),
('user:delete', 'user', 'delete', '删除用户'),
('item:read', 'item', 'read', '查看商品'),
('item:write', 'item', 'write', '发布/修改商品'),
('item:delete', 'item', 'delete', '删除商品'),
('order:read', 'order', 'read', '查看订单'),
('order:write', 'order', 'write', '创建/修改订单'),
('admin:access', 'admin', 'access', '访问管理后台'),
('report:handle', 'report', 'handle', '处理举报');

-- 角色权限关联
INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
-- admin 拥有所有权限
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
-- moderator 拥有审核权限
(2, 1), (2, 4), (2, 6), (2, 7), (2, 9), (2, 10),
-- user 拥有基本权限
(3, 1), (3, 4), (3, 5), (3, 7), (3, 8),
-- seller 拥有卖家权限
(4, 1), (4, 4), (4, 5), (4, 6), (4, 7), (4, 8);

SELECT 'RBAC tables created successfully!' AS message;
