"""Background sync worker consuming Redis streams."""
from __future__ import annotations

import argparse
import os
import signal
import socket
import time
from threading import Event
from typing import Iterable

from loguru import logger
from redis.exceptions import RedisError, ResponseError

from apps.core.sync_engine import SyncEvent, sync_engine


ALL_TARGETS: tuple[str, ...] = ("mysql", "mariadb", "postgres", "sqlite")
STOP_EVENT = Event()


def _ensure_consumer_group(group_name: str) -> None:
    """Create Redis consumer group if it does not exist."""

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
    """Signal handler that stops the worker loop gracefully."""

    logger.warning("Sync worker received shutdown signal", signal=signum)
    STOP_EVENT.set()


def consume_events(
    batch_size: int = 100,
    block_ms: int = 5000,
    replay_pending: bool = True,
    idle_sleep: float = 1.0,
    max_batches: int | None = None,
) -> int:
    """Poll the Redis stream and fan out events to configured databases."""

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
                    redis_client.xack(stream_key, group_name, event_id)

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
) -> None:
    """Run the sync worker until interrupted."""

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


def _build_parser() -> argparse.ArgumentParser:
    """Create CLI parser for launching the worker."""

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
    """Console entry point for the sync worker."""

    args = _build_parser().parse_args()
    run_worker(
        batch_size=args.batch_size,
        block_ms=args.block_ms,
        replay_pending=not args.no_replay,
        idle_sleep=args.idle_sleep,
    )


if __name__ == "__main__":  # pragma: no cover - CLI bootstrap
    main()
