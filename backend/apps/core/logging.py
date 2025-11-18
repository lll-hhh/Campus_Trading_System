"""Logging helpers using loguru."""
from loguru import logger

logger.add("/tmp/campuswap.log", rotation="1 week", retention="1 month", encoding="utf-8")

__all__ = ["logger"]
