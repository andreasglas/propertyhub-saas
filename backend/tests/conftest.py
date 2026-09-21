import pytest
from fastapi.testclient import TestClient

from app.main import app


def create_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def client() -> TestClient:
    return create_client()
