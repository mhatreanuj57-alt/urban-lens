"""Inference orchestration — dispatches pipeline work to Celery or inline threads."""

import logging
import threading
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)


def _run_inline(media_asset_id: UUID) -> None:
    """Execute the pipeline in a daemon thread with its own event loop."""
    from app.services.pipeline import run_media_pipeline

    def _worker():
        try:
            asyncio_run = __import__("asyncio").run
            asyncio_run(run_media_pipeline(media_asset_id))
        except Exception:
            logger.exception("Inline pipeline failed for asset %s", media_asset_id)

    threading.Thread(target=_worker, name="urbanlens-pipeline", daemon=True).start()


def dispatch_pipeline(media_asset_id: UUID) -> str:
    """Send the media pipeline to the configured queue backend."""
    if settings.TASK_QUEUE_MODE == "celery":
        from app.workers.celery_app import celery_app

        task = celery_app.send_task(
            "workers.inference_task.run_detection",
            args=[str(media_asset_id), "", "yolov8-urbanlens"],
        )
        logger.info("Enqueued pipeline task %s for asset %s", task.id, media_asset_id)
        return task.id
    _run_inline(media_asset_id)
    return f"inline:{media_asset_id}"
