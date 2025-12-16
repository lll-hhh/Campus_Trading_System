#!/usr/bin/env python3
"""
高并发数据流水模拟器 - 模拟成百上千用户同时操作

功能：
1. 使用线程池模拟大量并发用户
2. 每个"虚拟用户"独立执行操作
3. 支持配置并发用户数、操作频率
4. 实时统计 TPS/QPS

运行方式：
  python scripts/concurrent_simulator.py [--users 100] [--duration 60]

参数：
  --users: 并发用户数 (默认 100)
  --duration: 运行时长秒数 (默认 60，0 表示持续运行)
  --rate: 每用户每秒操作数 (默认 0.5)
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Callable
import signal

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from apps.core.database import db_manager
from apps.core.models import (
    User,
)

# ============== 模拟数据池 ==============
ITEM_TITLES = [
    "iPhone 15 Pro Max 256G 全新未拆封",
    "MacBook Air M3 8+256 教育优惠",
    "索尼 WH-1000XM5 降噪耳机",
    "小米平板6 Pro 8+256",
    "Switch OLED 日版 带塞尔达",
    "佳能 EOS R50 微单相机套机",
    "戴尔 U2723QE 4K 显示器",
    "雷蛇黑寡妇 V4 机械键盘",
    "罗技 MX Master 3S 鼠标",
    "AirPods Pro 2 USB-C 版",
    "二手教材《高等数学》同济第七版",
    "考研英语真题全套 2015-2024",
    "CPA 教材全套 2024 版",
    "吉他 雅马哈 F310 入门款",
    "健身哑铃 20kg 可调节",
    "宿舍小冰箱 45L 九成新",
    "台灯 护眼 LED 可调光",
    "书架 实木 四层 自提",
    "自行车 捷安特 ATX660",
    "电动滑板车 小米 Pro2",
    "显卡 RTX 4060 全新",
    "机械硬盘 4TB 西数蓝盘",
    "固态硬盘 1TB 三星 980Pro",
    "路由器 小米 AX6000",
    "充电宝 20000mAh 紫米",
]

ITEM_DESCRIPTIONS = [
    "几乎全新，买来没怎么用，现在换了所以出掉",
    "自用一学期，成色很好，配件齐全",
    "毕业清仓，低价出售，可小刀",
    "正品保证，支持验货，价格可议",
    "急出！价格好商量，诚心要可私聊",
    "同城可面交，外地顺丰到付",
    "保修期内，有发票，放心购买",
    "限时特价，先到先得！",
    "学长毕业甩卖，物美价廉",
    "九成新，无任何问题",
]

SEARCH_KEYWORDS = [
    "iPhone", "MacBook", "耳机", "平板", "Switch",
    "相机", "显示器", "键盘", "鼠标", "教材",
    "考研", "吉他", "健身", "冰箱", "自行车",
    "笔记本", "手机", "数码", "书籍", "生活用品",
    "显卡", "硬盘", "路由器", "充电宝", "手表",
]

MESSAGE_CONTENTS = [
    "你好，请问这个还在吗？",
    "可以便宜点吗？",
    "什么时候方便看货？",
    "能包邮吗？",
    "有瑕疵吗？",
    "可以走闲鱼吗？",
    "今天能交易吗？",
    "请问是正品吗？",
    "还能再少点不？",
    "我想要了，怎么联系？",
    "最低多少？",
    "可以留个联系方式吗？",
    "东西还在吗？",
    "同学校吗？可以面交",
    "有实物图吗？",
]


class Stats:
    """线程安全的统计计数器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._counts: Dict[str, int] = defaultdict(int)
        self._errors: Dict[str, int] = defaultdict(int)
        self._start_time = time.time()
        self._recent_ops: List[float] = []  # 记录最近的操作时间戳
    
    def inc(self, key: str, count: int = 1):
        with self._lock:
            self._counts[key] += count
            self._recent_ops.append(time.time())
            # 只保留最近 10 秒的操作
            cutoff = time.time() - 10
            self._recent_ops = [t for t in self._recent_ops if t > cutoff]
    
    def inc_error(self, key: str):
        with self._lock:
            self._errors[key] += 1
    
    def get_stats(self) -> dict:
        with self._lock:
            elapsed = time.time() - self._start_time
            total_ops = sum(self._counts.values())
            total_errors = sum(self._errors.values())
            
            # 计算最近 10 秒的 TPS
            cutoff = time.time() - 10
            recent_count = len([t for t in self._recent_ops if t > cutoff])
            recent_tps = recent_count / 10 if recent_count > 0 else 0
            
            return {
                "elapsed_seconds": round(elapsed, 1),
                "total_operations": total_ops,
                "total_errors": total_errors,
                "avg_tps": round(total_ops / elapsed, 2) if elapsed > 0 else 0,
                "recent_tps": round(recent_tps, 2),
                "by_type": dict(self._counts),
                "errors_by_type": dict(self._errors),
            }


