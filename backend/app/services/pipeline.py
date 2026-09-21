"""Media processing pipeline — runs after a report is submitted.

Steps (per architecture doc):
1. Validate file and extract metadata (sha256, dimensions, EXIF capture time).
2. Blur faces for the public derivative; strip EXIF.
3. Run the detector, derive severity, create an image embedding.
4. Find duplicate candidates and update the incident.
5. Persist immutable inference output with exact model version.

Heavy ML deps (ultralytics, transformers, opencv) are optional: when absent,
the pipeline degrades gracefully and marks the media "needs review".
"""

import asyncio
import hashlib
import io
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import numpy as np
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.media_asset import MediaAsset
from app.models.inference_run import InferenceRun
from app.models.report import Report
from app.services import storage as storage_svc
from app.services.duplicate import DuplicateService
from app.services.priority import base_severity, compute_priority

logger = logging.getLogger(__name__)

try:  # Optional OpenCV — used for face blurring in public derivatives
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

MAX_PUBLIC_DIM = 1600


# ---------------------------------------------------------------------------
# Optional ML backends (lazy, cached)
# ---------------------------------------------------------------------------

_detector_cache = {}


def _load_yolo():
    """Load the fine-tuned YOLO model when weights + ultralytics are available."""
    if "yolo" in _detector_cache:
        return _detector_cache["yolo"]
    yolo = None
    try:
        from ultralytics import YOLO

        model_dir = Path(settings.ML_MODEL_PATH)
        weights = sorted(model_dir.glob("*.pt"))
        if weights:
            yolo = YOLO(str(weights[0]))
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.info("YOLO unavailable, detection skipped: %s", exc)
    _detector_cache["yolo"] = yolo
    return yolo


def _perceptual_embedding(img: Image.Image) -> list[float]:
    """64-dim average-hash embedding — offline fallback when CLIP is unavailable."""
    small = ImageOps.grayscale(img.resize((8, 8), Image.LANCZOS))
    arr = np.asarray(small, dtype=np.float32)
    bits = (arr > arr.mean()).astype(np.float32)
    return (bits * 2.0 - 1.0).tolist()


def _clip_embedding(img: Image.Image) -> list[float] | None:
    """CLIP image embedding when transformers is installed; None otherwise."""
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor

        if "clip" not in _detector_cache:
            _detector_cache["clip_model"] = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
            _detector_cache["clip_proc"] = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
        model = _detector_cache["clip_model"]
        proc = _detector_cache["clip_proc"]
        inputs = proc(images=img, return_tensors="pt")
        with torch.no_grad():
            feats = model.get_image_features(**inputs)
        emb = feats.cpu().numpy().flatten()
        return (emb / np.linalg.norm(emb)).tolist()
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.info("CLIP unavailable, using perceptual-hash embedding: %s", exc)
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    arr_a, arr_b = np.array(a), np.array(b)
    denom = np.linalg.norm(arr_a) * np.linalg.norm(arr_b)
    return float(np.dot(arr_a, arr_b) / denom) if denom else 0.0


def _blur_faces(img: Image.Image) -> tuple[Image.Image, int]:
    """Blur detected faces using OpenCV Haar cascades when available."""
    if cv2 is None or not hasattr(cv2, "CascadeClassifier"):
        return img, 0
    arr = np.array(img.convert("RGB"))
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(str(cascade_path))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(40, 40))
    for (x, y, w, h) in faces:
        pad = int(0.25 * max(w, h))
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(arr.shape[1], x + w + pad), min(arr.shape[0], y + h + pad)
        region = arr[y0:y1, x0:x1]
        if region.size:
            arr[y0:y1, x0:x1] = cv2.GaussianBlur(region, (51, 51), 30)
    return Image.fromarray(arr), len(faces)


def _strip_metadata_and_resize(img: Image.Image) -> Image.Image:
    """Remove EXIF/GPS metadata and cap the public derivative size."""
    img = ImageOps.exif_transpose(img)
    img.thumbnail((MAX_PUBLIC_DIM, MAX_PUBLIC_DIM), Image.LANCZOS)
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    return clean


def _extract_capture_time(img: Image.Image) -> datetime | None:
    try:
        exif = img.getexif()
        raw = exif.get(36867) or exif.get(306)  # DateTimeOriginal / DateTime
        if raw:
            return datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


