"""Inference service — orchestrates ML pipeline."""

from uuid import UUID
from typing import Optional
import logging

from app.models.media_asset import MediaAsset
from app.models.inference_run import InferenceRun
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class InferenceService:
    """Triggers inference pipeline via Celery workers."""

    @staticmethod
    async def enqueue_detection(
        media_asset_id: UUID,
        object_key: str,
        model_name: str = "yolov8-urbanlens",
    ) -> str:
        """Enqueue a detection task for a media asset."""
        task = celery_app.send_task(
            "workers.inference_task.run_detection",
            args=[str(media_asset_id), object_key, model_name],
        )
        logger.info(f"Enqueued detection task {task.id} for asset {media_asset_id}")
        return task.id

    @staticmethod
    async def enqueue_blur(
        media_asset_id: UUID,
        object_key: str,
    ) -> str:
        """Enqueue a face/plate blurring task."""
        task = celery_app.send_task(
            "workers.inference_task.run_blur",
            args=[str(media_asset_id), object_key],
        )
        logger.info(f"Enqueued blur task {task.id} for asset {media_asset_id}")
        return task.id


inference_service = InferenceService()
