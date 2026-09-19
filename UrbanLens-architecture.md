# UrbanLens AI — Architecture and Data Models

## Architecture overview

```text
Citizen web app / Admin dashboard (Next.js + TypeScript)
                    |
             HTTPS / REST API
                    v
            FastAPI application
      ┌─────────────┼──────────────┐
      v             v              v
 PostgreSQL +     Redis queue   Object storage
 PostGIS          + workers     (originals/derivatives)
      |             |              |
      └─────── ML inference ───────┘
                 (Python)
                     |
          YOLO + OpenCV + embeddings
                     |
       Weather/rainfall/tide data adapters
```

## Stack

| Layer | Choice | Purpose |
| --- | --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS | Citizen and admin interface |
| Maps | MapLibre GL + OpenStreetMap | Map layers and GeoJSON |
| API | FastAPI, Pydantic, SQLAlchemy | Python ML-friendly API |
| Database | PostgreSQL 16 + PostGIS | Relational + spatial queries |
| Queue/cache | Redis + Celery/RQ | Background inference/video jobs |
| Media storage | Cloudflare R2, S3, or MinIO local | Private originals + public derivatives |
| Detection | YOLO, PyTorch, OpenCV | Fine-tuned object detection |
| Duplicate matching | CLIP/SigLIP embeddings + pgvector | Visual near-duplicate search |
| Forecasting | LightGBM baseline, then XGBoost | Interpretable initial waterlogging risk |
| Monitoring | Sentry + structured logs | Error and inference diagnostics |
| CI | GitHub Actions | Lint, tests, build/migration checks |

## Responsibilities

### Frontend

Requests signed upload URLs, displays AI results/map/workflow, and never stores secrets.

### API

Authenticates users, validates reports, provides signed URLs, exposes reporting/incident/analytics APIs, enqueues jobs, and enforces roles/audit history.

### ML worker

1. Validate file and extract metadata.
2. Blur faces/plates for a public derivative.
3. Sample video frames.
4. Run detector, derive severity, create image embedding.
5. Find duplicate candidates and update incident.
6. Persist immutable inference output with exact model version.

### Forecast worker

Ingests weather/tide readings with source/timestamp, joins them to spatial grid and waterlogging history, predicts calibrated risk, and saves feature snapshots.

## Data models

### `users`

`id UUID PK`, `email CITEXT UNIQUE`, `display_name VARCHAR(100)`, `role ENUM(citizen, moderator, admin)`, `consent_training BOOLEAN DEFAULT false`, `created_at TIMESTAMPTZ`.

### `reports`

One citizen submission; may later join an incident.

`id UUID PK`, `reporter_id UUID FK users`, `incident_id UUID FK incidents NULL`, `issue_type ENUM`, `status ENUM`, `description TEXT`, `location GEOGRAPHY(Point,4326)`, `public_location GEOGRAPHY(Point,4326)`, `location_source ENUM(exif, manual_pin, landmark, unknown)`, `occurred_at TIMESTAMPTZ`, `submitted_at TIMESTAMPTZ`, `priority_score NUMERIC(5,2)`, `verification_state ENUM(unreviewed, verified, rejected)`.

Indexes: GIST `location`; B-tree `(issue_type, status, submitted_at DESC)`.

### `media_assets`

`id UUID PK`, `report_id UUID FK reports`, `kind ENUM(image, video, annotated_image, after_image)`, `object_key TEXT UNIQUE`, `public_object_key TEXT NULL`, `mime_type VARCHAR(100)`, `width INT`, `height INT`, `duration_seconds NUMERIC NULL`, `sha256 CHAR(64)`, `captured_at TIMESTAMPTZ NULL`, `created_at TIMESTAMPTZ`.

### `inference_runs`

Immutable model execution history.

`id UUID PK`, `media_asset_id UUID FK media_assets`, `model_name VARCHAR(100)`, `model_version VARCHAR(100)`, `task ENUM(detection, embedding, blur, risk)`, `result JSONB`, `latency_ms INT`, `created_at TIMESTAMPTZ`.

### `incidents`

Clustered operational issue.

`id UUID PK`, `primary_issue_type ENUM`, `centroid GEOGRAPHY(Point,4326)`, `ward_id UUID FK wards NULL`, `lifecycle_status ENUM(open, assigned, in_progress, resolved, closed)`, `severity_score NUMERIC(5,2)`, `priority_score NUMERIC(5,2)`, `report_count INT`, `first_seen_at TIMESTAMPTZ`, `last_seen_at TIMESTAMPTZ`, `resolved_at TIMESTAMPTZ NULL`.

### `duplicate_candidates`

`report_id UUID FK reports`, `candidate_report_id UUID FK reports`, `geo_distance_m NUMERIC`, `image_similarity NUMERIC(4,3) NULL`, `time_distance_hours NUMERIC`, `confidence NUMERIC(4,3)`, `decision ENUM(pending, merged, not_duplicate)`, `decided_by UUID FK users NULL`. Composite primary key: `(report_id, candidate_report_id)`.

### `wards`

`id UUID PK`, `name VARCHAR(100)`, `boundary GEOMETRY(MultiPolygon,4326)`, `source_url TEXT`, `updated_at TIMESTAMPTZ`.

### `weather_observations` and `flood_risk_predictions`

Observations store `observed_at`, `grid_cell`, `rainfall_mm`, `tide_m NULL`, and source. Predictions store `prediction_for`, `grid_cell`, `risk_level ENUM(low, medium, high)`, `risk_score NUMERIC(5,2)`, `model_version`, and `feature_snapshot JSONB`.

### `audit_events`

Append-only history: `id`, `actor_id`, `entity_type`, `entity_id`, `action`, `previous_value JSONB`, `new_value JSONB`, `created_at`.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/v1/uploads/sign` | Signed media-upload URL |
| POST | `/v1/reports` | Create report |
| GET | `/v1/reports/{id}` | Report plus AI analysis |
| GET | `/v1/incidents` | Map/list with filters |
| POST | `/v1/reports/{id}/verify` | Moderator verification |
| POST | `/v1/incidents/{id}/status` | Status update + audit event |
| GET | `/v1/analytics/hotspots` | Clustered statistics |
| GET | `/v1/risk/waterlogging` | Forecast/current risk grid |
| POST | `/v1/reports/{id}/complaint` | Editable complaint draft |

## Critical decisions

- Query candidate duplicates with PostGIS `ST_DWithin`, then compare embeddings to control cost.
- Inference results are immutable; reports/incidents are derived and can change after review.
- Separate private exact locations/original media from public map/media derivatives.
- Use a transparent rules-based priority baseline before training priority models.
- Version datasets, models, prompts/templates, and forecast features from day one.

## Build order

1. Schema, auth, signed uploads, manual pin.
2. Three-class image detector + moderator review.
3. Map, incidents, duplicate clustering, explainable priority, workflow.
4. Dataset/evaluation/model card, deployment, demo video.
5. Video, remaining classes, translations, waterlogging forecast.
