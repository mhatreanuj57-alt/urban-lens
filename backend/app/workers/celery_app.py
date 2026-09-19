"""Celery application instance."""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "urbanlens",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.inference_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes hard limit
    worker_prefetch_multiplier=1,
)
