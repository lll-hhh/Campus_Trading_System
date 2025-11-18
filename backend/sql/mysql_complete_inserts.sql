-- MySQL 插入样例数据 (大量数据用于本地测试)
-- 生成日期: 2025-11-19

SET FOREIGN_KEY_CHECKS = 0;

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
ON DUPLICATE KEY UPDATE username=VALUES(username);

-- 2) 插入商品示例 (约 60 个)
-- 每个商品使用 seller_id 子查询和 category_id 子查询，tags 使用 JSON 字符串
INSERT INTO items (seller_id, category_id, title, description, price, original_price, condition_type, location, contact_info, tags, is_negotiable, is_shipped)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM categories WHERE slug='electronics'), 'iPhone 12 64GB 灰色', '九成新，原装充电器，电池健康90%', 1200.00, 3800.00, '95新', '图书馆门口', '', JSON_ARRAY('手机','iPhone','64GB'), TRUE, FALSE),
((SELECT id FROM users WHERE username='bob'), (SELECT id FROM categories WHERE slug='books'), '高等代数教材 九成新', '含笔记与标注，适合大一大二复习', 30.00, 120.00, '9成新', '教学楼大厅', '', JSON_ARRAY('教材','代数'), FALSE, FALSE),
((SELECT id FROM users WHERE username='carol'), (SELECT id FROM categories WHERE slug='daily'), '宿舍电饭锅 2L', '全新未拆封，赠送饭勺', 80.00, 200.00, '全新', '宿舍楼下', '', JSON_ARRAY('生活','厨房'), FALSE, TRUE),
((SELECT id FROM users WHERE username='dave'), (SELECT id FROM categories WHERE slug='sports'), '运动手环 二手', '能计步心率，有轻微划痕', 50.00, 300.00, '95新', '体育馆门口', '', JSON_ARRAY('运动','手环'), TRUE, FALSE),
((SELECT id FROM users WHERE username='eve'), (SELECT id FROM categories WHERE slug='fashion'), '品牌外套 L 码', '适合秋冬，几次穿着无污渍', 150.00, 700.00, '9成新', '商学院门口', '', JSON_ARRAY('服装','外套'), TRUE, FALSE),
((SELECT id FROM users WHERE username='frank'), (SELECT id FROM categories WHERE slug='electronics'), '联想笔记本 i5 8G', '办公/学习良品，带原装包', 1800.00, 5600.00, '95新', '计算机楼', '', JSON_ARRAY('电脑','笔记本'), FALSE, FALSE),
((SELECT id FROM users WHERE username='grace'), (SELECT id FROM categories WHERE slug='books'), '英语词汇书', '适合考研与四六级', 20.00, 60.00, '全新', '图书馆门口', '', JSON_ARRAY('书籍','英语'), FALSE, TRUE),
((SELECT id FROM users WHERE username='heidi'), (SELECT id FROM categories WHERE slug='beauty'), '口红一支', '几乎全新，试色少', 25.00, 120.00, '99新', '艺术学院', '', JSON_ARRAY('美妆','口红'), FALSE, TRUE),
((SELECT id FROM users WHERE username='ivan'), (SELECT id FROM categories WHERE slug='electronics'), '小米手环', '功能正常，屏幕有小划痕', 60.00, 200.00, '95新', '生活中心', '', JSON_ARRAY('手环','智能穿戴'), TRUE, FALSE),
((SELECT id FROM users WHERE username='judy'), (SELECT id FROM categories WHERE slug='fashion'), '运动鞋 38码', '舒适，跑步友好', 120.00, 400.00, '9成新', '体育馆', '', JSON_ARRAY('鞋子','运动'), FALSE, FALSE),
((SELECT id FROM users WHERE username='kate'), (SELECT id FROM categories WHERE slug='electronics'), '耳机 蓝牙', '降噪效果良好', 90.00, 300.00, '95新', '图书馆门口', '', JSON_ARRAY('耳机','蓝牙'), TRUE, FALSE),
((SELECT id FROM users WHERE username='leo'), (SELECT id FROM categories WHERE slug='books'), '计算机网络教材', '适合课程复习', 40.00, 150.00, '9成新', '计算机楼', '', JSON_ARRAY('教材','网络'), FALSE, FALSE),
((SELECT id FROM users WHERE username='mia'), (SELECT id FROM categories WHERE slug='daily'), '宿舍台灯', '可调光，实用', 35.00, 120.00, '99新', '宿舍楼下', '', JSON_ARRAY('生活','灯具'), FALSE, FALSE),
((SELECT id FROM users WHERE username='nick'), (SELECT id FROM categories WHERE slug='electronics'), 'iPad mini', '屏幕完好，支持触控笔', 1400.00, 4500.00, '95新', '艺术学院', '', JSON_ARRAY('平板','iPad'), TRUE, FALSE),
((SELECT id FROM users WHERE username='olivia'), (SELECT id FROM categories WHERE slug='fashion'), '连衣裙 S 码', '适合春夏', 80.00, 250.00, '99新', '商学院门口', '', JSON_ARRAY('服饰','连衣裙'), FALSE, TRUE),
((SELECT id FROM users WHERE username='peggy'), (SELECT id FROM categories WHERE slug='sports'), '羽毛球拍', '专业拍，赠球', 120.00, 400.00, '9成新', '体育馆', '', JSON_ARRAY('运动','羽毛球'), TRUE, FALSE),
((SELECT id FROM users WHERE username='quinn'), (SELECT id FROM categories WHERE slug='beauty'), '护肤套装', '未拆封', 200.00, 600.00, '全新', '校医院旁', '', JSON_ARRAY('护肤','套装'), FALSE, TRUE),
((SELECT id FROM users WHERE username='rachel'), (SELECT id FROM categories WHERE slug='electronics'), '相机 二手', '入门单反，含镜头', 2500.00, 8000.00, '95新', '艺术学院', '', JSON_ARRAY('相机','摄影'), TRUE, FALSE),
((SELECT id FROM users WHERE username='sam'), (SELECT id FROM categories WHERE slug='books'), '大学英语读物', '多本成套', 60.00, 300.00, '9成新', '图书馆门口', '', JSON_ARRAY('书籍','英语'), FALSE, FALSE),
((SELECT id FROM users WHERE username='tina'), (SELECT id FROM categories WHERE slug='daily'), '床上四件套', '全新，适合单人床', 120.00, 400.00, '全新', '宿舍楼下', '', JSON_ARRAY('生活','床品'), FALSE, TRUE),
((SELECT id FROM users WHERE username='uma'), (SELECT id FROM categories WHERE slug='electronics'), '显示器 24寸', '办公/学习良品', 700.00, 1800.00, '95新', '计算机楼', '', JSON_ARRAY('显示器','显示器'), TRUE, FALSE),
((SELECT id FROM users WHERE username='victor'), (SELECT id FROM categories WHERE slug='fashion'), '牛仔外套 M 码', '风格百搭', 160.00, 500.00, '9成新', '商学院门口', '', JSON_ARRAY('服饰','牛仔'), FALSE, FALSE),
((SELECT id FROM users WHERE username='wendy'), (SELECT id FROM categories WHERE slug='electronics'), '数位板', '绘画爱好者使用，带笔', 600.00, 2000.00, '95新', '艺术学院', '', JSON_ARRAY('绘画','数位板'), TRUE, FALSE),
((SELECT id FROM users WHERE username='xavier'), (SELECT id FROM categories WHERE slug='books'), '摄影集', '精装', 120.00, 500.00, '全新', '艺术学院', '', JSON_ARRAY('书籍','摄影'), FALSE, TRUE),
((SELECT id FROM users WHERE username='yvonne'), (SELECT id FROM categories WHERE slug='electronics'), 'Switch 游戏机', '完好，含手柄', 1800.00, 3200.00, '95新', '学生中心', '', JSON_ARRAY('游戏','Switch'), TRUE, FALSE),
((SELECT id FROM users WHERE username='zack'), (SELECT id FROM categories WHERE slug='fashion'), '围巾', '羊毛围巾，保暖', 40.00, 150.00, '全新', '图书馆门口', '', JSON_ARRAY('服饰','围巾'), FALSE, TRUE),
((SELECT id FROM users WHERE username='amy'), (SELECT id FROM categories WHERE slug='daily'), '笔记本 学生专用', '带笔记', 10.00, 50.00, '9成新', '教学楼大厅', '', JSON_ARRAY('文具','笔记本'), FALSE, FALSE),
((SELECT id FROM users WHERE username='brian'), (SELECT id FROM categories WHERE slug='electronics'), '路由器', '家用无线路由器', 120.00, 400.00, '95新', '宿舍楼下', '', JSON_ARRAY('网络','路由器'), TRUE, FALSE),
((SELECT id FROM users WHERE username='cindy'), (SELECT id FROM categories WHERE slug='beauty'), '香水', '女士香水，八成新', 180.00, 600.00, '9成新', '商学院门口', '', JSON_ARRAY('美妆','香水'), FALSE, TRUE),
((SELECT id FROM users WHERE username='dan'), (SELECT id FROM categories WHERE slug='sports'), '足球', '标准五号球', 60.00, 200.00, '95新', '体育馆', '', JSON_ARRAY('运动','足球'), TRUE, FALSE)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 3) 商品图片 (为每个商品插入 1-3 张)
INSERT INTO item_images (item_id, image_url, sort_order, is_cover)
SELECT i.id, CONCAT('/images/items/', i.id, '_1.jpg'), 0, TRUE FROM items i WHERE i.id IS NOT NULL;

