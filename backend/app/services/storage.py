"""Storage service — signed URL generation for object storage."""

import logging
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Generate presigned URLs for media uploads/downloads."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.STORAGE_ENDPOINT,
                aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=settings.STORAGE_SECRET_KEY,
                region_name=settings.STORAGE_REGION,
                config=BotoConfig(signature_version="s3v4"),
            )
        return self._client

    def generate_upload_url(
        self,
        object_key: str,
        bucket: str,
        content_type: str = "application/octet-stream",
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned PUT URL for uploading."""
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

    def generate_download_url(
        self,
        object_key: str,
        bucket: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned GET URL for downloading."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )


storage_service = StorageService()
