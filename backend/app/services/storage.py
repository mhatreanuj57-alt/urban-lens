"""Storage service — S3-compatible object storage (MinIO / R2 / S3).

Handles bucket bootstrapping, presigned upload URLs for private originals,
and public derivatives with anonymous read access.
"""

import logging
from typing import Optional

import boto3
from botocore.client import BaseClient
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Generate presigned URLs and move objects between buckets."""

    def __init__(self):
        self._client: Optional[BaseClient] = None
        self._buckets_ready = False

    @property
    def client(self) -> BaseClient:
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.public_storage_endpoint,
                aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=settings.STORAGE_SECRET_KEY,
                region_name=settings.STORAGE_REGION,
                config=BotoConfig(
                    signature_version="s3v4",
                    s3={"path_style_access": settings.STORAGE_PATH_STYLE},
                ),
            )
        return self._client

    def _create_bucket(self, bucket: str) -> None:
        """Create a bucket, sending a region only if the gateway demands one."""
        try:
            self.client.create_bucket(Bucket=bucket)
        except ClientError:
            self.client.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": settings.STORAGE_REGION},
            )

    def ensure_buckets(self) -> None:
        """Create the private/public buckets and set the public read policy."""
        if self._buckets_ready:
            return
        for bucket in (settings.STORAGE_BUCKET_PRIVATE, settings.STORAGE_BUCKET_PUBLIC):
            try:
                self.client.head_bucket(Bucket=bucket)
                continue
            except ClientError:
                pass
            try:
                self._create_bucket(bucket)
                logger.info("Created bucket %s", bucket)
            except ClientError as exc:
                # Hosted gateways often refuse creation (Supabase) or require a
                # globally unique name, and a missing bucket surfaces clearly on
                # the next object operation, so don't take the app down for it.
                logger.warning("Could not create bucket %s: %s", bucket, exc)
        public_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{settings.STORAGE_BUCKET_PUBLIC}/*"],
                }
            ],
        }
        try:
            self.client.put_bucket_policy(
                Bucket=settings.STORAGE_BUCKET_PUBLIC,
                Policy=__import__("json").dumps(public_policy),
            )
        except ClientError as exc:
            logger.warning("Could not set public bucket policy: %s", exc)
        self._buckets_ready = True

    def generate_upload_url(
        self,
        object_key: str,
        bucket: str | None = None,
        content_type: str = "application/octet-stream",
        expires_in: int = 900,
    ) -> str:
        """Generate a presigned PUT URL for uploading an original."""
        bucket = bucket or settings.STORAGE_BUCKET_PRIVATE
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": object_key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )

    def generate_download_url(
        self,
        object_key: str,
        bucket: str | None = None,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned GET URL for private objects."""
        bucket = bucket or settings.STORAGE_BUCKET_PRIVATE
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )

    def public_url(self, object_key: str) -> str:
        """Stable anonymous URL for a public derivative."""
        base = settings.STORAGE_PUBLIC_URL_BASE.rstrip("/")
        if base:
            return f"{base}/{object_key}"
        return (
            f"{settings.public_storage_endpoint.rstrip('/')}/"
            f"{settings.STORAGE_BUCKET_PUBLIC}/{object_key}"
        )

    def upload_bytes(self, object_key: str, data: bytes, content_type: str,
                     bucket: str | None = None) -> None:
        self.client.put_object(
            Bucket=bucket or settings.STORAGE_BUCKET_PRIVATE,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )

    def download_bytes(self, object_key: str, bucket: str | None = None) -> bytes:
        response = self.client.get_object(
            Bucket=bucket or settings.STORAGE_BUCKET_PRIVATE, Key=object_key
        )
        return response["Body"].read()

    def object_exists(self, object_key: str, bucket: str | None = None) -> bool:
        try:
            self.client.head_object(
                Bucket=bucket or settings.STORAGE_BUCKET_PRIVATE, Key=object_key
            )
            return True
        except ClientError:
            return False


storage_service = StorageService()
