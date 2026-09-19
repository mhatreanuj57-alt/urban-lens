"""Application configuration via Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "UrbanLens AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://urban:urban@localhost:5432/urbanlens"
    DATABASE_URL_SYNC: str = "postgresql://urban:urban@localhost:5432/urbanlens"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Storage
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET_PRIVATE: str = "urbanlens-private"
    STORAGE_BUCKET_PUBLIC: str = "urbanlens-public"
    STORAGE_REGION: str = "ap-south-1"

    # ML
    ML_MODEL_PATH: str = "../ml/models"
    ML_DEVICE: str = "cpu"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Sentry
    SENTRY_DSN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
