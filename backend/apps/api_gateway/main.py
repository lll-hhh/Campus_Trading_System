"""FastAPI entrypoint for the API Gateway."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api_gateway.routers import auth, dashboard, database, health, market, sync
from apps.core.config import get_settings
from apps.services.db_initializer import initialize_databases

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the API gateway instance."""

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.cors_origins],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(sync.router, prefix=settings.api_v1_prefix)
    app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
    app.include_router(market.router, prefix=settings.api_v1_prefix)
    app.include_router(database.router, prefix=settings.api_v1_prefix)

    @app.on_event("startup")
    async def startup_event():
        """应用启动时初始化数据库对象（触发器、存储过程等）"""
        logger.info("应用启动中...开始初始化数据库对象")
        try:
            results = initialize_databases()
            for db_name, result in results.items():
                logger.info(
                    f"{db_name}: 执行 {result['executed']} 条成功, "
                    f"{result['failed']} 条失败"
                )
                if result['errors']:
                    for error in result['errors'][:3]:  # 只显示前3个错误
                        logger.warning(f"{db_name} 错误: {error}")
        except Exception as e:
            logger.error(f"数据库初始化异常: {e}", exc_info=True)
            # 不阻断应用启动，允许运行时手动初始化

    @app.get("/", tags=["root"])
    def read_root() -> dict[str, str]:
        return {"message": "CampuSwap API Gateway"}

    return app


app = create_app()
