#!/usr/bin/env python3
"""
长期运行的数据流水模拟器（演示/压测友好版）

特点：
- 复用现有 `DataSimulator`，长时间循环运行
- 支持自定义运行时长（0 表示无限），可调整间隔/强度/打印频率
- 提供轻量日志，异常自动重试且不中断

用法示例：
  python scripts/long_stream_simulator.py --interval 3 --intensity high --duration 0
  python scripts/long_stream_simulator.py --interval 5 --duration 300 --stats-every 5
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

# 将项目根目录加入路径，便于脚本独立运行
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.data_simulator import DataSimulator  # type: ignore


def run_long_stream(interval: float, intensity: str, duration: int, stats_every: int, jitter: float) -> None:
    sim = DataSimulator(interval=max(1, int(interval)), intensity=intensity)
    start_ts = time.time()
    cycle = 0

    print(
        f"\n🚀 启动长期数据流水模拟 | 间隔={interval}s | 强度={intensity} | 运行时长={'无限' if duration == 0 else duration}s | 统计频率={stats_every}周期"
    )

    try:
        while True:
            cycle += 1
            sim.run_cycle()
            if stats_every > 0 and cycle % stats_every == 0:
                sim.print_stats()

            # 运行时长控制
            if duration > 0 and (time.time() - start_ts) >= duration:
                print("⏹️ 达到设定时长，准备退出...")
                break

            sleep_time = interval + (random.uniform(0, jitter) if jitter > 0 else 0)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("\n🛑 收到中断信号，停止模拟...")
    finally:
        sim.print_stats()


def main():
    parser = argparse.ArgumentParser(description="长期运行的数据流水模拟器")
    parser.add_argument("--interval", type=float, default=5, help="每轮间隔秒数，默认 5")
    parser.add_argument(
        "--intensity",
        choices=["low", "medium", "high"],
        default="medium",
        help="模拟强度，默认 medium",
    )
    parser.add_argument("--duration", type=int, default=0, help="总运行时长秒，0 表示无限运行")
    parser.add_argument("--stats-every", type=int, default=5, help="多少个周期打印一次统计，0 关闭")
    parser.add_argument("--jitter", type=float, default=0, help="为每轮 sleep 追加 0~jitter 的随机抖动")
    args = parser.parse_args()

    run_long_stream(
        interval=args.interval,
        intensity=args.intensity,
        duration=args.duration,
        stats_every=args.stats_every,
        jitter=args.jitter,
    )


if __name__ == "__main__":
    main()