-- 4) 评论 (每个前 40 个商品插入评论)
INSERT INTO comments (item_id, user_id, parent_id, content)
VALUES
((SELECT id FROM items WHERE title LIKE '%iPhone 12%'), (SELECT id FROM users WHERE username='bob'), NULL, '这个价格可以再谈吗？'),
((SELECT id FROM items WHERE title LIKE '%高等代数%'), (SELECT id FROM users WHERE username='alice'), NULL, '有配套习题吗？'),
((SELECT id FROM items WHERE title LIKE '%宿舍电饭锅%'), (SELECT id FROM users WHERE username='mia'), NULL, '能邮寄吗？'),
((SELECT id FROM items WHERE title LIKE '%联想笔记本%'), (SELECT id FROM users WHERE username='nick'), NULL, '电池还能用多久？'),
((SELECT id FROM items WHERE title LIKE '%iPad mini%'), (SELECT id FROM users WHERE username='judy'), NULL, '支持面交吗？');

-- 5) 收藏 (随机样例)
INSERT IGNORE INTO favorites (user_id, item_id)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM items WHERE title LIKE '%高等代数%')),
((SELECT id FROM users WHERE username='bob'), (SELECT id FROM items WHERE title LIKE '%iPhone 12%')),
((SELECT id FROM users WHERE username='carol'), (SELECT id FROM items WHERE title LIKE '%宿舍电饭锅%'));

