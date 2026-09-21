"""Report model — a citizen submission."""

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    String, Text, DateTime, Enum as SAEnum, Numeric, Float,
    ForeignKey, Integer, Index, Boolean, text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

ISSUE_TYPES = ("pothole", "garbage", "damaged_streetlight", "waterlogging", "illegal_dumping")
REPORT_STATUSES = (
    "submitted", "under_review", "verified",
    "assigned", "in_progress", "resolved", "rejected",
)
LOCATION_SOURCES = ("exif", "manual_pin", "landmark", "unknown")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True
    )
    issue_type: Mapped[str | None] = mapped_column(
        SAEnum(*ISSUE_TYPES, name="issue_type"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(*REPORT_STATUSES, name="report_status"),
        nullable=False,
        default="submitted",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    landmark: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Exact location (kept private) and reduced-precision public copy
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    public_location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    public_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    public_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_source: Mapped[str] = mapped_column(
        SAEnum(*LOCATION_SOURCES, name="location_source"),
        nullable=False,
        default="unknown",
    )

    consent_location: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_training: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    priority_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    priority_factors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    severity_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    verification_state: Mapped[str] = mapped_column(
        SAEnum("unreviewed", "verified", "rejected", name="verification_state"),
        nullable=False,
        default="unreviewed",
    )

    media_assets_rel: Mapped[list["MediaAsset"]] = relationship(
        "MediaAsset", foreign_keys="MediaAsset.report_id", lazy="selectin"
    )
    inference_runs_rel: Mapped[list["InferenceRun"]] = relationship(
        "InferenceRun",
        secondary="media_assets",
        primaryjoin="Report.id==MediaAsset.report_id",
        secondaryjoin="MediaAsset.id==InferenceRun.media_asset_id",
        viewonly=True,
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_reports_issue_status_submitted", "issue_type", "status", "submitted_at"),
        Index("ix_reports_location_gist", "location", postgresql_using="gist"),
        Index("ix_reports_reporter", "reporter_id"),
        Index("ix_reports_incident", "incident_id"),
    )
