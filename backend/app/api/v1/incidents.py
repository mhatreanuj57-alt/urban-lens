"""Incidents API endpoints."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.incident import Incident
from app.schemas.incident import IncidentResponse, IncidentUpdate

router = APIRouter()


@router.get("/", response_model=list[IncidentResponse])
async def list_incidents(
    issue_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List incidents with optional filters."""
    query = select(Incident).limit(limit).offset(offset)
    if issue_type:
        query = query.where(Incident.primary_issue_type == issue_type)
    if status:
        query = query.where(Incident.lifecycle_status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=IncidentResponse, status_code=201)
async def create_incident(
    primary_issue_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Create a new incident."""
    incident = Incident(primary_issue_type=primary_issue_type)
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single incident."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update incident status or severity."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if payload.lifecycle_status:
        incident.lifecycle_status = payload.lifecycle_status
    if payload.severity_score is not None:
        incident.severity_score = payload.severity_score
    await db.commit()
    await db.refresh(incident)
    return incident