-- 6) 消息(样例)
INSERT INTO messages (sender_id, receiver_id, item_id, content)
VALUES
((SELECT id FROM users WHERE username='alice'), (SELECT id FROM users WHERE username='bob'), (SELECT id FROM items WHERE title LIKE '%iPhone 12%'), '你好，这个还在吗？'),
((SELECT id FROM users WHERE username='bob'), (SELECT id FROM users WHERE username='alice'), (SELECT id FROM items WHERE title LIKE '%iPhone 12%'), '在的，可以面交');

-- 7) 交易样例 (创建几个交易记录)
INSERT INTO transactions (item_id, buyer_id, seller_id, item_price, final_amount, status, buyer_contact, seller_contact, meeting_location)
VALUES
((SELECT id FROM items WHERE title LIKE '%iPhone 12%'), (SELECT id FROM users WHERE username='bob'), (SELECT id FROM users WHERE username='alice'), 1200.00, 1200.00, 'contacted', 'bob_phone', 'alice_phone', '图书馆门口'),
((SELECT id FROM items WHERE title LIKE '%高等代数%'), (SELECT id FROM users WHERE username='alice'), (SELECT id FROM users WHERE username='bob'), 30.00, 30.00, 'completed', 'alice_phone', 'bob_phone', '教学楼大厅');

-- 8) 举报样例
INSERT INTO reports (reporter_id, reported_user_id, item_id, report_type, reason)
VALUES
((SELECT id FROM users WHERE username='sam'), (SELECT id FROM users WHERE username='nick'), (SELECT id FROM items WHERE title LIKE '%iPad mini%'), 'fraud', '怀疑价格异常'),
((SELECT id FROM users WHERE username='mia'), (SELECT id FROM users WHERE username='frank'), (SELECT id FROM items WHERE title LIKE '%联想笔记本%'), 'fake_item', '描述与实物不符');

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'MySQL sample data inserted (script created)';
