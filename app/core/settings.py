"""Typed application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="InsightFlow AI", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    max_upload_mb: int = Field(default=200, alias="MAX_UPLOAD_MB", ge=1, le=2048)
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash-lite", alias="INSIGHTFLOW_GEMINI_MODEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings; tests may clear the cache with cache_clear()."""
    return Settings()


settings = get_settings()
