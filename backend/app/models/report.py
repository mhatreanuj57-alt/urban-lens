"""Report model — a citizen submission."""

import uuid
from datetime import datetime

from sqlalchemy import (
    String, Text, DateTime, Enum as SAEnum, Numeric,
    ForeignKey, Integer, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True
    )
    issue_type: Mapped[str] = mapped_column(
        SAEnum(
            "pothole", "garbage", "damaged_streetlight",
            "waterlogging", "illegal_dumping",
            name="issue_type",
        ),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(
            "submitted", "under_review", "verified",
            "assigned", "in_progress", "resolved", "rejected",
            name="report_status",
        ),
        nullable=False,
        default="submitted",
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # location / public_location / location_source would be added via PostGIS
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    priority_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    verification_state: Mapped[str] = mapped_column(
        SAEnum("unreviewed", "verified", "rejected", name="verification_state"),
        nullable=False,
        default="unreviewed",
    )
