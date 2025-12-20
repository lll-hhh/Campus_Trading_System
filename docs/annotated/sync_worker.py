"""Annotated copy of `backend/apps/services/sync_worker.py` with per-line comments.
仅作阅读与答辩说明，不用于运行。
"""
from __future__ import annotations  # 注: 启用未来注解支持

import argparse  # 注: CLI 参数解析
import os  # 注: 环境变量访问
import signal  # 注: 信号处理
import socket  # 注: 获取主机名作为 consumer 名称
import time  # 注: sleep 等时间控制
from threading import Event  # 注: 用于停止标志
from typing import Iterable  # 注: 类型提示

from loguru import logger  # 注: 日志记录
from redis.exceptions import RedisError, ResponseError  # 注: Redis 异常类型

from apps.core.sync_engine import SyncEvent, sync_engine  # 注: 导入 SyncEvent 和全局 sync_engine


ALL_TARGETS: tuple[str, ...] = ("mysql", "mariadb", "postgres", "sqlite")  # 注: 支持的目标数据库列表
STOP_EVENT = Event()  # 注: 全局停止事件


def _ensure_consumer_group(group_name: str) -> None:  # 注: 创建 consumer group（如果不存在）
    redis_client = sync_engine.redis_client
    try:
        redis_client.xgroup_create(
            sync_engine.stream_key,
            group_name,
            id="0-0",
            mkstream=True,
        )
        logger.info(
            "Created Redis consumer group",
            group=group_name,
            stream=sync_engine.stream_key,
        )
    except ResponseError as exc:  # group already exists
        if "BUSYGROUP" in str(exc):
            logger.debug(
                "Redis consumer group already exists",
                group=group_name,
                stream=sync_engine.stream_key,
            )
        else:  # pragma: no cover - unexpected redis error
            raise


def _handle_shutdown(signum: int, _frame: object) -> None:  # pragma: no cover - signal
    logger.warning("Sync worker received shutdown signal", signal=signum)
    STOP_EVENT.set()  # 注: 收到信号时设置停止事件


def consume_events(
    batch_size: int = 100,
    block_ms: int = 5000,
    replay_pending: bool = True,
    idle_sleep: float = 1.0,
    max_batches: int | None = None,
) -> int:  # 注: 从 Redis stream 拉取并处理事件
    redis_client = sync_engine.redis_client
    group_name = os.getenv("SYNC_STREAM_GROUP", "campuswap-sync-group")
    consumer_name = os.getenv("SYNC_CONSUMER_NAME", socket.gethostname())
    _ensure_consumer_group(group_name)

    read_id = "0" if replay_pending else ">"
    processed = 0
    batches = 0

    while not STOP_EVENT.is_set():
        try:
            response = redis_client.xreadgroup(
                group_name,
                consumer_name,
                {sync_engine.stream_key: read_id},
                count=batch_size,
                block=block_ms,
            )
        except RedisError as exc:  # pragma: no cover - network failure
            logger.exception("Redis read failed", error=str(exc))
            time.sleep(idle_sleep)
            continue

        if not response:
            read_id = ">"
            time.sleep(idle_sleep)
            if max_batches is not None:
                batches += 1
                if batches >= max_batches:
                    break
            continue

        for stream_key, events in response:
            for event_id, payload in events:
                try:
                    sync_event = SyncEvent.from_stream(payload)
                    targets: Iterable[str] = tuple(t for t in ALL_TARGETS if t != sync_event.origin)
                    sync_engine.replicate(sync_event, targets)
                    processed += 1
                    logger.info(
                        "Replicated event",
                        stream=stream_key,
                        event_id=event_id,
                        targets=list(targets),
                    )
                except Exception as exc:  # pragma: no cover - defensive catch
                    logger.exception(
                        "Failed to process sync event",
                        event_id=event_id,
                        error=str(exc),
                    )
                finally:
                    redis_client.xack(stream_key, group_name, event_id)  # 注: 确认消息已处理

        read_id = ">"
        batches += 1
        if max_batches is not None and batches >= max_batches:
            break

    return processed


def run_worker(
    batch_size: int = 100,
    block_ms: int = 5000,
    replay_pending: bool = True,
    idle_sleep: float = 1.0,
) -> None:  # 注: 长期运行的 worker 主循环包装
    for sig in (signal.SIGINT, signal.SIGTERM):  # pragma: no cover - runtime hook
        signal.signal(sig, _handle_shutdown)

    logger.info(
        "Starting sync worker",
        batch_size=batch_size,
        block_ms=block_ms,
        replay_pending=replay_pending,
    )
    processed = consume_events(
        batch_size=batch_size,
        block_ms=block_ms,
        replay_pending=replay_pending,
        idle_sleep=idle_sleep,
    )
    logger.info("Sync worker stopped", processed_events=processed)


def _build_parser() -> argparse.ArgumentParser:  # 注: CLI 参数解析器构造
    parser = argparse.ArgumentParser(description="CampuSwap Sync Worker")
    parser.add_argument("--batch-size", type=int, default=100, help="Max events per Redis read")
    parser.add_argument("--block-ms", type=int, default=5000, help="Blocking read timeout")
    parser.add_argument(
        "--no-replay", action="store_true", help="Skip replaying pending entries on startup"
    )
    parser.add_argument(
        "--idle-sleep", type=float, default=1.0, help="Seconds to sleep when stream is idle"
    )
    return parser


def main() -> None:  # pragma: no cover - CLI
    args = _build_parser().parse_args()
    run_worker(
        batch_size=args.batch_size,
        block_ms=args.block_ms,
        replay_pending=not args.no_replay,
        idle_sleep=args.idle_sleep,
    )


if __name__ == "__main__":  # pragma: no cover - CLI bootstrap
    main()
