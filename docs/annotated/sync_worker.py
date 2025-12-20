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
    redis_client = sync_engine.redis_client  # 注: 获取 Redis 客户端
    try:
        redis_client.xgroup_create(  # 注: 尝试创建消费者组
            sync_engine.stream_key,
            group_name,
            id="0-0",
            mkstream=True,
        )
        logger.info(  # 注: 记录创建成功日志
            "Created Redis consumer group",
            group=group_name,
            stream=sync_engine.stream_key,
        )
    except ResponseError as exc:  # group already exists
        if "BUSYGROUP" in str(exc):  # 注: 如果组已存在，忽略错误
            logger.debug(
                "Redis consumer group already exists",
                group=group_name,
                stream=sync_engine.stream_key,
            )
        else:  # pragma: no cover - unexpected redis error
            raise  # 注: 其他错误抛出


def _handle_shutdown(signum: int, _frame: object) -> None:  # pragma: no cover - signal
    logger.warning("Sync worker received shutdown signal", signal=signum)  # 注: 记录停机信号
    STOP_EVENT.set()  # 注: 收到信号时设置停止事件


def consume_events(
    batch_size: int = 100,
    block_ms: int = 5000,
    replay_pending: bool = True,
    idle_sleep: float = 1.0,
    max_batches: int | None = None,
) -> int:  # 注: 从 Redis stream 拉取并处理事件
    redis_client = sync_engine.redis_client  # 注: 获取 Redis 客户端
    group_name = os.getenv("SYNC_STREAM_GROUP", "campuswap-sync-group")  # 注: 获取消费者组名
    consumer_name = os.getenv("SYNC_CONSUMER_NAME", socket.gethostname())  # 注: 获取消费者名
    _ensure_consumer_group(group_name)  # 注: 确保组存在

    read_id = "0" if replay_pending else ">"  # 注: 决定读取起始位置（0=未确认消息，>=新消息）
    processed = 0
    batches = 0

    while not STOP_EVENT.is_set():  # 注: 主循环
        try:
            response = redis_client.xreadgroup(  # 注: 读取消息
                group_name,
                consumer_name,
                {sync_engine.stream_key: read_id},
                count=batch_size,
                block=block_ms,
            )
        except RedisError as exc:  # pragma: no cover - network failure
            logger.exception("Redis read failed", error=str(exc))  # 注: 记录读取失败
            time.sleep(idle_sleep)
            continue

        if not response:  # 注: 无消息
            read_id = ">"  # 注: 切换到读取新消息模式
            time.sleep(idle_sleep)
            if max_batches is not None:
                batches += 1
                if batches >= max_batches:
                    break
            continue

        for stream_key, events in response:  # 注: 遍历消息流
            for event_id, payload in events:  # 注: 遍历消息
                try:
                    sync_event = SyncEvent.from_stream(payload)  # 注: 反序列化事件
                    targets: Iterable[str] = tuple(t for t in ALL_TARGETS if t != sync_event.origin)  # 注: 确定目标数据库（排除来源）
                    sync_engine.replicate(sync_event, targets)  # 注: 执行复制
                    processed += 1
                    logger.info(  # 注: 记录处理成功
                        "Replicated event",
                        stream=stream_key,
                        event_id=event_id,
                        targets=list(targets),
                    )
                except Exception as exc:  # pragma: no cover - defensive catch
                    logger.exception(  # 注: 记录处理失败
                        "Failed to process sync event",
                        event_id=event_id,
                        error=str(exc),
                    )
                finally:
                    redis_client.xack(stream_key, group_name, event_id)  # 注: 确认消息已处理

        read_id = ">"  # 注: 确保后续读取新消息
        batches += 1
        if max_batches is not None and batches >= max_batches:
            break

    return processed  # 注: 返回处理总数


def run_worker(
    batch_size: int = 100,
    block_ms: int = 5000,
    replay_pending: bool = True,
    idle_sleep: float = 1.0,
) -> None:  # 注: 长期运行的 worker 主循环包装
    for sig in (signal.SIGINT, signal.SIGTERM):  # pragma: no cover - runtime hook
        signal.signal(sig, _handle_shutdown)  # 注: 注册信号处理器

    logger.info(  # 注: 记录启动日志
        "Starting sync worker",
        batch_size=batch_size,
        block_ms=block_ms,
        replay_pending=replay_pending,
    )
    processed = consume_events(  # 注: 开始消费循环
        batch_size=batch_size,
        block_ms=block_ms,
        replay_pending=replay_pending,
        idle_sleep=idle_sleep,
    )
    logger.info("Sync worker stopped", processed_events=processed)  # 注: 记录停止日志


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
    args = _build_parser().parse_args()  # 注: 解析参数
    run_worker(  # 注: 运行 worker
        batch_size=args.batch_size,
        block_ms=args.block_ms,
        replay_pending=not args.no_replay,
        idle_sleep=args.idle_sleep,
    )


if __name__ == "__main__":  # pragma: no cover - CLI bootstrap
    main()
