"""Analytics endpoints — hotspots and summary statistics."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, cast, Numeric, Float
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.incident import Incident
from app.models.report import Report
from app.schemas.analytics import Hotspot, SummaryStats

router = APIRouter()


@router.get("/hotspots", response_model=list[Hotspot])
async def hotspots(
    days: int = Query(30, ge=1, le=365),
    grid_precision: int = Query(3, ge=2, le=4),
    db: AsyncSession = Depends(get_db),
):
    """Clustered report statistics on a lat/lng grid for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    lat_cell = func.round(cast(Report.public_latitude, Numeric), grid_precision)
    lng_cell = func.round(cast(Report.public_longitude, Numeric), grid_precision)

    stmt = (
        select(
            lat_cell.label("lat"),
            lng_cell.label("lng"),
            func.count(Report.id).label("cnt"),
            func.max(Report.issue_type).label("top_issue"),
            func.avg(cast(Report.priority_score, Float)).label("avg_priority"),
        )
        .where(Report.submitted_at >= since, Report.status != "rejected",
               Report.public_latitude.is_not(None))
        .group_by(lat_cell, lng_cell)
        .order_by(func.count(Report.id).desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        Hotspot(
            latitude=float(row.lat),
            longitude=float(row.lng),
            report_count=int(row.cnt),
            top_issue_type=row.top_issue,
            avg_priority=round(float(row.avg_priority), 2) if row.avg_priority else None,
        )
        for row in rows
    ]


@router.get("/summary", response_model=SummaryStats)
async def summary(db: AsyncSession = Depends(get_db)):
    """Platform-wide counters for the landing page and dashboards."""
    by_status_rows = (await db.execute(
        select(Report.status, func.count(Report.id)).group_by(Report.status)
    )).all()
    by_issue_rows = (await db.execute(
        select(Report.issue_type, func.count(Report.id)).group_by(Report.issue_type)
    )).all()
    total = (await db.execute(select(func.count(Report.id)))).scalar() or 0
    inc_total = (await db.execute(select(func.count(Incident.id)))).scalar() or 0
    inc_open = (await db.execute(
        select(func.count(Incident.id)).where(
            Incident.lifecycle_status.in_(["open", "assigned", "in_progress"])
        )
    )).scalar() or 0
    inc_resolved = (await db.execute(
        select(func.count(Incident.id)).where(
            Incident.lifecycle_status.in_(["resolved", "closed"])
        )
    )).scalar() or 0

    return SummaryStats(
        total_reports=int(total),
        reports_by_status={str(s): int(c) for s, c in by_status_rows if s},
        reports_by_issue={str(i): int(c) for i, c in by_issue_rows if i},
        total_incidents=int(inc_total),
        open_incidents=int(inc_open),
        resolved_incidents=int(inc_resolved),
    )
