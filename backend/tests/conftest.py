import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "propertyhub-test-secret-key-000000")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "test-password")

from app.main import app


def create_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def client() -> TestClient:
    return create_client()
