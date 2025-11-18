#!/usr/bin/env python3
"""
生成大规模样例数据 SQL 脚本
- 200+ 用户
- 500+ 商品
- 1000+ 评论
- 2000+ 消息
- 500+ 交易
- 大量收藏、举报等
"""

import random
import json
from datetime import datetime, timedelta

# 中文名字库
FIRST_NAMES = ['张', '李', '王', '刘', '陈', '杨', '黄', '赵', '周', '吴', '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '高', '罗']
SECOND_NAMES = ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '涛', '明', '超', '秀', '英', '华', '文',
                '红', '玲', '飞', '鹏', '辉', '斌', '宇', '晨', '婷', '欣', '欢', '雨', '雪', '霞', '梅', '兰', '燕', '莉', '萍', '颖']

PRODUCT_PREFIXES = {
    'electronics': ['iPhone', 'iPad', '小米', '华为', '联想', 'MacBook', 'Surface', 'ThinkPad', '戴尔', '惠普', '索尼', '佳能', '尼康', '蓝牙耳机', 'AirPods', '小米手环', 'Apple Watch', 'Kindle', '显示器', '机械键盘', '鼠标', '路由器', '充电宝', '数据线', '手机壳'],
    'books': ['高等数学', '线性代数', '概率论', '大学物理', '大学英语', 'C语言', 'Python', 'Java', '数据结构', '算法导论', '操作系统', '计算机网络', '经济学原理', '管理学', '会计学', '市场营销', '心理学', '哲学', '文学作品', '历史书籍', '考研资料', '四六级词汇', 'TOEFL', 'GRE'],
    'daily': ['台灯', '水杯', '保温杯', '雨伞', '床上用品', '枕头', '被子', '电饭锅', '电热水壶', '风扇', '暖手宝', '挂钩', '收纳箱', '衣架', '洗漱用品', '毛巾', '拖鞋', '垃圾桶', '闹钟', '插线板'],
    'sports': ['篮球', '足球', '羽毛球拍', '乒乓球拍', '网球拍', '跑步鞋', '运动服', '瑜伽垫', '哑铃', '跳绳', '游泳镜', '运动手环', '护腕', '护膝', '登山包', '帐篷', '睡袋'],
    'fashion': ['T恤', '衬衫', '牛仔裤', '连衣裙', '外套', '羽绒服', '运动鞋', '帆布鞋', '高跟鞋', '背包', '钱包', '手表', '太阳镜', '围巾', '帽子', '手套'],
    'beauty': ['口红', '粉底液', '眼影', '面膜', '洗面奶', '爽肤水', '乳液', '精华液', '防晒霜', '香水', '指甲油', '眉笔', '腮红', '睫毛膏'],
}

LOCATIONS = ['图书馆门口', '教学楼大厅', '宿舍楼下', '食堂广场', '体育馆', '艺术学院', '商学院门口', '计算机楼', '生活中心', '校医院旁', '学生中心', '东门', '西门', '南门', '北门']

CONDITIONS = ['全新', '99新', '95新', '9成新', '二手']

COMMENT_TEMPLATES = [
    '这个还在吗？',
    '价格可以商量吗？',
    '能便宜点吗？',
    '成色怎么样？',
    '有没有磕碰？',
    '支持验货吗？',
    '什么时候能交易？',
    '在哪里面交？',
    '包邮吗？',
    '有发票吗？',
    '用了多久了？',
    '为什么要卖？',
    '能发几张实物图吗？',
    '功能都正常吗？',
    '有配件吗？',
]

def generate_users(count=200):
    """生成用户数据"""
    users = []
    for i in range(1, count + 1):
        first = random.choice(FIRST_NAMES)
        second = random.choice(SECOND_NAMES)
        name = f"{first}{second}"
        username = f"user{i:04d}"
        email = f"{username}@university.edu"
        student_id = f"S{20000 + i}"
        credit_score = random.randint(60, 100)
        is_verified = random.choice([True, True, True, False])  # 75% 认证
        
        users.append({
            'username': username,
            'email': email,
            'student_id': student_id,
            'real_name': name,
            'credit_score': credit_score,
            'is_verified': is_verified,
        })
    return users

