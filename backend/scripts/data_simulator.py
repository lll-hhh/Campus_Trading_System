#!/usr/bin/env python3
"""
数据流水模拟器 - 持续生成业务数据用于演示同步与管理后台

功能：
1. 模拟用户登录/注册活动
2. 模拟商品发布/更新/下架
3. 模拟交易创建/状态变更
4. 模拟消息发送
5. 模拟搜索历史生成
6. 触发同步事件

运行方式：
  python scripts/data_simulator.py [--interval 5] [--intensity medium]

参数：
  --interval: 操作间隔秒数 (默认 5)
  --intensity: 强度 low/medium/high (默认 medium)
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, update, func, text
from sqlalchemy.orm import Session

from apps.core.database import db_manager
from apps.core.models import (
    User,
    Item,
    Message,
    Conversation,
    SearchTrending,
)

# 模拟数据池
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
]

SEARCH_KEYWORDS = [
    "iPhone", "MacBook", "耳机", "平板", "Switch",
    "相机", "显示器", "键盘", "鼠标", "教材",
    "考研", "吉他", "健身", "冰箱", "自行车",
    "笔记本", "手机", "数码", "书籍", "生活用品",
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
]

TRANSACTION_STATUSES = ["pending", "confirmed", "paid", "shipped", "completed", "cancelled"]


class DataSimulator:
    """数据流水模拟器"""

    def __init__(self, interval: int = 5, intensity: str = "medium"):
        self.interval = interval
        self.intensity = intensity
        self.ops_per_cycle = {"low": 1, "medium": 3, "high": 6}.get(intensity, 3)
        self.cycle_count = 0
        self.stats = {
            "items_created": 0,
            "items_updated": 0,
            "transactions_created": 0,
            "transactions_updated": 0,
            "messages_sent": 0,
            "searches_logged": 0,
            "syncs_triggered": 0,
        }

    def log_audit(self, session: Session, user_id: int, table_name: str, operation: str, record_id: int, old_value: dict = None, new_value: dict = None):
        """记录审计日志 (使用原始 SQL 匹配数据库结构)"""
        import json
        session.execute(
            text("""
                INSERT INTO audit_logs (user_id, table_name, operation, record_id, old_value, new_value, created_at)
                VALUES (:user_id, :table_name, :operation, :record_id, :old_value, :new_value, :created_at)
            """),
            {
                "user_id": user_id,
                "table_name": table_name,
                "operation": operation,
                "record_id": record_id,
                "old_value": json.dumps(old_value) if old_value else None,
                "new_value": json.dumps(new_value) if new_value else None,
                "created_at": datetime.utcnow(),
            }
        )

    def get_random_user(self, session: Session) -> User | None:
        """获取随机用户"""
        count = session.execute(select(func.count()).select_from(User)).scalar() or 0
        if count == 0:
            return None
        offset = random.randint(0, max(0, count - 1))
        return session.execute(select(User).offset(offset).limit(1)).scalar_one_or_none()

    def get_random_item(self, session: Session, status: str = "available") -> Item | None:
        """获取随机商品"""
        query = select(Item).where(Item.status == status)
        count = session.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        if count == 0:
            return None
        offset = random.randint(0, max(0, count - 1))
        return session.execute(query.offset(offset).limit(1)).scalar_one_or_none()

    def simulate_item_publish(self, session: Session) -> bool:
        """模拟发布商品"""
        seller = self.get_random_user(session)
        if not seller:
            return False

        title = random.choice(ITEM_TITLES)
        item = Item(
            title=f"{title} #{random.randint(1000, 9999)}",
            description=random.choice(ITEM_DESCRIPTIONS),
            price=Decimal(str(random.randint(10, 5000))),
            original_price=Decimal(str(random.randint(100, 8000))),
            seller_id=seller.id,
            category_id=random.randint(1, 9),
            status="available",
            condition_type=random.choice(["全新", "99新", "95新", "9成新", "二手"]),
            view_count=random.randint(0, 50),
            favorite_count=random.randint(0, 10),
        )
        session.add(item)
        session.flush()

        # 记录审计日志 (使用辅助函数)
        self.log_audit(
            session, seller.id, "items", "INSERT", item.id, 
            new_value={"title": item.title, "price": float(item.price)}
        )

        self.stats["items_created"] += 1
        print(f"  📦 发布商品: {item.title[:30]}... (¥{item.price})")
        return True

    def simulate_item_update(self, session: Session) -> bool:
        """模拟更新商品"""
        item = self.get_random_item(session)
        if not item:
            return False

        # 随机操作：改价/改状态/增加浏览量
        action = random.choice(["price", "view", "status"])

        if action == "price":
            old_price = item.price
            change = Decimal(str(random.randint(-100, 100)))
            item.price = max(Decimal("1"), item.price + change)
            print(f"  💰 调价: {item.title[:20]}... ¥{old_price} → ¥{item.price}")
        elif action == "view":
            item.view_count += random.randint(1, 20)
            item.favorite_count += random.randint(0, 3)
            print(f"  👁️ 浏览增加: {item.title[:20]}... (浏览:{item.view_count})")
        else:
            if random.random() < 0.3:
                item.status = random.choice(["sold", "archived"])
                print(f"  🏷️ 状态变更: {item.title[:20]}... → {item.status}")

        # items 表有 updated_at，会自动更新
        self.stats["items_updated"] += 1
        return True

    def simulate_transaction(self, session: Session) -> bool:
        """模拟创建/更新交易 (使用原始 SQL 避免 ORM 查询 updated_at)"""
        # 70% 概率更新现有交易，30% 创建新交易
        if random.random() < 0.7:
            # 使用原始 SQL 查询避免 ORM 加载不存在的 updated_at 字段
            result = session.execute(
                text("""
                    SELECT id, status FROM transactions 
                    WHERE status IN ('pending', 'contacted', 'meeting')
                    ORDER BY RAND() LIMIT 1
                """)
            ).fetchone()

            if result:
                tx_id, old_status = result
                status_flow = {
                    "pending": ["contacted", "cancelled"],
                    "contacted": ["meeting", "cancelled"],
                    "meeting": ["completed", "cancelled"],
                }
                if old_status in status_flow:
                    new_status = random.choice(status_flow[old_status])
                    now = datetime.utcnow()
                    
                    # 构建更新 SQL
                    update_parts = ["status = :status"]
                    params = {"status": new_status, "tx_id": tx_id}
                    
                    if new_status == "completed":
                        update_parts.append("completed_at = :completed_at")
                        params["completed_at"] = now
                    elif new_status == "cancelled":
                        update_parts.append("cancelled_at = :cancelled_at")
                        params["cancelled_at"] = now
                    elif new_status == "contacted":
                        update_parts.append("contacted_at = :contacted_at")
                        params["contacted_at"] = now
                    
                    update_sql = f"UPDATE transactions SET {', '.join(update_parts)} WHERE id = :tx_id"
                    session.execute(text(update_sql), params)
                    
                    print(f"  🔄 交易状态: #{tx_id} {old_status} → {new_status}")
                    self.stats["transactions_updated"] += 1
                    return True
        
        # 创建新交易 - 也用原始 SQL
        item = self.get_random_item(session)
        buyer = self.get_random_user(session)
        if not item or not buyer or item.seller_id == buyer.id:
            return False

        now = datetime.utcnow()
        result = session.execute(
            text("""
                INSERT INTO transactions (item_id, buyer_id, seller_id, item_price, final_amount, status, created_at)
                VALUES (:item_id, :buyer_id, :seller_id, :item_price, :final_amount, :status, :created_at)
            """),
            {
                "item_id": item.id,
                "buyer_id": buyer.id,
                "seller_id": item.seller_id,
                "item_price": float(item.price),
                "final_amount": float(item.price),
                "status": "pending",
                "created_at": now,
            }
        )
        tx_id = result.lastrowid

        self.log_audit(
            session, buyer.id, "transactions", "INSERT", tx_id,
            new_value={"item_id": item.id, "amount": float(item.price)}
        )

        print(f"  🛒 新交易: #{tx_id} 商品#{item.id} ¥{item.price}")
        self.stats["transactions_created"] += 1
        return True

    def simulate_message(self, session: Session) -> bool:
        """模拟发送消息"""
        sender = self.get_random_user(session)
        receiver = self.get_random_user(session)
        if not sender or not receiver or sender.id == receiver.id:
            return False

        # 查找或创建会话
        conv = session.execute(
            select(Conversation).where(
                ((Conversation.user1_id == sender.id) & (Conversation.user2_id == receiver.id)) |
                ((Conversation.user1_id == receiver.id) & (Conversation.user2_id == sender.id))
            ).limit(1)
        ).scalar_one_or_none()

        if not conv:
            conv = Conversation(user1_id=sender.id, user2_id=receiver.id)
            session.add(conv)
            session.flush()

        content = random.choice(MESSAGE_CONTENTS)
        msg = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            content=content,
        )
        session.add(msg)
        
        # 更新会话最后消息 - conversations 表有 updated_at 自动更新
        conv.last_message_content = content
        conv.last_message_at = datetime.utcnow()

        print(f"  💬 消息: 用户#{sender.id} → 用户#{receiver.id}")
        self.stats["messages_sent"] += 1
        return True

    def simulate_search(self, session: Session) -> bool:
        """模拟搜索行为"""
        user = self.get_random_user(session)
        if not user:
            return False

        keyword = random.choice(SEARCH_KEYWORDS)
        
        # 记录搜索历史 (search_history 表没有 updated_at 字段)
        session.execute(
            text("""
                INSERT INTO search_history (user_id, keyword, result_count, created_at)
                VALUES (:user_id, :keyword, :result_count, :created_at)
            """),
            {
                "user_id": user.id,
                "keyword": keyword,
                "result_count": random.randint(0, 100),
                "created_at": datetime.utcnow(),
            }
        )

        # 更新热门搜索
        today = datetime.utcnow().date()
        trending = session.execute(
            select(SearchTrending).where(
                SearchTrending.keyword == keyword,
                SearchTrending.date == today
            )
        ).scalar_one_or_none()

        if trending:
            trending.search_count += 1
            trending.last_searched_at = datetime.utcnow()
        else:
            session.add(SearchTrending(
                keyword=keyword,
                search_count=1,
                date=today,
                last_searched_at=datetime.utcnow()
            ))

        print(f"  🔍 搜索: '{keyword}' by 用户#{user.id}")
        self.stats["searches_logged"] += 1
        return True

    def simulate_sync_event(self, session: Session) -> bool:
        """模拟同步事件记录 (使用原始 SQL 匹配数据库结构)"""
        import json
        source_db = random.choice(["mysql", "mariadb", "postgres"])
        target_db = random.choice(["mysql", "mariadb", "postgres"])
        status = random.choices(["completed", "failed"], weights=[0.9, 0.1])[0]
        started_at = datetime.utcnow() - timedelta(seconds=random.randint(1, 10))
        completed_at = datetime.utcnow() if status == "completed" else None
        stats = {
            "mode": random.choice(["full", "incremental"]),
            "duration_ms": random.randint(100, 2000),
            "tables": ["items", "transactions", "users"],
            "records_synced": random.randint(1, 50),
            "source_db": source_db,
            "target_db": target_db,
        }
        
        # sync_logs 表用 config_id 而不是 source_db/target_db
        session.execute(
            text("""
                INSERT INTO sync_logs (config_id, status, started_at, completed_at, stats, created_at)
                VALUES (:config_id, :status, :started_at, :completed_at, :stats, :created_at)
            """),
            {
                "config_id": 1,  # 假设 config_id 1 存在
                "status": status,
                "started_at": started_at,
                "completed_at": completed_at,
                "stats": json.dumps(stats),
                "created_at": datetime.utcnow(),
            }
        )
        print(f"  🔄 同步: {source_db} → {target_db} ({status})")
        self.stats["syncs_triggered"] += 1
        return True

    def run_cycle(self):
        """执行一个模拟周期"""
        self.cycle_count += 1
        print(f"\n{'='*50}")
        print(f"⏱️  周期 #{self.cycle_count} @ {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}")

        operations = [
            ("发布商品", self.simulate_item_publish, 0.2),
            ("更新商品", self.simulate_item_update, 0.25),
            ("交易流水", self.simulate_transaction, 0.25),
            ("发送消息", self.simulate_message, 0.15),
            ("搜索记录", self.simulate_search, 0.1),
            ("同步事件", self.simulate_sync_event, 0.05),
        ]

        for _ in range(self.ops_per_cycle):
            # 每个操作用独立的 session，避免死锁时整个周期失败
            with db_manager.session_scope("mysql") as session:
                # 按权重随机选择操作
                weights = [op[2] for op in operations]
                chosen = random.choices(operations, weights=weights, k=1)[0]
                name, func, _ = chosen
                try:
                    func(session)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    err_msg = str(e)[:80]
                    print(f"  ⚠️ {name} 失败: {err_msg}")

    def print_stats(self):
        """打印统计信息"""
        print(f"\n{'='*50}")
        print("📊 累计统计")
        print(f"{'='*50}")
        print(f"  商品发布: {self.stats['items_created']}")
        print(f"  商品更新: {self.stats['items_updated']}")
        print(f"  新建交易: {self.stats['transactions_created']}")
        print(f"  交易更新: {self.stats['transactions_updated']}")
        print(f"  消息发送: {self.stats['messages_sent']}")
        print(f"  搜索记录: {self.stats['searches_logged']}")
        print(f"  同步事件: {self.stats['syncs_triggered']}")

    def run(self):
        """主运行循环"""
        print(f"""
╔══════════════════════════════════════════════════╗
║     🎮 校园交易系统 - 数据流水模拟器              ║
╠══════════════════════════════════════════════════╣
║  间隔: {self.interval}秒  |  强度: {self.intensity}  |  每周期操作: {self.ops_per_cycle}次  ║
╚══════════════════════════════════════════════════╝

按 Ctrl+C 停止模拟...
""")

        try:
            while True:
                self.run_cycle()
                if self.cycle_count % 10 == 0:
                    self.print_stats()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n\n🛑 模拟器已停止")
            self.print_stats()


def main():
    parser = argparse.ArgumentParser(description="数据流水模拟器")
    parser.add_argument("--interval", type=int, default=5, help="操作间隔秒数 (默认 5)")
    parser.add_argument(
        "--intensity",
        choices=["low", "medium", "high"],
        default="medium",
        help="模拟强度 (默认 medium)",
    )
    args = parser.parse_args()

    simulator = DataSimulator(interval=args.interval, intensity=args.intensity)
    simulator.run()


if __name__ == "__main__":
    main()
