#!/usr/bin/env python3
"""
同步操作与指标模拟脚本

用途：为管理后台「同步热力图 / 性能指标 / 同步日志」生成演示数据。
- 生成 sync_logs 记录（含源/目标、耗时、模式）
- 生成 performance_metrics 记录（模拟慢查询、延迟告警）
- 聚合到 daily_stats，便于看板展示

示例：
  python scripts/sync_simulator.py --batch 5 --interval 2 --loops 0
  python scripts/sync_simulator.py --batch 20 --interval 0
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from apps.core.database import db_manager

SOURCES = ["mysql", "postgres", "mariadb", "sqlite"]
MODES = ["full", "incremental", "realtime"]
TABLES = ["items", "transactions", "users", "orders", "inventory"]


def insert_sync_batch(batch: int) -> int:
    inserted = 0
    with db_manager.session_scope("mysql") as session:
        for _ in range(batch):
            source, target = random.sample(SOURCES, 2)
            mode = random.choice(MODES)
            duration_ms = random.randint(80, 2500)
            status = random.choices(["completed", "failed"], weights=[0.9, 0.1])[0]
            started_at = datetime.utcnow() - timedelta(seconds=random.randint(1, 15))
            completed_at = datetime.utcnow() if status == "completed" else None
            stats = {
                "mode": mode,
                "duration_ms": duration_ms,
                "tables": random.sample(TABLES, k=random.randint(2, min(4, len(TABLES)))),
                "records_synced": random.randint(5, 120),
                "source_db": source,
                "target_db": target,
            }

            session.execute(
                text(
                    """
                    INSERT INTO sync_logs (config_id, status, started_at, completed_at, stats)
                    VALUES (:config_id, :status, :started_at, :completed_at, :stats)
                    """
                ),
                {
                    "config_id": 1,
                    "status": status,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "stats": json.dumps(stats),
                },
            )

            # 为性能指标写入一条记录
            metric = {
                "metric_type": "query_time",
                "db_name": target,
                "metric_value": round(random.uniform(10, 300), 1),
                "threshold": random.choice([120.0, 180.0, 220.0]),
                "alert": random.random() < 0.25,
                "details": json.dumps(
                    {
                        "sql": f"SELECT * FROM {random.choice(TABLES)} LIMIT 100",
                        "table": random.choice(TABLES),
                        "count": random.randint(50, 500),
                        "max_time": round(random.uniform(20, 350), 2),
                        "rows": random.randint(10, 800),
                        "suggestion": "为高频过滤列添加复合索引",
                    }
                ),
            }
            session.execute(
                text(
                    """
                    INSERT INTO performance_metrics
                    (metric_type, db_name, metric_value, threshold_value, is_alert, details, recorded_at)
                    VALUES (:metric_type, :db_name, :metric_value, :threshold, :alert, :details, :recorded_at)
                    """
                ),
                {
                    "metric_type": metric["metric_type"],
                    "db_name": metric["db_name"],
                    "metric_value": metric["metric_value"],
                    "threshold": metric["threshold"],
                    "alert": metric["alert"],
                    "details": metric["details"],
                    "recorded_at": datetime.utcnow(),
                },
            )

            # 聚合到每日统计
            session.execute(
                text(
                    """
                    INSERT INTO daily_stats (stat_date, sync_success_count, sync_conflict_count, ai_request_count, inventory_changes)
                    VALUES (CURRENT_DATE(), 1, 0, 0, 0)
                    ON DUPLICATE KEY UPDATE sync_success_count = sync_success_count + 1
                    """
                )
            )
            inserted += 1
    return inserted


def run_loop(batch: int, interval: float, loops: int) -> None:
    total = 0
    try:
        while True:
            inserted = insert_sync_batch(batch)
            total += inserted
            print(f"✅ 本轮生成同步/指标 {inserted} 条，累计 {total} 条")
            if loops > 0:
                loops -= 1
                if loops <= 0:
                    break
            if interval <= 0:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 已停止同步模拟，总计插入:", total)


def main():
    parser = argparse.ArgumentParser(description="同步操作模拟器")
    parser.add_argument("--batch", type=int, default=10, help="每轮生成条数，默认 10")
    parser.add_argument("--interval", type=float, default=3, help="每轮间隔秒，<=0 表示只跑一轮")
    parser.add_argument("--loops", type=int, default=0, help="轮数，0 表示无限循环直到 Ctrl+C")
    args = parser.parse_args()

    run_loop(batch=max(1, args.batch), interval=args.interval, loops=args.loops)


if __name__ == "__main__":
    main()
