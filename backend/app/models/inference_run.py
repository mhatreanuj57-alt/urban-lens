"""Inference run model — immutable model execution history."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum as SAEnum, Integer, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InferenceRun(Base):
    __tablename__ = "inference_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    media_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    task: Mapped[str] = mapped_column(
        SAEnum("detection", "embedding", "blur", "risk", name="inference_task"),
        nullable=False,
    )
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