def generate_items(users, count=500):
    """生成商品数据"""
    items = []
    categories = ['electronics', 'books', 'daily', 'sports', 'fashion', 'beauty']
    
    for i in range(1, count + 1):
        seller = random.choice(users)
        category = random.choice(categories)
        prefix = random.choice(PRODUCT_PREFIXES[category])
        
        # 生成商品标题
        suffix = random.choice(['', ' 二手', ' 闲置', ' 急出', ' 低价', ' 包邮'])
        title = f"{prefix}{suffix}"
        
        # 生成价格
        if category == 'electronics':
            price = round(random.uniform(50, 5000), 2)
            original = round(price * random.uniform(1.5, 4), 2)
        elif category == 'books':
            price = round(random.uniform(10, 150), 2)
            original = round(price * random.uniform(1.5, 3), 2)
        else:
            price = round(random.uniform(20, 500), 2)
            original = round(price * random.uniform(1.3, 3), 2)
        
        condition = random.choice(CONDITIONS)
        location = random.choice(LOCATIONS)
        is_negotiable = random.choice([True, False])
        is_shipped = random.choice([True, False, False])  # 33% 包邮
        
        # 生成标签
        tags = []
        if is_negotiable:
            tags.append('可小刀')
        if is_shipped:
            tags.append('包邮')
        if random.random() > 0.7:
            tags.append(random.choice(['急出', '限时', '支持验机', '有发票', '保修中']))
        
        description = f"{'全新' if condition == '全新' else '二手'}{prefix}，{condition}，{random.choice(['功能完好', '无磕碰', '轻微使用痕迹', '9.5成新', '几乎全新'])}，{random.choice(['当面交易', '支持验货', '可议价', '诚心出售'])}"
        
        items.append({
            'seller_username': seller['username'],
            'category': category,
            'title': title,
            'description': description,
            'price': price,
            'original_price': original,
            'condition': condition,
            'location': location,
            'tags': json.dumps(tags, ensure_ascii=False),
            'is_negotiable': 1 if is_negotiable else 0,
            'is_shipped': 1 if is_shipped else 0,
        })
    
    return items

def generate_comments(users, items_count, count=1000):
    """生成评论数据"""
    comments = []
    for i in range(count):
        item_id = random.randint(1, min(items_count, 500))
        user = random.choice(users)
        content = random.choice(COMMENT_TEMPLATES)
        
        # 30% 的评论是回复
        parent_id = 'NULL'
        if random.random() < 0.3 and i > 100:
            parent_id = str(random.randint(max(1, i - 100), i))
        
        comments.append({
            'item_id': item_id,
            'username': user['username'],
            'parent_id': parent_id,
            'content': content,
        })
    
    return comments

def generate_transactions(users, items_count, count=500):
    """生成交易数据"""
    transactions = []
    statuses = ['pending', 'contacted', 'meeting', 'completed', 'cancelled']
    status_weights = [0.1, 0.3, 0.15, 0.35, 0.1]
    
    for i in range(count):
        buyer = random.choice(users)
        seller = random.choice(users)
        if buyer['username'] == seller['username']:
            continue
        
        item_id = random.randint(1, min(items_count, 500))
        price = round(random.uniform(20, 3000), 2)
        final_amount = round(price * random.uniform(0.85, 1.0), 2)  # 可能讨价还价
        status = random.choices(statuses, weights=status_weights)[0]
        location = random.choice(LOCATIONS)
        
        transactions.append({
            'item_id': item_id,
            'buyer_username': buyer['username'],
            'seller_username': seller['username'],
            'item_price': price,
            'final_amount': final_amount,
            'status': status,
            'meeting_location': location,
        })
    
    return transactions

def generate_messages(users, items_count, count=2000):
    """生成消息数据"""
    messages = []
    message_templates = [
        '你好，这个商品还在吗？',
        '可以看看实物吗？',
        '明天下午可以交易吗？',
        '价格能再便宜点吗？',
        '在哪里面交比较方便？',
        '好的，那就这样定了',
        '谢谢！',
        '不好意思，我不需要了',
        '已经买了别的',
        '等我考虑一下',
    ]
    
    for i in range(count):
        sender = random.choice(users)
        receiver = random.choice(users)
        if sender['username'] == receiver['username']:
            continue
        
        item_id = random.randint(1, min(items_count, 500))
        content = random.choice(message_templates)
        
        messages.append({
            'sender_username': sender['username'],
            'receiver_username': receiver['username'],
            'item_id': item_id,
            'content': content,
        })
    
    return messages

