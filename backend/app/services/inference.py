"""Inference orchestration — dispatches pipeline work to Celery or the app loop."""

import asyncio
import logging
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)


def _run_inline(media_asset_id: UUID) -> str:
    """Run the pipeline on the caller's event loop.

    The shared async engine owns one connection pool bound to a single event
    loop, so we must not execute pipeline DB work on a fresh thread+loop
    (that corrupts pooled asyncpg connections). Scheduling a task on the
    running loop keeps all DB access on the loop that owns the pool.
    """
    from app.services.pipeline import run_media_pipeline

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        task = loop.create_task(run_media_pipeline(media_asset_id))

        def _done(t: asyncio.Task) -> None:
            exc = t.exception()
            if exc is not None:
                logger.error("Inline pipeline failed for asset %s: %s", media_asset_id, exc)

        task.add_done_callback(_done)
        return f"inline:{media_asset_id}"

    # No running loop (e.g. seeding / CLI): run to completion on a throwaway loop.
    asyncio.run(run_media_pipeline(media_asset_id))
    return f"inline-sync:{media_asset_id}"


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
    return _run_inline(media_asset_id)

