"""Initial UrbanLens schema (users, reports, incidents, media, inference,
wards, audit, duplicates, weather) with PostGIS enabled.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography, Geometry

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("role", sa.Enum("citizen", "moderator", "admin", name="user_role"),
                  nullable=False, server_default="citizen"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("consent_training", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "wards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("boundary", Geometry(geometry_type="MULTIPOLYGON", srid=4326)),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("primary_issue_type",
                  sa.Enum("pothole", "garbage", "damaged_streetlight",
                          "waterlogging", "illegal_dumping", name="issue_type"),
                  nullable=False),
        sa.Column("centroid", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("ward_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("wards.id"), nullable=True),
        sa.Column("lifecycle_status",
                  sa.Enum("open", "assigned", "in_progress", "resolved", "closed",
                          name="lifecycle_status"),
                  nullable=False, server_default="open"),
        sa.Column("severity_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("priority_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("priority_factors", postgresql.JSONB(), nullable=True),
        sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_incidents_centroid_gist", "incidents", ["centroid"],
                    postgresql_using="gist")
    op.create_index("ix_incidents_lifecycle", "incidents", ["lifecycle_status"])
    op.create_index("ix_incidents_priority", "incidents", ["priority_score"])

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("incidents.id"), nullable=True),
        sa.Column("issue_type",
                  sa.Enum("pothole", "garbage", "damaged_streetlight",
                          "waterlogging", "illegal_dumping",
                          name="issue_type", create_type=False),
                  nullable=True),
        sa.Column("status",
                  sa.Enum("submitted", "under_review", "verified", "assigned",
                          "in_progress", "resolved", "rejected",
                          name="report_status"),
                  nullable=False, server_default="submitted"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("landmark", sa.String(200), nullable=True),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("public_location", Geography(geometry_type="POINT", srid=4326)),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("public_latitude", sa.Float(), nullable=True),
        sa.Column("public_longitude", sa.Float(), nullable=True),
        sa.Column("location_source",
                  sa.Enum("exif", "manual_pin", "landmark", "unknown",
                          name="location_source"),
                  nullable=False, server_default="unknown"),
        sa.Column("consent_location", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("consent_training", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("priority_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("priority_factors", postgresql.JSONB(), nullable=True),
        sa.Column("severity_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("verification_state",
                  sa.Enum("unreviewed", "verified", "rejected",
                          name="verification_state"),
                  nullable=False, server_default="unreviewed"),
    )
    op.create_index("ix_reports_issue_status_submitted", "reports",
                    ["issue_type", "status", "submitted_at"])
    op.create_index("ix_reports_location_gist", "reports", ["location"],
                    postgresql_using="gist")
    op.create_index("ix_reports_reporter", "reports", ["reporter_id"])
    op.create_index("ix_reports_incident", "reports", ["incident_id"])

    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("kind",
                  sa.Enum("image", "video", "annotated_image", "after_image",
                          name="media_kind"),
                  nullable=False),
        sa.Column("object_key", sa.String(500), nullable=False, unique=True),
        sa.Column("public_object_key", sa.String(500), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Numeric(), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "inference_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("media_assets.id"), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=False),
        sa.Column("task",
                  sa.Enum("detection", "embedding", "blur", "risk",
                          name="inference_task"),
                  nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "duplicate_candidates",
        sa.Column("report_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("reports.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("candidate_report_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("reports.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("geo_distance_m", sa.Numeric(10, 2), nullable=True),
        sa.Column("image_similarity", sa.Numeric(4, 3), nullable=True),
        sa.Column("time_distance_hours", sa.Numeric(10, 2), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("decision",
                  sa.Enum("pending", "merged", "not_duplicate",
                          name="duplicate_decision"),
                  nullable=False, server_default="pending"),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("previous_value", postgresql.JSONB(), nullable=True),
        sa.Column("new_value", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_entity", "audit_events", ["entity_type", "entity_id"])
    op.create_index("ix_audit_created", "audit_events", ["created_at"])

    op.create_table(
        "weather_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("grid_cell", sa.String(50), nullable=False),
        sa.Column("rainfall_mm", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("tide_m", sa.Numeric(5, 2), nullable=True),
        sa.Column("source", sa.String(100), nullable=False, server_default="manual"),
    )
    op.create_index("ix_weather_cell_time", "weather_observations",
                    ["grid_cell", "observed_at"])

    op.create_table(
        "flood_risk_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("prediction_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("grid_cell", sa.String(50), nullable=False),
        sa.Column("risk_level",
                  sa.Enum("low", "medium", "high", name="risk_level"),
                  nullable=False, server_default="low"),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("model_version", sa.String(100), nullable=False,
                  server_default="rules-v0"),
        sa.Column("feature_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_risk_cell_for", "flood_risk_predictions",
                    ["grid_cell", "prediction_for"])


def downgrade() -> None:
    op.drop_table("flood_risk_predictions")
    op.drop_table("weather_observations")
    op.drop_table("audit_events")
    op.drop_table("duplicate_candidates")
    op.drop_table("inference_runs")
    op.drop_table("media_assets")
    op.drop_table("reports")
    op.drop_table("incidents")
    op.drop_table("wards")
    op.drop_table("users")
    for enum_name in ("report_status", "location_source", "verification_state",
                      "issue_type", "lifecycle_status", "media_kind",
                      "inference_task", "duplicate_decision", "risk_level",
                      "user_role"):
        op.execute(f'DROP TYPE IF EXISTS "{enum_name}"')