def write_mysql_inserts(filename, users, items, comments, transactions, messages):
    """生成 MySQL INSERT 语句"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("-- MySQL 大规模样例数据\n")
        f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- 数据量: {len(users)} 用户, {len(items)} 商品, {len(comments)} 评论, {len(transactions)} 交易, {len(messages)} 消息\n\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
        
        # 用户
        f.write("-- 插入用户数据\n")
        f.write("INSERT INTO users (username, email, student_id, password_hash, phone, avatar_url, real_name, is_verified, credit_score)\nVALUES\n")
        user_values = []
        for u in users:
            phone = f"138{random.randint(10000000, 99999999)}"
            avatar = f"/images/avatars/{u['username']}.jpg"
            verified = 'TRUE' if u['is_verified'] else 'FALSE'
            user_values.append(f"('{u['username']}', '{u['email']}', '{u['student_id']}', 'hashed_password', '{phone}', '{avatar}', '{u['real_name']}', {verified}, {u['credit_score']})")
        f.write(',\n'.join(user_values))
        f.write("\nON DUPLICATE KEY UPDATE username=VALUES(username);\n\n")
        
        # 商品
        f.write("-- 插入商品数据\n")
        batch_size = 100
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            f.write("INSERT INTO items (seller_id, category_id, title, description, price, original_price, condition_type, location, tags, is_negotiable, is_shipped)\nVALUES\n")
            item_values = []
            for item in batch:
                category_map = {
                    'electronics': 'electronics',
                    'books': 'books',
                    'daily': 'daily',
                    'sports': 'sports',
                    'fashion': 'fashion',
                    'beauty': 'beauty',
                }
                slug = category_map[item['category']]
                desc = item['description'].replace("'", "\\'")
                title = item['title'].replace("'", "\\'")
                item_values.append(f"((SELECT id FROM users WHERE username='{item['seller_username']}'), (SELECT id FROM categories WHERE slug='{slug}'), '{title}', '{desc}', {item['price']}, {item['original_price']}, '{item['condition']}', '{item['location']}', '{item['tags']}', {item['is_negotiable']}, {item['is_shipped']})")
            f.write(',\n'.join(item_values))
            f.write(";\n\n")
        
        # 商品图片
        f.write("-- 插入商品图片\n")
        f.write("INSERT INTO item_images (item_id, image_url, sort_order, is_cover)\n")
        f.write("SELECT id, CONCAT('/images/items/', id, '_1.jpg'), 0, TRUE FROM items WHERE id <= 500;\n\n")
        
        # 评论
        f.write("-- 插入评论数据\n")
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i+batch_size]
            f.write("INSERT INTO comments (item_id, user_id, parent_id, content)\nVALUES\n")
            comment_values = []
            for c in batch:
                content = c['content'].replace("'", "\\'")
                comment_values.append(f"({c['item_id']}, (SELECT id FROM users WHERE username='{c['username']}'), {c['parent_id']}, '{content}')")
            f.write(',\n'.join(comment_values))
            f.write(";\n\n")
        
        # 交易
        f.write("-- 插入交易数据\n")
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i+batch_size]
            f.write("INSERT INTO transactions (item_id, buyer_id, seller_id, item_price, final_amount, status, meeting_location)\nVALUES\n")
            trans_values = []
            for t in batch:
                trans_values.append(f"({t['item_id']}, (SELECT id FROM users WHERE username='{t['buyer_username']}'), (SELECT id FROM users WHERE username='{t['seller_username']}'), {t['item_price']}, {t['final_amount']}, '{t['status']}', '{t['meeting_location']}')")
            f.write(',\n'.join(trans_values))
            f.write(";\n\n")
        
        # 消息
        f.write("-- 插入消息数据\n")
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            f.write("INSERT INTO messages (sender_id, receiver_id, item_id, content)\nVALUES\n")
            msg_values = []
            for m in batch:
                content = m['content'].replace("'", "\\'")
                msg_values.append(f"((SELECT id FROM users WHERE username='{m['sender_username']}'), (SELECT id FROM users WHERE username='{m['receiver_username']}'), {m['item_id']}, '{content}')")
            f.write(',\n'.join(msg_values))
            f.write(";\n\n")
        
        # 收藏
        f.write("-- 插入收藏数据（随机500条）\n")
        f.write("INSERT IGNORE INTO favorites (user_id, item_id)\nVALUES\n")
        fav_values = []
        for i in range(500):
            user_idx = random.randint(0, len(users)-1)
            item_id = random.randint(1, min(len(items), 500))
            fav_values.append(f"((SELECT id FROM users WHERE username='{users[user_idx]['username']}'), {item_id})")
        f.write(',\n'.join(fav_values))
        f.write(";\n\n")
        
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n\n")
        f.write("SELECT 'Large dataset inserted successfully!' AS message;\n")

def main():
    print("生成大规模样例数据...")
    
    # 生成数据
    print("生成用户数据...")
    users = generate_users(200)
    
    print("生成商品数据...")
    items = generate_items(users, 500)
    
    print("生成评论数据...")
    comments = generate_comments(users, len(items), 1000)
    
    print("生成交易数据...")
    transactions = generate_transactions(users, len(items), 500)
    
    print("生成消息数据...")
    messages = generate_messages(users, len(items), 2000)
    
    # 写入文件
    print("写入 MySQL 文件...")
    write_mysql_inserts('mysql_large_dataset.sql', users, items, comments, transactions, messages)
    
    print(f"""
数据生成完成！
- 用户: {len(users)}
- 商品: {len(items)}
- 评论: {len(comments)}
- 交易: {len(transactions)}
- 消息: {len(messages)}
- 收藏: 500
    """)

if __name__ == '__main__':
    main()
