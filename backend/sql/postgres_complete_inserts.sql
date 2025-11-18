-- PostgreSQL 插入样例数据 (大量数据用于本地测试)
-- 生成日期: 2025-11-19

-- 1) 插入用户 (30 个)
INSERT INTO users (username, email, student_id, password_hash, phone, avatar_url, real_name, is_verified, credit_score)
VALUES
('alice', 'alice@university.edu','S10001','hash_pw','13800000001','/images/avatars/alice.jpg','Alice', TRUE, 95),
('bob', 'bob@university.edu','S10002','hash_pw','13800000002','/images/avatars/bob.jpg','Bob', TRUE, 90),
('carol', 'carol@university.edu','S10003','hash_pw','13800000003','/images/avatars/carol.jpg','Carol', TRUE, 92),
('dave', 'dave@university.edu','S10004','hash_pw','13800000004','/images/avatars/dave.jpg','Dave', FALSE, 85),
('eve', 'eve@university.edu','S10005','hash_pw','13800000005','/images/avatars/eve.jpg','Eve', TRUE, 88),
('frank', 'frank@university.edu','S10006','hash_pw','13800000006','/images/avatars/frank.jpg','Frank', FALSE, 80),
('grace', 'grace@university.edu','S10007','hash_pw','13800000007','/images/avatars/grace.jpg','Grace', TRUE, 97),
('heidi', 'heidi@university.edu','S10008','hash_pw','13800000008','/images/avatars/heidi.jpg','Heidi', FALSE, 75),
('ivan', 'ivan@university.edu','S10009','hash_pw','13800000009','/images/avatars/ivan.jpg','Ivan', TRUE, 86),
('judy', 'judy@university.edu','S10010','hash_pw','13800000010','/images/avatars/judy.jpg','Judy', TRUE, 93),
('kate', 'kate@university.edu','S10011','hash_pw','13800000011','/images/avatars/kate.jpg','Kate', TRUE, 89),
('leo', 'leo@university.edu','S10012','hash_pw','13800000012','/images/avatars/leo.jpg','Leo', FALSE, 70),
('mia', 'mia@university.edu','S10013','hash_pw','13800000013','/images/avatars/mia.jpg','Mia', TRUE, 91),
('nick', 'nick@university.edu','S10014','hash_pw','13800000014','/images/avatars/nick.jpg','Nick', FALSE, 65),
('olivia', 'olivia@university.edu','S10015','hash_pw','13800000015','/images/avatars/olivia.jpg','Olivia', TRUE, 94),
('peggy', 'peggy@university.edu','S10016','hash_pw','13800000016','/images/avatars/peggy.jpg','Peggy', FALSE, 78),
('quinn', 'quinn@university.edu','S10017','hash_pw','13800000017','/images/avatars/quinn.jpg','Quinn', TRUE, 88),
('rachel', 'rachel@university.edu','S10018','hash_pw','13800000018','/images/avatars/rachel.jpg','Rachel', TRUE, 90),
('sam', 'sam@university.edu','S10019','hash_pw','13800000019','/images/avatars/sam.jpg','Sam', TRUE, 85),
('tina', 'tina@university.edu','S10020','hash_pw','13800000020','/images/avatars/tina.jpg','Tina', TRUE, 92),
('uma', 'uma@university.edu','S10021','hash_pw','13800000021','/images/avatars/uma.jpg','Uma', FALSE, 73),
('victor', 'victor@university.edu','S10022','hash_pw','13800000022','/images/avatars/victor.jpg','Victor', TRUE, 87),
('wendy', 'wendy@university.edu','S10023','hash_pw','13800000023','/images/avatars/wendy.jpg','Wendy', TRUE, 90),
('xavier', 'xavier@university.edu','S10024','hash_pw','13800000024','/images/avatars/xavier.jpg','Xavier', FALSE, 69),
('yvonne', 'yvonne@university.edu','S10025','hash_pw','13800000025','/images/avatars/yvonne.jpg','Yvonne', TRUE, 96),
('zack', 'zack@university.edu','S10026','hash_pw','13800000026','/images/avatars/zack.jpg','Zack', TRUE, 84),
('amy', 'amy@university.edu','S10027','hash_pw','13800000027','/images/avatars/amy.jpg','Amy', TRUE, 91),
('brian', 'brian@university.edu','S10028','hash_pw','13800000028','/images/avatars/brian.jpg','Brian', FALSE, 77),
('cindy', 'cindy@university.edu','S10029','hash_pw','13800000029','/images/avatars/cindy.jpg','Cindy', TRUE, 89),
('dan', 'dan@university.edu','S10030','hash_pw','13800000030','/images/avatars/dan.jpg','Dan', TRUE, 86)
ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username;

-- 2) 插入商品 (与 MySQL 相同内容, tags 使用 JSONB 字面量)
INSERT INTO items (seller_id, category_id, title, description, price, original_price, condition_type, location, contact_info, tags, is_negotiable, is_shipped)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM categories WHERE slug='electronics'), 'iPhone 12 64GB 灰色', '九成新，原装充电器，电池健康90%', 1200.00, 3800.00, '95新', '图书馆门口', '', '[]'::jsonb || '"手机","iPhone","64GB"'::jsonb, TRUE, FALSE),
((SELECT id FROM users WHERE username='bob'), (SELECT id FROM categories WHERE slug='books'), '高等代数教材 九成新', '含笔记与标注，适合大一大二复习', 30.00, 120.00, '9成新', '教学楼大厅', '', '[]'::jsonb || '"教材","代数"'::jsonb, FALSE, FALSE);

-- 后续可追加更多 items, comments, images 等，使用与 MySQL 类似的子查询方式

-- 3) 示例评论/收藏/消息/交易等（简短示例）
INSERT INTO comments (item_id, user_id, parent_id, content)
VALUES
((SELECT id FROM items WHERE title LIKE '%iPhone 12%'), (SELECT id FROM users WHERE username='bob'), NULL, '这个价格可以再谈吗？');

INSERT INTO favorites (user_id, item_id)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM items WHERE title LIKE '%高等代数%'))
ON CONFLICT DO NOTHING;

INSERT INTO messages (sender_id, receiver_id, item_id, content)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM users WHERE username='bob'), (SELECT id FROM items WHERE title LIKE '%iPhone 12%'), '你好，这个还在吗？');

INSERT INTO transactions (item_id, buyer_id, seller_id, item_price, final_amount, status, buyer_contact, seller_contact, meeting_location)
VALUES
((SELECT id FROM items WHERE title LIKE '%iPhone 12%'), (SELECT id FROM users WHERE username='bob'), (SELECT id FROM users WHERE username='alice'), 1200.00, 1200.00, 'contacted', 'bob_phone', 'alice_phone', '图书馆门口');

-- 结束
SELECT 'Postgres sample data script created';
