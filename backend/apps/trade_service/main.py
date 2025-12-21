"""Trade service entrypoint."""
from fastapi import FastAPI

from .router import router


def create_app() -> FastAPI:
    """Create trade service app."""

    app = FastAPI(title="CampuSwap Trade Service", version="0.1.0")
    app.include_router(router)
    return app


app = create_app()
