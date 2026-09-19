"""Upload endpoints — signed URL generation."""

import uuid
import time
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings

router = APIRouter()


@router.post("/sign")
async def sign_upload(
    filename: str,
    content_type: str = "image/jpeg",
):
    """Generate a signed upload URL for object storage.

    In production, this calls S3/MinIO presigned URL generation.
    For now returns a placeholder that the frontend fills in.
    """
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    object_key = f"uploads/{uuid.uuid4()}.{ext}"

    return {
        "object_key": object_key,
        "upload_url": f"{settings.STORAGE_ENDPOINT}/{settings.STORAGE_BUCKET_PRIVATE}/{object_key}",
        "expires_in": 3600,
        "method": "PUT",
    }


@router.get("/health")
async def upload_health():
    return {"status": "ok"}
