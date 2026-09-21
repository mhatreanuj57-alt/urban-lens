"""API integration tests — auth flow, report lifecycle, RBAC.

Runs against the local development database (skipped when unavailable).
"""

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_DB_TESTS") == "1",
    reason="Database not available",
)


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@urbanlens.dev"


def test_register_login_me(client):
    email = _unique_email()
    r = client.post("/v1/auth/register", json={
        "email": email, "password": "strongpass123", "display_name": "Test User",
    })
    assert r.status_code == 201, r.text
    assert r.json()["role"] == "citizen"

    r = client.post("/v1/auth/token", data={
        "username": email, "password": "strongpass123",
    })
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_me_requires_token(client):
    assert client.get("/v1/auth/me").status_code == 401


def test_register_duplicate_email(client):
    email = _unique_email()
    payload = {"email": email, "password": "strongpass123"}
    assert client.post("/v1/auth/register", json=payload).status_code == 201
    r = client.post("/v1/auth/register", json=payload)
    assert r.status_code == 400


def test_report_requires_auth(client):
    r = client.post("/v1/reports/", json={
        "issue_type": "pothole", "latitude": 19.07, "longitude": 73.0,
        "consent_location": True, "media": [{"object_key": "x"}],
    })
    assert r.status_code == 401


def test_report_location_validation(client):
    email = _unique_email()
    client.post("/v1/auth/register", json={
        "email": email, "password": "strongpass123"})
    token = client.post("/v1/auth/token", data={
        "username": email, "password": "strongpass123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Outside the Navi Mumbai bounding box
    r = client.post("/v1/reports/", headers=headers, json={
        "issue_type": "pothole", "latitude": 12.0, "longitude": 77.0,
        "consent_location": True, "media": [{"object_key": "k"}],
    })
    assert r.status_code == 422

    # Missing consent
    r = client.post("/v1/reports/", headers=headers, json={
        "issue_type": "pothole", "latitude": 19.07, "longitude": 73.0,
        "consent_location": False, "media": [{"object_key": "k"}],
    })
    assert r.status_code == 422

    # Nonexistent media object
    r = client.post("/v1/reports/", headers=headers, json={
        "issue_type": "pothole", "latitude": 19.07, "longitude": 73.0,
        "consent_location": True,
        "media": [{"object_key": f"missing-{uuid.uuid4().hex}.jpg"}],
    })
    assert r.status_code == 400


def test_public_listings_available_anonymously(client):
    assert client.get("/v1/reports/?limit=3").status_code == 200
    assert client.get("/v1/incidents/?limit=3").status_code == 200
    assert client.get("/v1/analytics/summary").status_code == 200
    assert client.get("/v1/analytics/hotspots?days=30").status_code == 200
    r = client.get("/v1/risk/waterlogging?lat=19.03&lng=73.04")
    assert r.status_code == 200
    assert r.json()["risk_level"] in ("low", "medium", "high")


def test_verify_requires_moderator(client):
    email = _unique_email()
    client.post("/v1/auth/register", json={
        "email": email, "password": "strongpass123"})
    token = client.post("/v1/auth/token", data={
        "username": email, "password": "strongpass123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    incidents = client.get("/v1/incidents/?limit=1").json()
    assert incidents
    r = client.post(f"/v1/incidents/{incidents[0]['id']}/status", headers=headers,
                    json={"lifecycle_status": "assigned"})
    assert r.status_code == 403

