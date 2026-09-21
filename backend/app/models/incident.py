"""Incident model — clustered operational issue."""

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    DateTime, Enum as SAEnum, Numeric, Integer, Float,
    ForeignKey, text, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.report import ISSUE_TYPES

LIFECYCLE_STATUSES = ("open", "assigned", "in_progress", "resolved", "closed")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    primary_issue_type: Mapped[str] = mapped_column(
        SAEnum(*ISSUE_TYPES, name="issue_type"),
        nullable=False,
    )
    centroid = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    ward_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wards.id"), nullable=True
    )
    lifecycle_status: Mapped[str] = mapped_column(
        SAEnum(*LIFECYCLE_STATUSES, name="lifecycle_status"),
        nullable=False,
        default="open",
    )
    severity_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    priority_factors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    report_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_incidents_centroid_gist", "centroid", postgresql_using="gist"),
        Index("ix_incidents_lifecycle", "lifecycle_status"),
        Index("ix_incidents_priority", "priority_score"),
    )
