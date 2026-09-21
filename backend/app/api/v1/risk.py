"""Waterlogging risk — transparent rules-based baseline (demo feature).

Not an emergency warning system. Combines recent verified waterlogging
reports and recent rainfall observations (when available) into
low / medium / high risk for the requested map cell.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, cast, Float
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.report import Report
from app.models.weather import WeatherObservation
from app.schemas.analytics import RiskCell

router = APIRouter()


def grid_cell_for(lat: float, lng: float) -> str:
    """~1 km grid cell id from a rounded lat/lng pair."""
    return f"{round(lat, 2)}:{round(lng, 2)}"


@router.get("/waterlogging", response_model=RiskCell)
async def waterlogging_risk(
    latitude: float = Query(..., ge=-90, le=90, alias="lat"),
    longitude: float = Query(..., ge=-180, le=180, alias="lng"),
    db: AsyncSession = Depends(get_db),
):
    """Current waterlogging risk for the cell containing (lat, lng)."""
    now = datetime.now(timezone.utc)
    cell = grid_cell_for(latitude, longitude)

    # Verified waterlogging reports within ~1 km over the last 30 days
    since = now - timedelta(days=30)
    point = func.ST_GeogFromText(f"POINT({longitude} {latitude})")
    nearby = await db.execute(
        select(func.count(Report.id)).where(
            Report.issue_type == "waterlogging",
            Report.status == "verified",
            Report.submitted_at >= since,
            Report.location.is_not(None),
            func.ST_DWithin(Report.location, point, 1000),
        )
    )
    waterlogging_30d = int(nearby.scalar() or 0)

    # Latest rainfall observation in the same cell (0 when no data)
    obs = (await db.execute(
        select(WeatherObservation)
        .where(WeatherObservation.grid_cell == cell,
               WeatherObservation.observed_at >= now - timedelta(days=1))
        .order_by(WeatherObservation.observed_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    rainfall_24h = float(obs.rainfall_mm) if obs else 0.0

    # Transparent rules-based score
    score = min(40 + waterlogging_30d * 12, 70) + min(rainfall_24h, 50)
    score = round(min(score, 100.0), 2)
    if score >= 70:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    return RiskCell(
        grid_cell=cell,
        latitude=round(latitude, 3),
        longitude=round(longitude, 3),
        risk_level=level,
        risk_score=score,
        rainfall_mm_24h=rainfall_24h,
        verified_waterlogging_30d=waterlogging_30d,
        updated_at=now,
    )