class VirtualUser:
    """虚拟用户 - 模拟单个用户的所有行为"""
    
    def __init__(self, user_id: int, stats: Stats):
        self.user_id = user_id
        self.stats = stats
        self._user_db_id: int | None = None
    
    def _get_db_user_id(self, session: Session) -> int:
        """获取数据库中的真实用户 ID"""
        if self._user_db_id is None:
            # 随机选一个用户作为这个虚拟用户的身份
            count = session.execute(select(func.count()).select_from(User)).scalar() or 0
            if count == 0:
                raise ValueError("No users in database")
            offset = self.user_id % count
            user = session.execute(select(User).offset(offset).limit(1)).scalar_one()
            self._user_db_id = user.id
        return self._user_db_id
    
    def browse_items(self, session: Session) -> bool:
        """浏览商品 - 增加浏览量"""
        result = session.execute(
            text("SELECT id, view_count FROM items WHERE status = 'available' ORDER BY RAND() LIMIT 1")
        ).fetchone()
        
        if not result:
            return False
        
        item_id, current_views = result
        session.execute(
            text("UPDATE items SET view_count = view_count + 1 WHERE id = :id"),
            {"id": item_id}
        )
        self.stats.inc("browse")
        return True
    
    def search_items(self, session: Session) -> bool:
        """搜索商品"""
        user_id = self._get_db_user_id(session)
        keyword = random.choice(SEARCH_KEYWORDS)
        
        session.execute(
            text("""
                INSERT INTO search_history (user_id, keyword, result_count, created_at)
                VALUES (:user_id, :keyword, :result_count, :created_at)
            """),
            {
                "user_id": user_id,
                "keyword": keyword,
                "result_count": random.randint(0, 100),
                "created_at": datetime.utcnow(),
            }
        )
        self.stats.inc("search")
        return True
    
    def publish_item(self, session: Session) -> bool:
        """发布商品"""
        user_id = self._get_db_user_id(session)
        title = f"{random.choice(ITEM_TITLES)} #{random.randint(1000, 9999)}"
        price = Decimal(str(random.randint(10, 5000)))
        
        result = session.execute(
            text("""
                INSERT INTO items (seller_id, category_id, title, description, price, 
                    original_price, condition_type, status, view_count, favorite_count, created_at, updated_at)
                VALUES (:seller_id, :category_id, :title, :description, :price,
                    :original_price, :condition_type, :status, :view_count, :favorite_count, :created_at, :updated_at)
            """),
            {
                "seller_id": user_id,
                "category_id": random.randint(1, 9),
                "title": title,
                "description": random.choice(ITEM_DESCRIPTIONS),
                "price": float(price),
                "original_price": float(price * Decimal("1.2")),
                "condition_type": random.choice(["全新", "99新", "95新", "9成新", "二手"]),
                "status": "available",
                "view_count": 0,
                "favorite_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        
        # 记录审计日志
        item_id = result.lastrowid
        session.execute(
            text("""
                INSERT INTO audit_logs (user_id, table_name, operation, record_id, new_value, created_at)
                VALUES (:user_id, :table_name, :operation, :record_id, :new_value, :created_at)
            """),
            {
                "user_id": user_id,
                "table_name": "items",
                "operation": "INSERT",
                "record_id": item_id,
                "new_value": json.dumps({"title": title, "price": float(price)}),
                "created_at": datetime.utcnow(),
            }
        )
        
        self.stats.inc("publish")
        return True
    
    def update_item_price(self, session: Session) -> bool:
        """更新商品价格"""
        user_id = self._get_db_user_id(session)
        
        result = session.execute(
            text("SELECT id, price FROM items WHERE seller_id = :user_id AND status = 'available' ORDER BY RAND() LIMIT 1"),
            {"user_id": user_id}
        ).fetchone()
        
        if not result:
            return False
        
        item_id, old_price = result
        change = random.randint(-50, 50)
        new_price = max(1, float(old_price) + change)
        
        session.execute(
            text("UPDATE items SET price = :price, updated_at = :updated_at WHERE id = :id"),
            {"price": new_price, "updated_at": datetime.utcnow(), "id": item_id}
        )
        self.stats.inc("price_update")
        return True
    
    def add_to_favorites(self, session: Session) -> bool:
        """收藏商品"""
        user_id = self._get_db_user_id(session)
        
        result = session.execute(
            text("""
                SELECT id FROM items 
                WHERE status = 'available' AND seller_id != :user_id 
                AND id NOT IN (SELECT item_id FROM favorites WHERE user_id = :user_id)
                ORDER BY RAND() LIMIT 1
            """),
            {"user_id": user_id}
        ).fetchone()
        
        if not result:
            return False
        
        item_id = result[0]
        session.execute(
            text("""
                INSERT INTO favorites (user_id, item_id, created_at, updated_at)
                VALUES (:user_id, :item_id, :created_at, :updated_at)
            """),
            {
                "user_id": user_id,
                "item_id": item_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        
        # 更新商品收藏数
        session.execute(
            text("UPDATE items SET favorite_count = favorite_count + 1 WHERE id = :id"),
            {"id": item_id}
        )
        
        self.stats.inc("favorite")
        return True
    
    def send_message(self, session: Session) -> bool:
        """发送消息"""
        sender_id = self._get_db_user_id(session)
        
        # 随机选择一个收件人
        result = session.execute(
            text("SELECT id FROM users WHERE id != :sender_id ORDER BY RAND() LIMIT 1"),
            {"sender_id": sender_id}
        ).fetchone()
        
        if not result:
            return False
        
        receiver_id = result[0]
        content = random.choice(MESSAGE_CONTENTS)
        
        # 查找或创建会话
        conv = session.execute(
            text("""
                SELECT id FROM conversations 
                WHERE (user1_id = :u1 AND user2_id = :u2) OR (user1_id = :u2 AND user2_id = :u1)
                LIMIT 1
            """),
            {"u1": sender_id, "u2": receiver_id}
        ).fetchone()
        
        if not conv:
            session.execute(
                text("""
                    INSERT INTO conversations (user1_id, user2_id, created_at, updated_at)
                    VALUES (:u1, :u2, :created_at, :updated_at)
                """),
                {"u1": sender_id, "u2": receiver_id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            )
        
        # 发送消息
        session.execute(
            text("""
                INSERT INTO messages (sender_id, receiver_id, content, created_at, updated_at)
                VALUES (:sender_id, :receiver_id, :content, :created_at, :updated_at)
            """),
            {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "content": content,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        
        self.stats.inc("message")
        return True
    
    def create_transaction(self, session: Session) -> bool:
        """创建交易"""
        buyer_id = self._get_db_user_id(session)
        
        # 找一个可购买的商品
        result = session.execute(
            text("""
                SELECT id, seller_id, price FROM items 
                WHERE status = 'available' AND seller_id != :buyer_id 
                ORDER BY RAND() LIMIT 1
            """),
            {"buyer_id": buyer_id}
        ).fetchone()
        
        if not result:
            return False
        
        item_id, seller_id, price = result
        
        session.execute(
            text("""
                INSERT INTO transactions (item_id, buyer_id, seller_id, item_price, final_amount, status, created_at)
                VALUES (:item_id, :buyer_id, :seller_id, :price, :price, 'pending', :created_at)
            """),
            {
                "item_id": item_id,
                "buyer_id": buyer_id,
                "seller_id": seller_id,
                "price": float(price),
                "created_at": datetime.utcnow(),
            }
        )
        
        self.stats.inc("transaction_create")
        return True
    
    def update_transaction(self, session: Session) -> bool:
        """更新交易状态"""
        user_id = self._get_db_user_id(session)
        
        result = session.execute(
            text("""
                SELECT id, status FROM transactions 
                WHERE (buyer_id = :user_id OR seller_id = :user_id)
                AND status IN ('pending', 'contacted', 'meeting')
                ORDER BY RAND() LIMIT 1
            """),
            {"user_id": user_id}
        ).fetchone()
        
        if not result:
            return False
        
        tx_id, old_status = result
        status_flow = {
            "pending": ["contacted", "cancelled"],
            "contacted": ["meeting", "cancelled"],
            "meeting": ["completed", "cancelled"],
        }
        
        if old_status not in status_flow:
            return False
        
        new_status = random.choice(status_flow[old_status])
        now = datetime.utcnow()
        
        update_sql = "UPDATE transactions SET status = :status"
        params = {"status": new_status, "tx_id": tx_id}
        
        if new_status == "completed":
            update_sql += ", completed_at = :time"
            params["time"] = now
        elif new_status == "cancelled":
            update_sql += ", cancelled_at = :time"
            params["time"] = now
        elif new_status == "contacted":
            update_sql += ", contacted_at = :time"
            params["time"] = now
        
        update_sql += " WHERE id = :tx_id"
        session.execute(text(update_sql), params)
        
        self.stats.inc("transaction_update")
        return True
    
    def do_random_action(self) -> bool:
        """执行随机操作"""
        # 操作权重分布 (模拟真实用户行为)
        actions: List[tuple[Callable, float]] = [
            (self.browse_items, 0.35),      # 浏览最多
            (self.search_items, 0.20),      # 搜索次之
            (self.send_message, 0.15),      # 消息
            (self.add_to_favorites, 0.10),  # 收藏
            (self.create_transaction, 0.08), # 创建交易
            (self.update_transaction, 0.05), # 更新交易
            (self.publish_item, 0.04),       # 发布商品
            (self.update_item_price, 0.03),  # 改价
        ]
        
        # 按权重选择操作
        weights = [a[1] for a in actions]
        chosen_action = random.choices(actions, weights=weights, k=1)[0][0]
        
        try:
            with db_manager.session_scope("mysql") as session:
                result = chosen_action(session)
                session.commit()
                return result
        except Exception:
            self.stats.inc_error(chosen_action.__name__)
            return False


class ConcurrentSimulator:
    """高并发模拟器"""
    
    def __init__(self, num_users: int, rate_per_user: float, duration: int):
        self.num_users = num_users
        self.rate_per_user = rate_per_user  # 每用户每秒操作数
        self.duration = duration  # 0 表示持续运行
        self.stats = Stats()
        self.running = True
        self.users: List[VirtualUser] = []
        
        # 创建虚拟用户
        for i in range(num_users):
            self.users.append(VirtualUser(i, self.stats))
    
    def user_loop(self, user: VirtualUser):
        """单个用户的操作循环"""
        interval = 1.0 / self.rate_per_user if self.rate_per_user > 0 else 2.0
        
        while self.running:
            user.do_random_action()
            # 添加随机抖动，模拟真实用户行为
            jitter = random.uniform(0.5, 1.5)
            time.sleep(interval * jitter)
    
    def stats_reporter(self):
        """定期报告统计信息"""
        while self.running:
            time.sleep(5)
            stats = self.stats.get_stats()
            print(f"""
╔══════════════════════════════════════════════════════════════╗
║  ⏱️  运行时间: {stats['elapsed_seconds']}s  |  👥 并发用户: {self.num_users}
║  📊 总操作数: {stats['total_operations']}  |  ❌ 错误: {stats['total_errors']}
║  🚀 平均 TPS: {stats['avg_tps']}  |  📈 实时 TPS: {stats['recent_tps']}
╠══════════════════════════════════════════════════════════════╣
║  操作明细:
║    👁️  浏览: {stats['by_type'].get('browse', 0):>6}    🔍 搜索: {stats['by_type'].get('search', 0):>6}
║    💬 消息: {stats['by_type'].get('message', 0):>6}    ⭐ 收藏: {stats['by_type'].get('favorite', 0):>6}
║    📦 发布: {stats['by_type'].get('publish', 0):>6}    💰 改价: {stats['by_type'].get('price_update', 0):>6}
║    🛒 下单: {stats['by_type'].get('transaction_create', 0):>6}    🔄 交易: {stats['by_type'].get('transaction_update', 0):>6}
╚══════════════════════════════════════════════════════════════╝
""")
    
    def run(self):
        """启动模拟器"""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║     🎮 校园交易系统 - 高并发数据模拟器                        ║
╠══════════════════════════════════════════════════════════════╣
║  👥 并发用户数: {self.num_users}
║  ⚡ 每用户操作频率: {self.rate_per_user} 次/秒
║  ⏱️  预计总 TPS: {self.num_users * self.rate_per_user:.1f}
║  🕐 运行时长: {'持续运行' if self.duration == 0 else f'{self.duration}秒'}
╚══════════════════════════════════════════════════════════════╝

按 Ctrl+C 停止模拟...
""")
        
        # 设置信号处理
        def signal_handler(sig, frame):
            print("\n\n🛑 收到停止信号，正在关闭...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动统计报告线程
        stats_thread = threading.Thread(target=self.stats_reporter, daemon=True)
        stats_thread.start()
        
        # 使用线程池运行所有虚拟用户
        with ThreadPoolExecutor(max_workers=min(self.num_users, 200)) as executor:
            futures = []
            for user in self.users:
                future = executor.submit(self.user_loop, user)
                futures.append(future)
            
            # 如果设置了时长，等待时长结束
            if self.duration > 0:
                time.sleep(self.duration)
                self.running = False
            else:
                # 持续运行直到被中断
                try:
                    while self.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.running = False
        
        # 打印最终统计
        final_stats = self.stats.get_stats()
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    📊 最终统计报告                            ║
╠══════════════════════════════════════════════════════════════╣
║  ⏱️  总运行时间: {final_stats['elapsed_seconds']} 秒
║  📊 总操作数: {final_stats['total_operations']}
║  ❌ 总错误数: {final_stats['total_errors']}
║  🚀 平均 TPS: {final_stats['avg_tps']}
╠══════════════════════════════════════════════════════════════╣
║  操作统计:
║    👁️  浏览商品: {final_stats['by_type'].get('browse', 0)}
║    🔍 搜索商品: {final_stats['by_type'].get('search', 0)}
║    💬 发送消息: {final_stats['by_type'].get('message', 0)}
║    ⭐ 收藏商品: {final_stats['by_type'].get('favorite', 0)}
║    📦 发布商品: {final_stats['by_type'].get('publish', 0)}
║    💰 更新价格: {final_stats['by_type'].get('price_update', 0)}
║    🛒 创建交易: {final_stats['by_type'].get('transaction_create', 0)}
║    🔄 更新交易: {final_stats['by_type'].get('transaction_update', 0)}
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(description="高并发数据模拟器")
    parser.add_argument("--users", type=int, default=100, help="并发用户数 (默认 100)")
    parser.add_argument("--duration", type=int, default=0, help="运行时长秒数 (默认 0 表示持续运行)")
    parser.add_argument("--rate", type=float, default=0.5, help="每用户每秒操作数 (默认 0.5)")
    args = parser.parse_args()
    
    simulator = ConcurrentSimulator(
        num_users=args.users,
        rate_per_user=args.rate,
        duration=args.duration
    )
    simulator.run()


if __name__ == "__main__":
    main()
