SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE categories;
INSERT INTO categories (id, name, slug, description, is_active) VALUES
(1, '发动机系统', 'engine', '发动机及相关零部件', 1),
(2, '制动系统', 'brakes', '刹车片、刹车盘等', 1),
(3, '滤清器', 'filters', '机油、空气、空调滤清器', 1),
(4, '蓄电池', 'batteries', '汽车电瓶及充电系统', 1),
(5, '轮胎轮毂', 'tires', '轮胎、轮圈及附件', 1),
(6, '灯光照明', 'lighting', '大灯、尾灯、雾灯等', 1),
(7, '悬挂系统', 'suspension', '减震器、控制臂等', 1),
(8, '传动系统', 'transmission', '变速箱、离合器等', 1),
(9, '车身外观', 'body', '保险杠、后视镜、车门等', 1),
(10, '内饰配件', 'interior', '脚垫、座套、方向盘等', 1),
(11, '其他闲置', 'other', '其他汽车相关配件', 1);
SET FOREIGN_KEY_CHECKS = 1;
