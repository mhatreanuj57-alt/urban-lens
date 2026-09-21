"""Incidents API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_optional_user
from app.database import get_db
from app.models.audit_event import AuditEvent
from app.models.incident import Incident, LIFECYCLE_STATUSES
from app.models.report import Report
from app.models.user import User
from app.schemas.incident import (
    AuditEventResponse,
    IncidentDetail,
    IncidentResponse,
    IncidentStatusUpdate,
)
from app.services.audit import record_audit
from app.services.duplicate import DuplicateService

router = APIRouter()


@router.get("/", response_model=list[IncidentResponse])
async def list_incidents(
    issue_type: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List incidents with optional filters, most urgent first."""
    query = select(Incident).order_by(Incident.priority_score.desc().nullslast())
    if issue_type:
        query = query.where(Incident.primary_issue_type == issue_type)
    if status:
        query = query.where(Incident.lifecycle_status == status)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.get("/{incident_id}", response_model=IncidentDetail)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single incident with its member reports."""
    incident = (await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )).scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    reports = (await db.execute(
        select(Report)
        .where(Report.incident_id == incident_id, Report.status != "rejected")
        .order_by(Report.submitted_at.desc())
    )).scalars().unique().all()
    data = IncidentResponse.model_validate(incident).model_dump(mode="json")
    from app.schemas.report import ReportResponse

    data["reports"] = [
        ReportResponse.model_validate(r).model_dump(mode="json") for r in reports
    ]
    return data


@router.get("/{incident_id}/history", response_model=list[AuditEventResponse])
async def get_incident_history(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Append-only audit history for an incident."""
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.entity_type == "incident",
               AuditEvent.entity_id == incident_id)
        .order_by(AuditEvent.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{incident_id}/status", response_model=IncidentDetail)
async def update_incident_status(
    incident_id: UUID,
    payload: IncidentStatusUpdate,
    moderator: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Status update + audit event (moderator or admin only)."""
    if moderator.role not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Moderator role required")
    if payload.lifecycle_status not in LIFECYCLE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"lifecycle_status must be one of {', '.join(LIFECYCLE_STATUSES)}",
        )
    incident = (await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )).scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    previous = {"lifecycle_status": incident.lifecycle_status}
    incident.lifecycle_status = payload.lifecycle_status
    if payload.lifecycle_status == "resolved":
        from datetime import datetime, timezone

        incident.resolved_at = datetime.now(timezone.utc)
    elif payload.lifecycle_status != "closed":
        incident.resolved_at = None

    await record_audit(
        db,
        actor_id=moderator.id,
        entity_type="incident",
        entity_id=incident.id,
        action=f"incident.status.{payload.lifecycle_status}",
        previous_value=previous,
        new_value={"lifecycle_status": payload.lifecycle_status,
                   "note": payload.note},
    )
    await db.commit()
    await db.refresh(incident)

    reports = (await db.execute(
        select(Report)
        .where(Report.incident_id == incident_id, Report.status != "rejected")
        .order_by(Report.submitted_at.desc())
    )).scalars().unique().all()
    data = IncidentResponse.model_validate(incident).model_dump(mode="json")
    from app.schemas.report import ReportResponse

    data["reports"] = [
        ReportResponse.model_validate(r).model_dump(mode="json") for r in reports
    ]
    return data
