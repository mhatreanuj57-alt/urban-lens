# UrbanLens AI — Product Requirements Document

## Product summary

UrbanLens AI is a civic-intelligence platform for Navi Mumbai. Citizens submit road photos or short videos; AI turns them into structured reports, maps recurring issues, and helps an operations team prioritise response. It is decision support, never a replacement for an official inspection.

## Problem

Civic issues are reported with incomplete descriptions, imprecise locations, duplicates, and no consistent urgency signal. Residents cannot easily know whether an issue already exists in the system, while civic teams must manually turn unstructured media into a work queue.

## What we are building

### Citizen workflow

1. User signs in and uploads a photo or short video.
2. GPS metadata is read when available; otherwise the user drops a map pin and adds a landmark.
3. Computer vision suggests one or more labels: `pothole`, `garbage`, `damaged_streetlight`, `waterlogging`, and `illegal_dumping`.
4. User reviews the suggestion and submits the report.
5. The app detects likely duplicates, shows the report on a map, and lets the user track status.
6. The user can export an editable structured complaint in English, Hindi, or Marathi.

### Operations dashboard

- Map and prioritised queue of reports/incidents.
- Nearby, visually similar reports grouped as one incident.
- Explainable priority score based on severity, confirmations, recency, risk context, and road context.
- Verification, assignment, status updates, before/after proof, and resolution-time tracking.
- Hotspots, ward trends, issue mix, and SLA analytics.

### Waterlogging-risk module

Combine rainfall, tide data where available, recent verified waterlogging reports, and location features to estimate `low`, `medium`, or `high` risk by map cell. This is a demonstration feature, not an emergency warning system.

## Who it is for

| User | Need | Value |
| --- | --- | --- |
| Navi Mumbai residents/commuters | Report issues quickly | Clear, reusable complaint and status tracking |
| Resident groups/volunteers | Find recurring local issues | Evidence-rich hotspots and ward trends |
| Civic operations staff (demo persona) | Triage public reports | Deduplicated, prioritised work queue |
| Researchers/journalists | Understand patterns | Privacy-aware aggregated data |

## Goals and success metrics

- A reviewed report can be submitted in under 90 seconds.
- Initial custom detector reaches at least 0.70 mAP@50, with per-class metrics published.
- At least 75% duplicate recall within a manually labelled evaluation set (100 metres and 14 days).
- Standard API response under 3 seconds, excluding video processing.
- Publish a locally collected, consented/appropriately licensed dataset plus model card.

## Non-goals for v1

- Direct NMMC/BMC system integration.
- Automated dispatch, fines, or official verification.
- Face or number-plate recognition.
- Safety-critical flood alerts.

## Functional requirements

### FR-1: roles

Roles are `citizen`, `moderator`, and `admin`. Citizens edit their own unverified reports; moderators/admins manage verification and workflow.

### FR-2: submission

- Accept JPG, PNG, WebP, MP4, and MOV.
- Store original media privately; strip EXIF from public derivatives.
- Read GPS when present and allow manual correction.
- Require issue-type confirmation, location, and consent.

### FR-3: AI analysis

- Detect five v1 issue classes.
- Store model version, confidence, bounding boxes, and annotated preview.
- For video, sample frames and merge matching detections.
- Clearly label low-confidence results as “needs review.”

### FR-4: duplication and priority

- Find candidates by issue type, distance, time, and image-embedding similarity.
- Allow moderators to merge/unmerge incidents.
- Explain all factors contributing to priority.

### FR-5: map and workflow

- Public map uses privacy-safe location precision.
- States: `submitted → under_review → verified → assigned → in_progress → resolved → rejected`.
- Before/after media and append-only audit history.
- Filters: date, ward, issue type, status, priority.

### FR-6: complaint drafting

- Generate factual, editable drafts from confirmed data only.
- English first; Hindi/Marathi use reviewed templates.
- Never fabricate agency, location, urgency, or resolution details.

## Priority score

`priority = 0.35 × severity + 0.25 × confirmations + 0.20 × recency + 0.10 × risk_context + 0.10 × road_context`

Every component is normalised to 0–100 and visible in the UI. Road context is manually curated in v1 (e.g. near a school, hospital, or junction); do not make unsupported traffic claims.

## Privacy, safety, and ethics

- Blur faces and number plates in public media.
- Preserve originals only for authorised moderation.
- Obtain upload/location consent; training consent defaults to false.
- Provide account/report deletion.
- Reduce map precision in public views when appropriate.
- Publish confidence, limitations, and a correction pathway.

## Release plan

### MVP (6–8 weeks)

Image upload, manual pin, three classes (`pothole`, `garbage`, `waterlogging`), YOLO inference, map, report workflow, basic admin queue, and a 300–500 image local dataset.

### V1

Video support, five classes, duplicate clustering, multilingual complaint export, hotspot analytics, before/after evidence, a model card, and a public demo.

### V2

Forecasting, resident-group portal, subscriptions, and data partnerships.

## Demo narrative

“A commuter uploads a pothole photo near a Navi Mumbai junction. UrbanLens blurs a visible number plate, detects a pothole, maps it, finds nearby confirmations, explains the priority, and drafts an editable Marathi complaint. A moderator verifies and assigns the incident, then adds a repaired-road photo.”
