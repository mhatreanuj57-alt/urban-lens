"""Ward model — administrative boundary for Navi Mumbai zones."""

import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Ward(Base):
    __tablename__ = "wards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    boundary = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True
    )
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
