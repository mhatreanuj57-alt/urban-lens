"""Upload endpoints — presigned URL generation for private originals."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.storage import storage_service

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
}

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("/sign")
async def sign_upload(
    filename: str,
    content_type: str = "image/jpeg",
    size_bytes: int | None = None,
    user: User = Depends(get_current_user),
):
    """Generate a presigned PUT URL for uploading media to private storage."""
    ext = ALLOWED_CONTENT_TYPES.get(content_type)
    if ext is None:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )
    if size_bytes is not None and size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 25 MB limit")

    storage_service.ensure_buckets()
    object_key = f"originals/{user.id}/{uuid.uuid4()}.{ext}"
    upload_url = storage_service.generate_upload_url(
        object_key, content_type=content_type
    )
    return {
        "object_key": object_key,
        "upload_url": upload_url,
        "method": "PUT",
        "expires_in": 900,
        "headers": {"Content-Type": content_type},
    }
