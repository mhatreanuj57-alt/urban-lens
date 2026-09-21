"""Seed script — demo wards, users, reports and incidents for local development.

Run: python -m app.seed
Idempotent: skips entities that already exist (by email / name).
"""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from geoalchemy2 import WKTElement
from sqlalchemy import select

from app.config import settings
from app.core.security import hash_password
from app.database import async_session
from app.models.incident import Incident
from app.models.report import Report
from app.models.user import User
from app.models.ward import Ward
from app.services.priority import compute_priority

NOW = datetime.now(timezone.utc)

# Password for the demo accounts when Supabase Auth is the identity layer.
# Kept out of the repository: set SEED_DEMO_PASSWORD in the gitignored .env.
DEMO_PASSWORD = settings.SEED_DEMO_PASSWORD

WARDS = [
    ("Vashi", 72.995, 19.077),
    ("Nerul", 73.017, 19.044),
    ("Seawoods", 73.028, 19.032),
    ("CBD Belapur", 73.043, 19.018),
    ("Kharghar", 73.067, 19.040),
    ("Sanpada", 73.014, 19.065),
    ("Kopar Khairane", 73.007, 19.117),
    ("Ghansoli", 73.005, 19.135),
    ("Airoli", 72.998, 19.152),
]

USERS = [
    ("admin@urbanlens.demo", "admin1234", "admin", "Ops Admin", True),
    ("moderator@urbanlens.demo", "moderator123", "moderator", "NMMC Moderator", True),
    ("citizen@urbanlens.demo", "citizen1234", "citizen", "Priya Sharma", False),
]

# (issue_type, lat, lng, landmark, description, days_ago, status, verification_state)
REPORTS = [
    ("pothole", 19.0773, 72.9986, "Near Vashi Railway Station, Sector 9",
     "Deep pothole on the service road causing two-wheelers to swerve.", 6,
     "verified", "verified"),
    ("pothole", 19.0771, 72.9989, "Vashi Station Road, opposite bus depot",
     "Same pothole, filled with muddy water after rain.", 3,
     "under_review", "unreviewed"),
    ("pothole", 19.0780, 72.9990, "Vashi bridge approach",
     "Another deep pothole near the bridge approach.", 1,
     "submitted", "unreviewed"),
    ("garbage", 19.0445, 73.0176, "Nerul Sector 29 market lane",
     "Garbage not collected for three days; foul smell near the market.", 5,
     "verified", "verified"),
    ("illegal_dumping", 19.1171, 73.0072, "Kopar Khairane node, behind sector 8",
     "Construction debris dumped overnight near the playground.", 4,
     "under_review", "unreviewed"),
    ("waterlogging", 19.0180, 73.0435, "CBD Belapur station road underpass",
     "Knee-deep water after 30 minutes of rain; traffic blocked.", 2,
     "verified", "verified"),
    ("waterlogging", 19.0178, 73.0438, "Belapur Udyog Marg",
     "Waterlogging near the Udyog Marg signal.", 1,
     "under_review", "unreviewed"),
    ("damaged_streetlight", 19.0322, 73.0281, "Seawoods, near grand central",
     "Streetlight flickering and off since Monday; junction is dark at night.", 7,
     "verified", "verified"),
    ("garbage", 19.0650, 73.0141, "Sanpada village road",
     "Overflowing community bin near the village road.", 8,
     "resolved", "verified"),
    ("pothole", 19.0401, 73.0671, "Kharghar sector 12 main road",
     "Series of potholes on the sector 12 main road.", 10,
     "verified", "verified"),
]

INCIDENT_STATUSES = {
    "Sanpada village road": "resolved",
    "Kharghar sector 12 main road": "closed",
    "CBD Belapur station road underpass": "assigned",
}


def ward_polygon(lng: float, lat: float) -> str:
    d = 0.012
    return (
        f"MULTIPOLYGON((({lng - d} {lat - d},{lng + d} {lat - d},"
        f"{lng + d} {lat + d},{lng - d} {lat + d},{lng - d} {lat - d})))"
    )


def nearest_ward_name(lat: float, lng: float) -> str:
    return min(WARDS, key=lambda w: (w[2] - lat) ** 2 + (w[1] - lng) ** 2)[0]


def _supabase_admin_headers() -> dict[str, str]:
    key = settings.SUPABASE_SECRET_KEY
    return {"apikey": key, "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"}


async def ensure_supabase_auth_user(email: str, display_name: str) -> UUID:
    """Create (or fetch) a Supabase Auth user and return its uid.

    The uid becomes public.users.id, so the profile auto-provisioned on login
    matches this row and the seeded role is preserved.
    """
    base = f"{settings.SUPABASE_URL}/auth/v1/admin/users"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{base}?page=1&per_page=1000",
                                headers=_supabase_admin_headers())
        resp.raise_for_status()
        for u in resp.json().get("users", []):
            if u.get("email") == email:
                return UUID(u["id"])

        resp = await client.post(
            base,
            headers=_supabase_admin_headers(),
            json={
                "email": email,
                "password": DEMO_PASSWORD,
                "email_confirm": True,
                "app_metadata": {"role": "authenticated"},
                "user_metadata": {"display_name": display_name},
            },
        )
        resp.raise_for_status()
        return UUID(resp.json()["id"])


