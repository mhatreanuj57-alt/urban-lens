"""Weather observations and flood-risk predictions."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum as SAEnum, Numeric, Integer, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    grid_cell: Mapped[str] = mapped_column(String(50), nullable=False)
    rainfall_mm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    tide_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")

    __table_args__ = (
        Index("ix_weather_cell_time", "grid_cell", "observed_at"),
    )


class FloodRiskPrediction(Base):
    __tablename__ = "flood_risk_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prediction_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    grid_cell: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(
        SAEnum("low", "medium", "high", name="risk_level"),
        nullable=False,
        default="low",
    )
    risk_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False, default="rules-v0")
    feature_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_risk_cell_for", "grid_cell", "prediction_for"),
    )
