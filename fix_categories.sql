SET NAMES utf8mb4;
DELETE FROM categories WHERE slug IN ('engine', 'brakes', 'filters', 'batteries', 'tires', 'lighting', 'suspension', 'transmission', 'body', 'interior');
INSERT INTO categories (name, slug, description, is_active) VALUES 
('发动机系统', 'engine', '发动机系统分类', 1),
('制动系统', 'brakes', '制动系统分类', 1),
('滤清器', 'filters', '滤清器分类', 1),
('蓄电池', 'batteries', '蓄电池分类', 1),
('轮胎轮毂', 'tires', '轮胎轮毂分类', 1),
('灯光照明', 'lighting', '灯光照明分类', 1),
('悬挂系统', 'suspension', '悬挂系统分类', 1),
('传动系统', 'transmission', '传动系统分类', 1),
('车身外观', 'body', '车身外观分类', 1),
('内饰配件', 'interior', '内饰配件分类', 1);
