"""Application configuration via Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings
from typing import List

# Repo root: backend/app/config.py -> parents[2] == backend, parents[3] == repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    APP_NAME: str = "UrbanLens AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://urban:urban@localhost:15432/urbanlens"
    DATABASE_URL_SYNC: str = "postgresql://urban:urban@localhost:15432/urbanlens"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Task queue mode: "celery" (compose/production) or "inline" (single-process dev)
    TASK_QUEUE_MODE: str = "inline"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Supabase (auth + database)
    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""   # client-safe key (formerly "anon")
    SUPABASE_SECRET_KEY: str = ""        # server-only (formerly "service_role")

    # Password applied to demo accounts created by `python -m app.seed`.
    SEED_DEMO_PASSWORD: str = ""

    # Storage
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    # Endpoint used inside presigned URLs handed to browsers (differs in Docker)
    STORAGE_PUBLIC_ENDPOINT: str = ""
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET_PRIVATE: str = "urbanlens-private"
    STORAGE_BUCKET_PUBLIC: str = "urbanlens-public"
    STORAGE_REGION: str = "ap-south-1"
    # Anonymous-read prefix for public derivatives. Leave blank for MinIO/R2,
    # where the object URL is "{endpoint}/{bucket}/{key}"; Supabase instead
    # serves public objects at "https://<ref>.supabase.co/storage/v1/object/public".
    STORAGE_PUBLIC_URL_BASE: str = ""
    # Supabase's S3 gateway only routes virtual-host-style bucket requests.
    STORAGE_PATH_STYLE: bool = True

    # ML
    ML_MODEL_PATH: str = str(_REPO_ROOT / "ml" / "models")
    ML_DEVICE: str = "cpu"

    # Demo content boundaries (Navi Mumbai bounding box)
    NM_BBOX: List[float] = [72.85, 18.85, 73.10, 19.20]

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Sentry
    SENTRY_DSN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def public_storage_endpoint(self) -> str:
        return self.STORAGE_PUBLIC_ENDPOINT or self.STORAGE_ENDPOINT


settings = Settings()
