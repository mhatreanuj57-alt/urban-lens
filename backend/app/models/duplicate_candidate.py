"""Duplicate candidate model — near-duplicate report pairs."""

import uuid
from datetime import datetime

from sqlalchemy import Numeric, DateTime, Enum as SAEnum, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DuplicateCandidate(Base):
    __tablename__ = "duplicate_candidates"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), primary_key=True
    )
    candidate_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), primary_key=True
    )
    geo_distance_m: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    image_similarity: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    time_distance_hours: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    decision: Mapped[str] = mapped_column(
        SAEnum("pending", "merged", "not_duplicate", name="duplicate_decision"),
        nullable=False,
        default="pending",
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
