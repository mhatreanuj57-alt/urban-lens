"""SQLAlchemy ORM models package — imports expose all tables to Alembic."""

from app.models.user import User
from app.models.report import Report
from app.models.incident import Incident
from app.models.media_asset import MediaAsset
from app.models.inference_run import InferenceRun
from app.models.ward import Ward
from app.models.audit_event import AuditEvent
from app.models.duplicate_candidate import DuplicateCandidate
from app.models.weather import WeatherObservation, FloodRiskPrediction

__all__ = [
    "User",
    "Report",
    "Incident",
    "MediaAsset",
    "InferenceRun",
    "Ward",
    "AuditEvent",
    "DuplicateCandidate",
    "WeatherObservation",
    "FloodRiskPrediction",
]
