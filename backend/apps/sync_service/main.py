"""Sync service entrypoint."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from apps.core.sync_engine import sync_engine

from .router import router


scheduler = AsyncIOScheduler()


def create_app() -> FastAPI:
    """Create sync service app."""

    app = FastAPI(title="CampuSwap Sync Service", version="0.1.0")
    app.include_router(router)

    @app.on_event("startup")
    async def on_startup() -> None:  # pragma: no cover - runtime hook
        scheduler.add_job(
            sync_engine.run_periodic_sync,
            trigger="interval",
            minutes=5,
            id="sync-periodic",
            replace_existing=True,
        )
        scheduler.start()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:  # pragma: no cover - runtime hook
        if scheduler.running:
            scheduler.shutdown(wait=False)

    return app


app = create_app()
