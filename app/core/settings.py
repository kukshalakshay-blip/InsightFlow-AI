"""Application settings (placeholder) for InsightFlow-AI."""
from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "InsightFlow-AI"
    DEBUG: bool = True


settings = Settings()
