"""Inference Celery tasks.

These tasks run in a separate worker process.
"""

import logging
from uuid import UUID

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.inference_task.run_detection", bind=True)
def run_detection(
    self,
    media_asset_id: str,
    object_key: str,
    model_name: str = "yolov8-urbanlens",
):
    """Run YOLO detection on a media asset.

    Steps:
    1. Download object from storage.
    2. Run YOLO detector.
    3. Store results in inference_runs.
    4. Optionally enqueue blur task.
    """
    logger.info(f"Running detection for asset {media_asset_id}")
    # Placeholder — actual inference in ml/inference/detector.py
    return {
        "status": "completed",
        "media_asset_id": media_asset_id,
        "detections": [],
    }


@celery_app.task(name="workers.inference_task.run_blur", bind=True)
def run_blur(
    self,
    media_asset_id: str,
    object_key: str,
):
    """Blur faces and number plates in an image."""
    logger.info(f"Running blur for asset {media_asset_id}")
    return {"status": "completed", "media_asset_id": media_asset_id}
