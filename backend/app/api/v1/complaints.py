"""Complaint drafting endpoint — editable drafts from confirmed data only."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ComplaintDraft, ComplaintRequest
from app.services.complaints import draft_complaint

router = APIRouter()


@router.post("/{report_id}/complaint", response_model=ComplaintDraft)
async def create_complaint(
    report_id: UUID,
    payload: ComplaintRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an editable complaint draft (en / hi / mr) for a report."""
    report = (await db.execute(
        select(Report).where(Report.id == report_id)
    )).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if user.id != report.reporter_id and user.role not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Not your report")

    reporter = (await db.execute(
        select(User).where(User.id == report.reporter_id)
    )).scalar_one_or_none()
    draft = draft_complaint(report, reporter.display_name if reporter else None,
                            payload.language)
    return ComplaintDraft(report_id=report.id, language=payload.language, **draft)
