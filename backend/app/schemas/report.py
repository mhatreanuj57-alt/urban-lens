"""Pydantic schemas for reports, media assets and inference results."""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

from app.models.report import ISSUE_TYPES, REPORT_STATUSES, LOCATION_SOURCES

IssueType = Literal[
    "pothole", "garbage", "damaged_streetlight", "waterlogging", "illegal_dumping"
]


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    object_key: str
    public_object_key: Optional[str] = None
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    captured_at: Optional[datetime] = None
    created_at: datetime


class InferenceRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task: str
    model_name: str
    model_version: str
    result: dict
    latency_ms: Optional[int] = None
    created_at: datetime


class Detection(BaseModel):
    bbox: list[float]
    class_name: str
    confidence: float


class ReportBase(BaseModel):
    issue_type: Optional[IssueType] = None
    description: Optional[str] = Field(None, max_length=4000)


class MediaRef(BaseModel):
    object_key: str = Field(min_length=1, max_length=500)
    mime_type: str = "image/jpeg"
    kind: Literal["image", "video"] = "image"


class ReportCreate(ReportBase):
    """Submission payload — issue type, location pin, consent and media refs."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_source: Literal["exif", "manual_pin", "landmark", "unknown"] = "manual_pin"
    landmark: Optional[str] = Field(None, max_length=200)
    occurred_at: Optional[datetime] = None
    consent_location: bool
    consent_training: bool = False
    media: list[MediaRef] = Field(default_factory=list, max_length=5)

    @field_validator("consent_location")
    @classmethod
    def consent_required(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Location consent is required to submit a report")
        return v

    @field_validator("media")
    @classmethod
    def at_least_one_media(cls, v: list[MediaRef]) -> list[MediaRef]:
        if not v:
            raise ValueError("At least one photo or video is required")
        return v


class PriorityFactors(BaseModel):
    severity: float = 0
    confirmations: float = 0
    recency: float = 0
    risk_context: float = 0
    road_context: float = 0


class ReportResponse(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reporter_id: UUID
    incident_id: Optional[UUID] = None
    status: str
    landmark: Optional[str] = None
    location_source: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    public_latitude: Optional[float] = None
    public_longitude: Optional[float] = None
    consent_location: bool
    occurred_at: Optional[datetime] = None
    submitted_at: datetime
    priority_score: Optional[float] = None
    priority_factors: Optional[dict] = None
    severity_score: Optional[float] = None
    verification_state: str


class ReportDetail(ReportResponse):
    """Extended report response with media, inference results and incident link."""

    media_assets: list[MediaAssetResponse] = []
    inference_runs: list[InferenceRunResponse] = []


class ReportVerify(BaseModel):
    decision: Literal["verified", "rejected"]
    reason: Optional[str] = Field(None, max_length=1000)


class ComplaintRequest(BaseModel):
    language: Literal["en", "hi", "mr"] = "en"


class ComplaintDraft(BaseModel):
    report_id: UUID
    language: str
    subject: str
    body: str
