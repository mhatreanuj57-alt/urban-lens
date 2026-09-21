"""Inference Celery tasks.

These tasks run in a separate worker process (TASK_QUEUE_MODE=celery).
"""

import logging
from uuid import UUID

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.inference_task.run_detection", bind=True,
                 max_retries=2, default_retry_delay=10)
def run_detection(self, media_asset_id: str, object_key: str,
                  model_name: str = "yolov8-urbanlens"):
    """Run the full media pipeline (detect, embed, blur, cluster) for an asset."""
    from app.services.pipeline import run_pipeline_sync

    logger.info("Running pipeline for asset %s", media_asset_id)
    try:
        return run_pipeline_sync(UUID(media_asset_id))
    except Exception as exc:  # pragma: no cover
        logger.exception("Pipeline failed for asset %s", media_asset_id)
        raise self.retry(exc=exc)


@celery_app.task(name="workers.inference_task.run_blur", bind=True)
def run_blur(self, media_asset_id: str, object_key: str):
    """Backwards-compatible alias — blur is part of the full pipeline."""
    return run_detection(media_asset_id, object_key)
