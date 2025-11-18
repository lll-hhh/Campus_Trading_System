"""Unit tests for sync payload serialization helpers."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal

from apps.core.sync_payloads import decode_params, encode_params


def test_encode_decode_roundtrip() -> None:
    """Encoded parameters should be reversible for common scalar types."""

    original = {
        "amount": Decimal("12.50"),
        "created": datetime(2024, 5, 17, 8, 30, tzinfo=timezone.utc),
        "cutoff": date(2024, 5, 18),
        "reminder": time(9, 45),
        "description": "校园闲置",
        "flag": True,
        "count": 3,
        "payload": {"nested": "json"},
    }

    encoded = encode_params(original)
    assert encoded != original

    decoded = decode_params(encoded)
    assert decoded == original


def test_encode_decode_bytes() -> None:
    """Binary blobs should survive serialization."""

    original = {"blob": b"hello-world"}
    encoded = encode_params(original)
    decoded = decode_params(encoded)
    assert decoded == original
