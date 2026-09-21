"""Pydantic schemas for analytics and risk."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Hotspot(BaseModel):
    latitude: float
    longitude: float
    report_count: int
    top_issue_type: Optional[str] = None
    avg_priority: Optional[float] = None


class SummaryStats(BaseModel):
    total_reports: int = 0
    reports_by_status: dict[str, int] = {}
    reports_by_issue: dict[str, int] = {}
    total_incidents: int = 0
    open_incidents: int = 0
    resolved_incidents: int = 0


class RiskCell(BaseModel):
    grid_cell: str
    latitude: float
    longitude: float
    risk_level: str
    risk_score: float
    rainfall_mm_24h: float
    verified_waterlogging_30d: int
    updated_at: Optional[datetime] = None
