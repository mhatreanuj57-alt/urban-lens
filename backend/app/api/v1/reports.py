"""Reports API endpoints."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse, ReportDetail

router = APIRouter()


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    issue_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List reports with optional filters."""
    query = select(Report).limit(limit).offset(offset)
    if issue_type:
        query = query.where(Report.issue_type == issue_type)
    if status:
        query = query.where(Report.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(payload: ReportCreate, db: AsyncSession = Depends(get_db)):
    """Submit a new report."""
    report = Report(**payload.model_dump(exclude_unset=True))
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single report by ID."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{report_id}/verify", response_model=ReportResponse)
async def verify_report(
    report_id: UUID,
    state: str = Query(..., regex="^(verified|rejected)$"),
    db: AsyncSession = Depends(get_db),
):
    """Moderator verification of a report."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.verification_state = state
    await db.commit()
    await db.refresh(report)
    return report
