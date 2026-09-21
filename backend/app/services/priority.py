"""Explainable priority scoring.

priority = 0.35*severity + 0.25*confirmations + 0.20*recency
         + 0.10*risk_context + 0.10*road_context
Every component is normalised to 0-100.
"""

from datetime import datetime, timezone

WEIGHTS = {
    "severity": 0.35,
    "confirmations": 0.25,
    "recency": 0.20,
    "risk_context": 0.10,
    "road_context": 0.10,
}

# v1 rules-based severity baseline per issue class (0-100)
BASE_SEVERITY = {
    "waterlogging": 80,
    "pothole": 70,
    "damaged_streetlight": 60,
    "illegal_dumping": 55,
    "garbage": 50,
}


def base_severity(issue_type: str, max_confidence: float | None = None) -> float:
    """Rules-based severity, optionally scaled by detection confidence."""
    severity = float(BASE_SEVERITY.get(issue_type, 50))
    if max_confidence is not None and max_confidence > 0:
        # Scale severity between 60% and 100% of the baseline by confidence
        severity *= 0.6 + 0.4 * min(max_confidence, 1.0)
    return round(severity, 2)


def recency_score(submitted_at: datetime, now: datetime | None = None) -> float:
    """100 for fresh reports, decaying to ~0 after 30 days."""
    now = now or datetime.now(timezone.utc)
    if submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=timezone.utc)
    days = max((now - submitted_at).total_seconds() / 86400.0, 0.0)
    return round(100 * (0.5 ** (days / 7.0)), 2)  # 7-day half-life


def confirmations_score(report_count: int) -> float:
    """1 report -> 30, +15 per extra confirmation, capped at 100."""
    if report_count <= 0:
        return 0.0
    return round(min(30 + 15 * (report_count - 1), 100), 2)


def compute_priority(
    issue_type: str,
    severity: float | None = None,
    report_count: int = 1,
    submitted_at: datetime | None = None,
    risk_context: float = 0.0,
    road_context: float = 0.0,
) -> tuple[float, dict]:
    """Return (priority_score, factors) with each factor visible in the UI."""
    severity = float(severity if severity is not None else base_severity(issue_type))
    confirmations = confirmations_score(report_count)
    recency = recency_score(submitted_at) if submitted_at else 50.0
    risk = float(min(max(risk_context, 0.0), 100.0))
    road = float(min(max(road_context, 0.0), 100.0))

    factors = {
        "severity": round(severity, 2),
        "confirmations": confirmations,
        "recency": recency,
        "risk_context": risk,
        "road_context": road,
        "weights": WEIGHTS,
    }
    score = (
        WEIGHTS["severity"] * severity
        + WEIGHTS["confirmations"] * confirmations
        + WEIGHTS["recency"] * recency
        + WEIGHTS["risk_context"] * risk
        + WEIGHTS["road_context"] * road
    )
    return round(score, 2), factors
