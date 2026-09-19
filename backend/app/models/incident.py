"""Incident model — clustered operational issue."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum as SAEnum, Numeric, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    primary_issue_type: Mapped[str] = mapped_column(
        SAEnum(
            "pothole", "garbage", "damaged_streetlight",
            "waterlogging", "illegal_dumping",
            name="issue_type",
        ),
        nullable=False,
    )
    lifecycle_status: Mapped[str] = mapped_column(
        SAEnum(
            "open", "assigned", "in_progress", "resolved", "closed",
            name="lifecycle_status",
        ),
        nullable=False,
        default="open",
    )
    severity_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    priority_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
