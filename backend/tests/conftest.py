"""Test configuration."""

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