async def run_media_pipeline(media_asset_id: UUID) -> dict:
    """Full processing for one media asset. Safe to call inline or from Celery."""
    started = time.perf_counter()
    async with async_session() as db:
        result = await db.execute(
            select(MediaAsset).where(MediaAsset.id == media_asset_id)
        )
        asset = result.scalar_one_or_none()
        if asset is None:
            logger.error("Pipeline: media asset %s not found", media_asset_id)
            return {"status": "error", "detail": "media asset not found"}

        report = (await db.execute(
            select(Report).where(Report.id == asset.report_id)
        )).scalar_one_or_none()
        if report is None:
            return {"status": "error", "detail": "report not found"}

        summary: dict = {"status": "completed", "detections": [], "faces_blurred": 0}

        try:
            original = storage_svc.storage_service.download_bytes(asset.object_key)
        except Exception as exc:
            logger.error("Pipeline: download failed for %s: %s", asset.object_key, exc)
            summary["status"] = "error"
            summary["detail"] = f"storage download failed: {exc}"
            return summary

        sha256 = hashlib.sha256(original).hexdigest()

        # --- metadata extraction ------------------------------------------
        captured_at = None
        if asset.kind == "image":
            img = Image.open(io.BytesIO(original))
            img = ImageOps.exif_transpose(img)
            width, height = img.size
            captured_at = _extract_capture_time(Image.open(io.BytesIO(original)))
            summary.update({"width": width, "height": height})

            # --- public derivative (EXIF stripped, resized, faces blurred) --
            clean = _strip_metadata_and_resize(img)
            blurred, face_count = _blur_faces(clean)
            summary["faces_blurred"] = face_count
            buffer = io.BytesIO()
            blurred.save(buffer, format="JPEG", quality=85)
            public_key = f"public/{asset.id}.jpg"
            try:
                storage_svc.storage_service.upload_bytes(
                    public_key, buffer.getvalue(), "image/jpeg",
                    bucket=settings.STORAGE_BUCKET_PUBLIC,
                )
                asset.public_object_key = public_key
            except Exception as exc:
                logger.error("Pipeline: public upload failed: %s", exc)

            # --- detection ---------------------------------------------------
            yolo = _load_yolo()
            if yolo is not None:
                t0 = time.perf_counter()
                try:
                    raw = yolo(np.array(clean), device=settings.ML_DEVICE, conf=0.25)
                    detections = []
                    for res in raw:
                        boxes = getattr(res, "boxes", None)
                        if boxes is None:
                            continue
                        for box in boxes:
                            detections.append({
                                "bbox": [round(v, 1) for v in box.xyxy[0].tolist()],
                                "class_name": res.names[int(box.cls[0])],
                                "confidence": round(float(box.conf[0]), 3),
                            })
                    db.add(InferenceRun(
                        media_asset_id=asset.id, task="detection",
                        model_name="yolov8-urbanlens", model_version="v1",
                        result={"detections": detections, "needs_review": len(detections) == 0},
                        latency_ms=int((time.perf_counter() - t0) * 1000),
                    ))
                    summary["detections"] = detections
                except Exception as exc:
                    logger.error("Pipeline: detection failed: %s", exc)
            else:
                db.add(InferenceRun(
                    media_asset_id=asset.id, task="detection",
                    model_name="yolov8-urbanlens", model_version="v1",
                    result={"detections": [], "needs_review": True,
                            "status": "model_weights_not_available"},
                ))

            # --- embedding ---------------------------------------------------
            t0 = time.perf_counter()
            clip_emb = _clip_embedding(clean)
            if clip_emb is not None:
                emb, backend = clip_emb, "clip-vit-base-patch32"
            else:
                emb, backend = _perceptual_embedding(clean), "average-hash-v1"
            db.add(InferenceRun(
                media_asset_id=asset.id, task="embedding",
                model_name=backend, model_version="v1",
                result={"embedding": emb, "dim": len(emb)},
                latency_ms=int((time.perf_counter() - t0) * 1000),
            ))
            summary["embedding_backend"] = backend

            # --- blur inference record ---------------------------------------
            db.add(InferenceRun(
                media_asset_id=asset.id, task="blur",
                model_name="haar-cascade-frontend" if cv2 else "exif-strip-only",
                model_version="v1",
                result={"faces_blurred": face_count},
            ))

        asset.sha256 = sha256
        asset.captured_at = captured_at or asset.captured_at
        if summary.get("width"):
            asset.width = summary["width"]
            asset.height = summary["height"]
        if captured_at and report.occurred_at is None:
            report.occurred_at = captured_at

        # --- severity + duplicate clustering + priority ---------------------
        detections = summary.get("detections") or []
        max_conf = max((d["confidence"] for d in detections), default=None)
        severity = base_severity(report.issue_type or "garbage", max_conf)
        report.severity_score = severity

        candidates = await DuplicateService.find_candidates(db, report)
        await DuplicateService.record_candidates(db, report, candidates)
        incident = await DuplicateService.cluster_report(db, report, candidates)

        score, factors = compute_priority(
            issue_type=report.issue_type or "garbage",
            severity=severity,
            report_count=incident.report_count,
            submitted_at=report.submitted_at,
        )
        report.priority_score = score
        report.priority_factors = factors

        if report.status == "submitted":
            report.status = "under_review"

        await db.commit()
        summary["latency_ms"] = int((time.perf_counter() - started) * 1000)
        summary["incident_id"] = str(incident.id)
        summary["duplicates_found"] = len(candidates)
        logger.info("Pipeline completed for asset %s: %s", media_asset_id, summary)
        return summary


def run_pipeline_sync(media_asset_id: UUID) -> dict:
    """Synchronous entry point for Celery workers."""
    return asyncio.run(run_media_pipeline(media_asset_id))
