"""Pydantic schemas for incidents."""

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.schemas.report import IssueType, ReportResponse


class IncidentBase(BaseModel):
    primary_issue_type: IssueType


class IncidentResponse(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lifecycle_status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ward_id: Optional[UUID] = None
    severity_score: Optional[float] = None
    priority_score: Optional[float] = None
    priority_factors: Optional[dict] = None
    report_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: Optional[datetime] = None


class IncidentDetail(IncidentResponse):
    reports: list[ReportResponse] = []


class IncidentStatusUpdate(BaseModel):
    lifecycle_status: str = Field(
        ..., description="One of open, assigned, in_progress, resolved, closed"
    )
    note: Optional[str] = Field(None, max_length=1000)


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: Optional[UUID] = None
    entity_type: str
    entity_id: UUID
    action: str
    previous_value: Optional[dict] = None
    new_value: Optional[dict] = None
    created_at: datetime
