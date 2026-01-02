"""Configuration module for CampuSwap backend."""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application runtime settings."""

    app_name: str = "Phoenix Auto Parts"
    environment: str = Field("local", alias="PHOENIX_ENV")
    api_v1_prefix: str = "/api/v1"
    debug: bool = Field(default=True)

    mysql_dsn: str = Field(..., alias="MYSQL_DSN")
    redis_url: str = Field(..., alias="REDIS_URL")
    jwt_secret_key: str = Field("campuswap-secret", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    cors_origins: List[AnyHttpUrl] = []

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    alert_sender: str | None = Field(default=None, alias="ALERT_SENDER")
    alert_recipients: List[str] = Field(default_factory=list, alias="ALERT_RECIPIENTS")

    # GLM AI 配置
    glm_api_key: str | None = Field(default=None, alias="GLM_API_KEY")
    glm_api_base: str = Field(default="https://open.bigmodel.cn/api/paas/v4", alias="GLM_API_BASE")
    glm_model: str = Field(default="glm-4-flash", alias="GLM_MODEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