async def seed() -> None:
    supabase_mode = bool(settings.SUPABASE_URL and settings.SUPABASE_SECRET_KEY)
    async with async_session() as db:
        # --- wards ----------------------------------------------------------
        wards: dict[str, Ward] = {}
        for name, lng, lat in WARDS:
            existing = (await db.execute(
                select(Ward).where(Ward.name == name)
            )).scalar_one_or_none()
            if existing:
                wards[name] = existing
                continue
            ward = Ward(
                name=name,
                boundary=WKTElement(ward_polygon(lng, lat), srid=4326),
                source_url="https://github.com/UrbanLens/demo-wards",
            )
            db.add(ward)
            wards[name] = ward
        await db.flush()

        # --- users ----------------------------------------------------------
        users: dict[str, User] = {}
        for email, password, role, display_name, consent in USERS:
            existing = (await db.execute(
                select(User).where(User.email == email)
            )).scalar_one_or_none()
            if existing:
                existing.role = role
                existing.display_name = display_name
                users[role] = existing
                continue
            if supabase_mode:
                uid = await ensure_supabase_auth_user(email, display_name)
                user = User(
                    id=uid,
                    email=email,
                    hashed_password="!supabase-auth",
                    role=role,
                    display_name=display_name,
                    consent_training=consent,
                )
            else:
                user = User(
                    email=email,
                    hashed_password=hash_password(password),
                    role=role,
                    display_name=display_name,
                    consent_training=consent,
                )
            db.add(user)
            users[role] = user
        await db.flush()

        # --- reports + incidents (clustered manually, pipeline-free) --------
        clusters: dict[tuple, Incident] = {}
        for issue, lat, lng, landmark, desc, days_ago, status, verification in REPORTS:
            submitted_at = NOW - timedelta(days=days_ago)
            key = (issue, round(lat, 3), round(lng, 3))

            already = (await db.execute(
                select(Report).where(Report.description == desc)
            )).scalars().first()
            if already:
                # Keep the incident map consistent with the reports actually stored.
                if already.incident_id:
                    incident = await db.get(Incident, already.incident_id)
                    if incident is not None:
                        clusters[key] = incident
                continue

            cluster_members = [r for r in REPORTS
                               if (r[0], round(r[1], 3), round(r[2], 3)) == key]
            incident = clusters.get(key)

            if incident is None:
                ward_name = nearest_ward_name(lat, lng)
                incident = Incident(
                    primary_issue_type=issue,
                    latitude=lat,
                    longitude=lng,
                    centroid=WKTElement(f"POINT({lng} {lat})", srid=4326),
                    ward_id=wards[ward_name].id,
                    lifecycle_status=INCIDENT_STATUSES.get(landmark, "open"),
                    first_seen_at=submitted_at,
                    last_seen_at=submitted_at,
                    report_count=0,
                )
                if incident.lifecycle_status in ("resolved", "closed"):
                    incident.resolved_at = submitted_at + timedelta(days=2)
                db.add(incident)
                await db.flush()
                clusters[key] = incident

            report = Report(
                reporter_id=users["citizen"].id,
                incident_id=incident.id,
                issue_type=issue,
                status=status,
                description=desc,
                landmark=landmark,
                location=WKTElement(f"POINT({lng} {lat})", srid=4326),
                public_location=WKTElement(
                    f"POINT({round(lng, 3)} {round(lat, 3)})", srid=4326
                ),
                latitude=lat,
                longitude=lng,
                public_latitude=round(lat, 3),
                public_longitude=round(lng, 3),
                location_source="manual_pin",
                consent_location=True,
                occurred_at=submitted_at,
                submitted_at=submitted_at,
                verification_state=verification,
            )
            db.add(report)
            await db.flush()

            score, factors = compute_priority(
                issue_type=issue,
                report_count=len(cluster_members),
                submitted_at=submitted_at,
            )
            report.severity_score = factors["severity"]
            report.priority_score = score
            report.priority_factors = factors
            incident.severity_score = factors["severity"]

        for key, incident in clusters.items():
            members = [r for r in REPORTS
                       if (r[0], round(r[1], 3), round(r[2], 3)) == key]
            incident.report_count = len(members)
            incident.first_seen_at = NOW - timedelta(days=max(m[5] for m in members))
            incident.last_seen_at = NOW - timedelta(days=min(m[5] for m in members))
            score, factors = compute_priority(
                issue_type=incident.primary_issue_type,
                severity=incident.severity_score,
                report_count=incident.report_count,
                submitted_at=incident.first_seen_at,
            )
            incident.priority_score = score
            incident.priority_factors = factors

        await db.commit()
        print(f"Seeded {len(wards)} wards, {len(users)} users, "
              f"{len(REPORTS)} reports, {len(clusters)} incidents.")


if __name__ == "__main__":
    asyncio.run(seed())
