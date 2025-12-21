"""Utilities for serializing sync payload parameters."""
from __future__ import annotations

import base64
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict

_ENCODED_FLAG = "__type__"


def encode_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert SQL parameter dictionary into JSON-serializable values."""

    return {key: _encode_value(value) for key, value in params.items()}


def decode_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Restore SQL parameters from their serialized forms."""

    return {key: _decode_value(value) for key, value in params.items()}


def _encode_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return {_ENCODED_FLAG: "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {_ENCODED_FLAG: "date", "value": value.isoformat()}
    if isinstance(value, time):
        return {_ENCODED_FLAG: "time", "value": value.isoformat()}
    if isinstance(value, Decimal):
        return {_ENCODED_FLAG: "decimal", "value": str(value)}
    if isinstance(value, bytes):
        encoded = base64.b64encode(value).decode("utf-8")
        return {_ENCODED_FLAG: "bytes", "value": encoded}
    return value


def _decode_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value

    value_type = value.get(_ENCODED_FLAG)
    payload = value.get("value")
    if value_type == "datetime" and isinstance(payload, str):
        return datetime.fromisoformat(payload)
    if value_type == "date" and isinstance(payload, str):
        return date.fromisoformat(payload)
    if value_type == "time" and isinstance(payload, str):
        return time.fromisoformat(payload)
    if value_type == "decimal" and isinstance(payload, str):
        return Decimal(payload)
    if value_type == "bytes" and isinstance(payload, str):
        return base64.b64decode(payload.encode("utf-8"))
    return value
