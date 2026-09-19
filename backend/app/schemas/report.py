"""Pydantic schemas for reports."""

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class ReportBase(BaseModel):
    issue_type: Optional[str] = None
    description: Optional[str] = None


class ReportCreate(ReportBase):
    pass


class ReportResponse(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reporter_id: UUID
    incident_id: Optional[UUID] = None
    status: str
    submitted_at: datetime
    priority_score: Optional[float] = None
    verification_state: str


class ReportDetail(ReportResponse):
    """Extended report response with media and inference results."""
    media_assets: list = []
    inference_runs: list = []
