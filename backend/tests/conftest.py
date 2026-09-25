import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_propertyhub.db")
os.environ.setdefault("SECRET_KEY", "propertyhub-test-secret-key-000000")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "test-password")
os.environ.setdefault(
    "BOOTSTRAP_ADMIN_ORGANIZATION_ID", "00000000-0000-0000-0000-000000000001"
)

from app.main import app
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.user_service import UserService


def create_client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        UserService().ensure_bootstrap_admin(db)


@pytest.fixture
def client() -> TestClient:
    return create_client()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "test-password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": "Bearer " + token}


@pytest.fixture
def viewer_auth_headers(client: TestClient) -> dict[str, str]:
    with SessionLocal() as db:
        viewer = UserService().get_user_by_email(db, "viewer@example.com")
        if viewer is None:
            from app.core.security import get_password_hash
            from app.db.models.user import User

            db.add(
                User(
                    organization_id="00000000-0000-0000-0000-000000000001",
                    email="viewer@example.com",
                    full_name="Viewer User",
                    hashed_password=get_password_hash("viewer-password"),
                    role="viewer",
                    is_active=True,
                )
            )
            db.commit()

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "viewer@example.com", "password": "viewer-password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": "Bearer " + token}
