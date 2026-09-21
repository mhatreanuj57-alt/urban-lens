"""Tests for complaint template drafting — no fabrication of facts."""

from datetime import datetime, timezone
from uuid import uuid4

from app.services.complaints import draft_complaint


def make_report():
    from app.models.report import Report

    return Report(
        id=uuid4(),
        reporter_id=uuid4(),
        issue_type="pothole",
        description="Deep pothole near the bus stop",
        landmark="Vashi Sector 9 bus stop",
        public_latitude=19.077,
        public_longitude=72.999,
        occurred_at=datetime(2026, 9, 18, 8, 30, tzinfo=timezone.utc),
        submitted_at=datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc),
    )


def test_english_draft_contains_only_confirmed_facts():
    report = make_report()
    draft = draft_complaint(report, "Priya Sharma", "en")
    assert "pothole" in draft["subject"].lower()
    assert "Vashi Sector 9 bus stop" in draft["body"]
    assert "19.077" in draft["body"]
    assert "Deep pothole near the bus stop" in draft["body"]
    assert "Priya Sharma" in draft["body"]


def test_marathi_and_hindi_drafts_render():
    report = make_report()
    for lang in ("hi", "mr"):
        draft = draft_complaint(report, "Priya", lang)
        assert draft["subject"] and draft["body"]
        assert "Vashi Sector 9 bus stop" in draft["body"]


def test_unknown_language_falls_back_to_english():
    report = make_report()
    draft = draft_complaint(report, None, "fr")
    assert "Complaint" in draft["subject"]


def test_missing_location_hides_coords():
    from app.models.report import Report

    report = make_report()
    report.public_latitude = None
    report.public_longitude = None
    draft = draft_complaint(report, None, "en")
    assert "not disclosed" in draft["body"]
