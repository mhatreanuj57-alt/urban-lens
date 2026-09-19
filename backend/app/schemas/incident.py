"""Pydantic schemas for incidents."""

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class IncidentBase(BaseModel):
    primary_issue_type: str


class IncidentCreate(IncidentBase):
    pass


class IncidentResponse(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lifecycle_status: str
    severity_score: Optional[float] = None
    priority_score: Optional[float] = None
    report_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: Optional[datetime] = None


class IncidentUpdate(BaseModel):
    lifecycle_status: Optional[str] = None
    severity_score: Optional[float] = None
