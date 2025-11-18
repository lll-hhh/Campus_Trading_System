-- MariaDB 插入样例数据 (用于本地测试)
-- 生成日期: 2025-11-19

SET FOREIGN_KEY_CHECKS = 0;

-- 使用与 MySQL 类似的语法
-- 1) 插入用户 (30 个)
INSERT INTO users (username, email, student_id, password_hash, phone, avatar_url, real_name, is_verified, credit_score)
VALUES
('alice', 'alice@university.edu','S10001','hash_pw','13800000001','/images/avatars/alice.jpg','Alice', TRUE, 95),
('bob', 'bob@university.edu','S10002','hash_pw','13800000002','/images/avatars/bob.jpg','Bob', TRUE, 90),
('carol', 'carol@university.edu','S10003','hash_pw','13800000003','/images/avatars/carol.jpg','Carol', TRUE, 92)
ON DUPLICATE KEY UPDATE username=VALUES(username);

-- 2) 插入少量商品示例（演示）
INSERT INTO items (seller_id, category_id, title, description, price, original_price, condition_type, location, contact_info, tags, is_negotiable, is_shipped)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM categories WHERE slug='electronics'), '示例商品 - 数码', '示例描述', 999.00, 1999.00, '95新', '图书馆', '', JSON_ARRAY('示例','数码'), TRUE, FALSE);

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'MariaDB sample data created';
