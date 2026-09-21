"""Media asset model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    String, DateTime, Enum as SAEnum, Integer, Numeric,
    ForeignKey, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(
        SAEnum("image", "video", "annotated_image", "after_image", name="media_kind"),
        nullable=False,
    )
    object_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    public_object_key: Mapped[str] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Numeric, nullable=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
