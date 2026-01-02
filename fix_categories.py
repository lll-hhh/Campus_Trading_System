import pymysql
import os

def fix_categories():
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='campuswap',
        password='campuswap123',
        database='campuswap',
        charset='utf8mb4'
    )
    try:
        with conn.cursor() as cursor:
            # 删除可能损坏的分类
            slugs = ['engine', 'brakes', 'filters', 'batteries', 'tires', 'lighting', 'suspension', 'transmission', 'body', 'interior']
            cursor.execute("DELETE FROM categories WHERE slug IN %s", (slugs,))
            
            categories = [
                ('发动机系统', 'engine', '发动机系统分类'),
                ('制动系统', 'brakes', '制动系统分类'),
                ('滤清器', 'filters', '滤清器分类'),
                ('蓄电池', 'batteries', '蓄电池分类'),
                ('轮胎轮毂', 'tires', '轮胎轮毂分类'),
                ('灯光照明', 'lighting', '灯光照明分类'),
                ('悬挂系统', 'suspension', '悬挂系统分类'),
                ('传动系统', 'transmission', '传动系统分类'),
                ('车身外观', 'body', '车身外观分类'),
                ('内饰配件', 'interior', '内饰配件分类')
            ]
            
            for name, slug, desc in categories:
                cursor.execute(
                    "INSERT INTO categories (name, slug, description, is_active) VALUES (%s, %s, %s, 1)",
                    (name, slug, desc)
                )
        conn.commit()
        print("Categories fixed successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_categories()
