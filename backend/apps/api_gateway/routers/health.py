"""Health and readiness endpoints."""
from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness_probe() -> dict[str, str]:
    """Return a simple liveness payload."""

    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
def readiness_probe() -> dict[str, str]:
    """Return readiness status placeholder."""

    return {"status": "initializing", "timestamp": datetime.utcnow().isoformat()}
