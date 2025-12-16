#!/usr/bin/env python3
"""
冲突制造脚本

用途：为管理后台「冲突记录 / 数据库状态」页面快速生成演示数据。
- 在 MySQL 主库写入 conflict_records 伪造冲突记录
- 可选持续运行，按间隔批量写入

示例：
  python scripts/conflict_simulator.py --batch 5 --interval 2 --loops 0  # 持续生成
  python scripts/conflict_simulator.py --batch 20 --interval 0          # 一次性生成 20 条
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from apps.core.database import db_manager
from apps.services.notifications import email_notifier

TABLES = ["items", "transactions", "inventory", "orders", "users"]
SOURCES = ["mysql", "postgres", "mariadb", "sqlite"]
STATUSES = ["pending", "manual", "auto_resolved", "failed"]


def generate_conflicts(batch: int) -> int:
    """在 MySQL 中插入 batch 条 conflict_records。"""
    inserted = 0
    with db_manager.session_scope("mysql") as session:
        for _ in range(batch):
            table = random.choice(TABLES)
            # conflict_records.record_id 是 BIGINT，使用递增整数，避免 DataError 1366
            record_id = int(f"{int(time.time())}{random.randint(1000, 9999)}")
            source, target = random.sample(SOURCES, 2)
            status = random.choices(STATUSES, weights=[0.6, 0.2, 0.1, 0.1])[0]
            reason = random.choice([
                "version_mismatch",
                "data_inconsistency",
                "constraint_violation",
            ])

            payload = {
                "reason": reason,
                "fields": {
                    "price": {
                        "source": round(random.uniform(10, 5000), 2),
                        "target": round(random.uniform(10, 5000), 2),
                    },
                    "updated_at": datetime.utcnow().isoformat(),
                },
                "suggestion": random.choice([
                    "采用来源库覆盖目标库",
                    "保留目标库并打回来源",
                    "人工核对后再同步",
                ]),
            }

            session.execute(
                text(
                    """
                    INSERT INTO conflict_records
                    (table_name, record_id, source_db, target_db, conflict_type, local_data, remote_data, resolved, resolution_strategy, created_at, updated_at, source, target, status, payload)
                    VALUES (:table_name, :record_id, :source_db, :target_db, :conflict_type, :local_data, :remote_data, :resolved, :resolution_strategy, :created_at, :updated_at, :source, :target, :status, :payload)
                    """
                ),
                {
                    "table_name": table,
                    "record_id": record_id,
                    "source_db": source,
                    "target_db": target,
                    "conflict_type": reason,
                    "local_data": json.dumps({"value": payload["fields"]["price"]["source"]}),
                    "remote_data": json.dumps({"value": payload["fields"]["price"]["target"]}),
                    "resolved": 0,
                    "resolution_strategy": "manual" if status == "manual" else None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "source": source,
                    "target": target,
                    "status": status,
                    "payload": json.dumps(payload),
                },
            )

            # 累加 daily_stats 中的冲突计数（方便看板展示）
            session.execute(
                text(
                    """
                    INSERT INTO daily_stats (stat_date, sync_conflict_count, sync_success_count, ai_request_count, inventory_changes)
                    VALUES (CURRENT_DATE(), 1, 0, 0, 0)
                    ON DUPLICATE KEY UPDATE sync_conflict_count = sync_conflict_count + 1
                    """
                )
            )
            inserted += 1
    return inserted


def run_loop(batch: int, interval: float, loops: int) -> None:
    count = 0
    try:
        while True:
            inserted = generate_conflicts(batch)
            count += inserted
            print(f"✅ 本轮插入 {inserted} 条冲突记录，累计 {count} 条")

            # 可选：发送邮件提醒（若未配置收件人/SMTP会自动跳过）
            try:
                subject = "同步冲突告警（模拟器）"
                body = (
                    f"本轮生成 {inserted} 条冲突记录，累计 {count} 条。\n"
                    f"来源脚本: conflict_simulator.py\n"
                    f"时间: {datetime.utcnow().isoformat()}"
                )
                email_notifier.send(subject, body)
            except Exception as exc:
                print(f"⚠️ 发送邮件提醒失败: {exc}")

            # 兜底：写入通知表（给管理员用户ID=1）
            try:
                with db_manager.session_scope("mysql") as sess:
                    sess.execute(
                        text(
                            """
                            INSERT INTO notifications (user_id, type, title, content, related_type, is_read, created_at, updated_at)
                            VALUES (:user_id, :type, :title, :content, :related_type, :is_read, :created_at, :updated_at)
                            """
                        ),
                        {
                            "user_id": 1,  # 管理员
                            "type": "system",
                            "title": "同步冲突告警",
                            "content": f"本轮生成 {inserted} 条冲突记录，累计 {count} 条。来源: conflict_simulator.py",
                            "related_type": "conflict",
                            "is_read": False,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        },
                    )
            except Exception as exc:
                print(f"⚠️ 写入通知表失败: {exc}")

            if loops > 0:
                loops -= 1
                if loops <= 0:
                    break
            if interval <= 0:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 已停止冲突模拟，总计插入:", count)


def main():
    parser = argparse.ArgumentParser(description="冲突记录模拟器")
    parser.add_argument("--batch", type=int, default=10, help="每轮生成条数，默认 10")
    parser.add_argument("--interval", type=float, default=3, help="每轮间隔秒，<=0 表示只跑一轮")
    parser.add_argument("--loops", type=int, default=0, help="轮数，0 表示无限循环直到 Ctrl+C")
    args = parser.parse_args()

    run_loop(batch=max(1, args.batch), interval=args.interval, loops=args.loops)


if __name__ == "__main__":
    main()
