-- SQLite 插入样例数据 (用于本地开发与测试)
-- 生成日期: 2025-11-19

PRAGMA foreign_keys = ON;

-- 1) 插入用户 (30 个)
INSERT OR IGNORE INTO users (username, email, student_id, password_hash, phone, avatar_url, real_name, is_verified, credit_score)
VALUES
('alice', 'alice@university.edu','S10001','hash_pw','13800000001','/images/avatars/alice.jpg','Alice', 1, 95),
('bob', 'bob@university.edu','S10002','hash_pw','13800000002','/images/avatars/bob.jpg','Bob', 1, 90),
('carol', 'carol@university.edu','S10003','hash_pw','13800000003','/images/avatars/carol.jpg','Carol', 1, 92),
('dave', 'dave@university.edu','S10004','hash_pw','13800000004','/images/avatars/dave.jpg','Dave', 0, 85),
('eve', 'eve@university.edu','S10005','hash_pw','13800000005','/images/avatars/eve.jpg','Eve', 1, 88),
('frank', 'frank@university.edu','S10006','hash_pw','13800000006','/images/avatars/frank.jpg','Frank', 0, 80),
('grace', 'grace@university.edu','S10007','hash_pw','13800000007','/images/avatars/grace.jpg','Grace', 1, 97),
('heidi', 'heidi@university.edu','S10008','hash_pw','13800000008','/images/avatars/heidi.jpg','Heidi', 0, 75),
('ivan', 'ivan@university.edu','S10009','hash_pw','13800000009','/images/avatars/ivan.jpg','Ivan', 1, 86),
('judy', 'judy@university.edu','S10010','hash_pw','13800000010','/images/avatars/judy.jpg','Judy', 1, 93),
('kate', 'kate@university.edu','S10011','hash_pw','13800000011','/images/avatars/kate.jpg','Kate', 1, 89),
('leo', 'leo@university.edu','S10012','hash_pw','13800000012','/images/avatars/leo.jpg','Leo', 0, 70),
('mia', 'mia@university.edu','S10013','hash_pw','13800000013','/images/avatars/mia.jpg','Mia', 1, 91),
('nick', 'nick@university.edu','S10014','hash_pw','13800000014','/images/avatars/nick.jpg','Nick', 0, 65),
('olivia', 'olivia@university.edu','S10015','hash_pw','13800000015','/images/avatars/olivia.jpg','Olivia', 1, 94),
('peggy', 'peggy@university.edu','S10016','hash_pw','13800000016','/images/avatars/peggy.jpg','Peggy', 0, 78),
('quinn', 'quinn@university.edu','S10017','hash_pw','13800000017','/images/avatars/quinn.jpg','Quinn', 1, 88),
('rachel', 'rachel@university.edu','S10018','hash_pw','13800000018','/images/avatars/rachel.jpg','Rachel', 1, 90),
('sam', 'sam@university.edu','S10019','hash_pw','13800000019','/images/avatars/sam.jpg','Sam', 1, 85),
('tina', 'tina@university.edu','S10020','hash_pw','13800000020','/images/avatars/tina.jpg','Tina', 1, 92),
('uma', 'uma@university.edu','S10021','hash_pw','13800000021','/images/avatars/uma.jpg','Uma', 0, 73),
('victor', 'victor@university.edu','S10022','hash_pw','13800000022','/images/avatars/victor.jpg','Victor', 1, 87),
('wendy', 'wendy@university.edu','S10023','hash_pw','13800000023','/images/avatars/wendy.jpg','Wendy', 1, 90),
('xavier', 'xavier@university.edu','S10024','hash_pw','13800000024','/images/avatars/xavier.jpg','Xavier', 0, 69),
('yvonne', 'yvonne@university.edu','S10025','hash_pw','13800000025','/images/avatars/yvonne.jpg','Yvonne', 1, 96),
('zack', 'zack@university.edu','S10026','hash_pw','13800000026','/images/avatars/zack.jpg','Zack', 1, 84),
('amy', 'amy@university.edu','S10027','hash_pw','13800000027','/images/avatars/amy.jpg','Amy', 1, 91),
('brian', 'brian@university.edu','S10028','hash_pw','13800000028','/images/avatars/brian.jpg','Brian', 0, 77),
('cindy', 'cindy@university.edu','S10029','hash_pw','13800000029','/images/avatars/cindy.jpg','Cindy', 1, 89),
('dan', 'dan@university.edu','S10030','hash_pw','13800000030','/images/avatars/dan.jpg','Dan', 1, 86);

-- 2) 插入商品示例 (部分)
INSERT OR IGNORE INTO items (seller_id, category_id, title, description, price, original_price, condition_type, location, contact_info, tags, is_negotiable, is_shipped)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM categories WHERE slug='electronics'), 'iPhone 12 64GB 灰色', '九成新，原装充电器，电池健康90%', 1200.00, 3800.00, '95新', '图书馆门口', '', '["手机","iPhone","64GB"]', 1, 0),
((SELECT id FROM users WHERE username='bob'), (SELECT id FROM categories WHERE slug='books'), '高等代数教材 九成新', '含笔记与标注，适合大一大二复习', 30.00, 120.00, '9成新', '教学楼大厅', '', '["教材","代数"]', 0, 0),
((SELECT id FROM users WHERE username='carol'), (SELECT id FROM categories WHERE slug='daily'), '宿舍电饭锅 2L', '全新未拆封，赠送饭勺', 80.00, 200.00, '全新', '宿舍楼下', '', '["生活","厨房"]', 0, 1);

-- 3) 评论/收藏/交易简短示例
INSERT OR IGNORE INTO comments (item_id, user_id, parent_id, content)
VALUES
((SELECT id FROM items WHERE title LIKE '%iPhone 12%'), (SELECT id FROM users WHERE username='bob'), NULL, '这个价格可以再谈吗？');

INSERT OR IGNORE INTO favorites (user_id, item_id)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM items WHERE title LIKE '%高等代数%'));

INSERT OR IGNORE INTO messages (sender_id, receiver_id, item_id, content)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM users WHERE username='bob'), (SELECT id FROM items WHERE title LIKE '%iPhone 12%'), '你好，这个还在吗？');

INSERT OR IGNORE INTO transactions (item_id, buyer_id, seller_id, item_price, final_amount, status, buyer_contact, seller_contact, meeting_location)
VALUES
((SELECT id FROM items WHERE title LIKE '%iPhone 12%'), (SELECT id FROM users WHERE username='bob'), (SELECT id FROM users WHERE username='alice'), 1200.00, 1200.00, 'contacted', 'bob_phone', 'alice_phone', '图书馆门口');

-- 完成
SELECT 'SQLite sample data script created';
