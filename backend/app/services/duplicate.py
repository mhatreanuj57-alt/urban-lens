"""Duplicate detection and incident clustering service.

1. Query PostGIS for reports of the same issue type within a distance window.
2. Filter by time window.
3. Record duplicate candidate pairs with geo/time distance and image similarity.
4. Attach the report to the most relevant nearby incident, or create one.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.models.incident import Incident
from app.models.duplicate_candidate import DuplicateCandidate

logger = logging.getLogger(__name__)


def point_wkt(longitude: float, latitude: float) -> str:
    return f"POINT({longitude} {latitude})"


class DuplicateService:
    """Find near-duplicate reports and cluster them into incidents."""

    @staticmethod
    async def find_candidates(
        db: AsyncSession,
        report: Report,
        max_distance_m: float = 100.0,
        max_time_hours: int = 336,  # 14 days
        max_candidates: int = 10,
    ) -> list[dict]:
        """Find candidate duplicates for a report using spatial + time windows."""
        if report.latitude is None or report.longitude is None:
            return []

        since = (report.submitted_at or datetime.now(timezone.utc)) - timedelta(
            hours=max_time_hours
        )
        point = func.ST_GeogFromText(point_wkt(report.longitude, report.latitude))

        distance = func.ST_Distance(Report.location, point)
        stmt = (
            select(
                Report,
                distance.label("distance_m"),
                func.abs(
                    func.extract(
                        "epoch", Report.submitted_at - report.submitted_at
                    )
                    / 3600.0
                ).label("time_hours"),
            )
            .where(
                Report.id != report.id,
                Report.issue_type == report.issue_type,
                Report.location.is_not(None),
                Report.submitted_at >= since,
                func.ST_DWithin(Report.location, point, max_distance_m),
            )
            .order_by(distance_m.asc())
            .limit(max_candidates)
        )
        result = await db.execute(stmt)
        rows = result.all()
        candidates = []
        for row in rows:
            candidate: Report = row[0]
            candidates.append(
                {
                    "report_id": candidate.id,
                    "incident_id": candidate.incident_id,
                    "geo_distance_m": float(row[1] or 0),
                    "time_distance_hours": float(row[2] or 0),
                    "latitude": candidate.latitude,
                    "longitude": candidate.longitude,
                }
            )
        return candidates

    @staticmethod
    async def record_candidates(
        db: AsyncSession,
        report: Report,
        candidates: list[dict],
        image_similarity: float | None = None,
    ) -> list[DuplicateCandidate]:
        """Persist duplicate candidate pairs (both directions)."""
        recorded = []
        for cand in candidates:
            distance_m = cand["geo_distance_m"]
            time_hours = cand["time_distance_hours"]
            # Rule-based confidence: closer in space and time is more likely a duplicate
            geo_score = max(0.0, 1.0 - distance_m / 100.0)
            time_score = max(0.0, 1.0 - time_hours / 336.0)
            visual = float(image_similarity) if image_similarity is not None else 0.5
            confidence = round(0.4 * geo_score + 0.3 * time_score + 0.3 * visual, 3)

            for a, b in ((report.id, cand["report_id"]), (cand["report_id"], report.id)):
                exists = await db.get(DuplicateCandidate, {"report_id": a, "candidate_report_id": b})
                if exists:
                    continue
                dc = DuplicateCandidate(
                    report_id=a,
                    candidate_report_id=b,
                    geo_distance_m=round(distance_m, 2),
                    image_similarity=image_similarity,
                    time_distance_hours=round(time_hours, 2),
                    confidence=confidence,
                    decision="pending",
                )
                db.add(dc)
                recorded.append(dc)
        await db.flush()
        return recorded

    @staticmethod
    async def cluster_report(
        db: AsyncSession,
        report: Report,
        candidates: list[dict],
    ) -> Incident:
        """Attach the report to a nearby incident or create a new one."""
        incident = None
        # Prefer an incident already linked to a candidate
        for cand in candidates:
            if cand.get("incident_id"):
                result = await db.execute(
                    select(Incident).where(Incident.id == cand["incident_id"])
                )
                incident = result.scalar_one_or_none()
                if incident:
                    break

        if incident is None:
            incident = Incident(
                primary_issue_type=report.issue_type,
                centroid=report.location,
                latitude=report.latitude,
                longitude=report.longitude,
                lifecycle_status="open",
                report_count=0,
                severity_score=report.severity_score,
            )
            db.add(incident)
            await db.flush()

        report.incident_id = incident.id
        await db.flush()
        await DuplicateService.refresh_incident(db, incident)
        return incident

    @staticmethod
    async def refresh_incident(db: AsyncSession, incident: Incident) -> None:
        """Recompute incident aggregates from its member reports."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(
                func.count(Report.id),
                func.max(Report.submitted_at),
                func.min(Report.submitted_at),
                func.max(Report.severity_score),
            ).where(
                Report.incident_id == incident.id,
                Report.status != "rejected",
            )
        )
        count, last_seen, first_seen, max_severity = result.one()
        incident.report_count = int(count or 0)
        if last_seen:
            incident.last_seen_at = last_seen
        if first_seen:
            incident.first_seen_at = first_seen
        if max_severity is not None:
            incident.severity_score = float(max_severity)

        if incident.lifecycle_status in ("open", "assigned", "in_progress"):
            incident.resolved_at = None
        if incident.lifecycle_status == "resolved" and incident.resolved_at is None:
            incident.resolved_at = now

        from app.services.priority import compute_priority

        score, factors = compute_priority(
            issue_type=incident.primary_issue_type,
            severity=float(incident.severity_score or 0) or None,
            report_count=incident.report_count,
            submitted_at=incident.first_seen_at,
        )
        incident.priority_score = score
        incident.priority_factors = factors
        await db.flush()


duplicate_service = DuplicateService()
