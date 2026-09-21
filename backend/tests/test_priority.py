"""Unit tests for the explainable priority score."""

from datetime import datetime, timedelta, timezone

from app.services.priority import (
    base_severity, compute_priority, confirmations_score, recency_score,
)


def test_base_severity_known_types():
    assert base_severity("waterlogging") == 80
    assert base_severity("pothole") == 70
    assert base_severity("garbage") == 50


def test_base_severity_scales_with_confidence():
    low = base_severity("pothole", 0.2)
    high = base_severity("pothole", 0.99)
    assert low < high <= 70


def test_recency_decay():
    now = datetime.now(timezone.utc)
    fresh = recency_score(now)
    old = recency_score(now - timedelta(days=28))
    assert fresh == 100
    assert 0 <= old < 10


def test_confirmations_cap():
    assert confirmations_score(0) == 0
    assert confirmations_score(1) == 30
    assert confirmations_score(6) == 100
    assert confirmations_score(50) == 100


def test_compute_priority_components():
    now = datetime.now(timezone.utc)
    score, factors = compute_priority(
        issue_type="pothole", report_count=2, submitted_at=now,
        risk_context=20, road_context=40,
    )
    assert 0 <= score <= 100
    assert set(factors) >= {"severity", "confirmations", "recency",
                            "risk_context", "road_context", "weights"}
    # Verify the documented weighted-sum identity
    w = factors["weights"]
    expected = (w["severity"] * factors["severity"]
                + w["confirmations"] * factors["confirmations"]
                + w["recency"] * factors["recency"]
                + w["risk_context"] * factors["risk_context"]
                + w["road_context"] * factors["road_context"])
    assert abs(score - expected) < 0.05


def test_more_confirmations_higher_priority():
    now = datetime.now(timezone.utc)
    single, _ = compute_priority("pothole", report_count=1, submitted_at=now)
    confirmed, _ = compute_priority("pothole", report_count=5, submitted_at=now)
    assert confirmed > single
