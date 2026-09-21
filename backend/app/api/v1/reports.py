"""Reports API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_current_user, get_optional_user
from app.database import get_db
from app.models.media_asset import MediaAsset
from app.models.incident import Incident
from app.models.report import Report
from app.models.user import User
from app.schemas.report import (
    MediaAssetResponse,
    InferenceRunResponse,
    ReportCreate,
    ReportDetail,
    ReportResponse,
    ReportVerify,
)
from app.services import storage as storage_svc
from app.services.audit import record_audit
from app.services.duplicate import DuplicateService
from app.services.inference import dispatch_pipeline
from app.services.priority import compute_priority

logger = logging.getLogger(__name__)

router = APIRouter()


def _in_bbox(lat: float, lng: float) -> bool:
    min_lng, min_lat, max_lng, max_lat = settings.NM_BBOX
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


def _public_coords(lat: float, lng: float) -> tuple[float, float]:
    """Reduce precision to ~110 m for public views (privacy)."""
    return round(lat, 3), round(lng, 3)


def _redact(report: Report, user: User | None) -> dict:
    """Serialize a report, hiding exact locations from non-owners/moderators."""
    data = ReportResponse.model_validate(report).model_dump(mode="json")
    is_owner = user is not None and user.id == report.reporter_id
    is_moderator = user is not None and user.role in ("moderator", "admin")
    if not (is_owner or is_moderator):
        data["latitude"] = data["public_latitude"]
        data["longitude"] = data["public_longitude"]
    return data


def _to_detail(report: Report, user: User | None) -> dict:
    data = _redact(report, user)
    data["media_assets"] = [
        MediaAssetResponse.model_validate(m).model_dump(mode="json")
        for m in report.media_assets_rel
    ]
    data["inference_runs"] = [
        InferenceRunResponse.model_validate(r).model_dump(mode="json")
        for r in report.inference_runs_rel
    ]
    return data


async def _load_detail(db: AsyncSession, report_id: UUID, user: User | None) -> dict:
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_detail(report, user)


@router.get("/", response_model=list[dict])
async def list_reports(
    issue_type: str | None = Query(None),
    status: str | None = Query(None),
    mine: bool = Query(False, description="Only reports submitted by the caller"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """List reports with optional filters. Public view uses reduced precision."""
    query = select(Report).order_by(Report.submitted_at.desc())
    if issue_type:
        query = query.where(Report.issue_type == issue_type)
    if status:
        query = query.where(Report.status == status)
    if mine:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        query = query.where(Report.reporter_id == user.id)
    else:
        query = query.where(Report.status != "rejected")
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    reports = result.scalars().unique().all()
    return [_redact(r, user) for r in reports]


@router.post("/", response_model=ReportDetail, status_code=201)
async def create_report(
    payload: ReportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new report with a confirmed issue type, location pin and media."""
    if not _in_bbox(payload.latitude, payload.longitude):
        raise HTTPException(
            status_code=422,
            detail="Location is outside the supported area (Navi Mumbai)",
        )
    for media in payload.media:
        if not storage_svc.storage_service.object_exists(media.object_key):
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded file not found in storage: {media.object_key}",
            )

    pub_lat, pub_lng = _public_coords(payload.latitude, payload.longitude)
    report = Report(
        reporter_id=user.id,
        issue_type=payload.issue_type,
        description=payload.description,
        landmark=payload.landmark,
        location=func.ST_GeogFromText(f"POINT({payload.longitude} {payload.latitude})"),
        public_location=func.ST_GeogFromText(f"POINT({pub_lng} {pub_lat})"),
        latitude=payload.latitude,
        longitude=payload.longitude,
        public_latitude=pub_lat,
        public_longitude=pub_lng,
        location_source=payload.location_source,
        consent_location=payload.consent_location,
        consent_training=payload.consent_training or user.consent_training,
        occurred_at=payload.occurred_at,
        status="submitted",
    )
    db.add(report)
    await db.flush()

    media_assets = [
        MediaAsset(
            report_id=report.id,
            kind=media.kind,
            object_key=media.object_key,
            mime_type=media.mime_type,
        )
        for media in payload.media
    ]
    db.add_all(media_assets)
    await db.flush()
    media_asset_ids = [asset.id for asset in media_assets]

    await record_audit(
        db,
        actor_id=user.id,
        entity_type="report",
        entity_id=report.id,
        action="report.submitted",
        new_value={"issue_type": payload.issue_type,
                   "location_source": payload.location_source},
    )
    await db.commit()
    await db.refresh(report)

    for asset_id in media_asset_ids:
        dispatch_pipeline(asset_id)
    return await _load_detail(db, report.id, user)


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: UUID,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single report with media, AI analysis and incident link."""
    return await _load_detail(db, report_id, user)


@router.post("/{report_id}/verify", response_model=ReportDetail)
async def verify_report(
    report_id: UUID,
    payload: ReportVerify,
    moderator: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Moderator verification of a report (moderator or admin only)."""
    if moderator.role not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Moderator role required")
    report = (await db.execute(
        select(Report).where(Report.id == report_id)
    )).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    previous = {"status": report.status,
                "verification_state": report.verification_state}
    report.verification_state = payload.decision
    report.status = "verified" if payload.decision == "verified" else "rejected"
    await record_audit(
        db,
        actor_id=moderator.id,
        entity_type="report",
        entity_id=report.id,
        action=f"report.{payload.decision}",
        previous_value=previous,
        new_value={"status": report.status,
                   "verification_state": report.verification_state,
                   "reason": payload.reason},
    )

    if report.incident_id:
        incident = (await db.execute(
            select(Incident).where(Incident.id == report.incident_id)
        )).scalar_one_or_none()
        if incident:
            await DuplicateService.refresh_incident(db, incident)

    await db.commit()
    return await _load_detail(db, report_id, moderator)
