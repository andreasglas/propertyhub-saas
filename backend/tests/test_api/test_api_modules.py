from fastapi.testclient import TestClient


from app.api.v1.endpoints import auth


def test_properties_endpoint_is_available(client: TestClient) -> None:
    response = client.get("/api/v1/properties/")

    assert response.status_code == 200
    assert response.json()["module"] == "properties"


def test_auth_endpoint_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_auth_endpoint_returns_token_for_valid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "test-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_auth_endpoint_requires_bootstrap_configuration(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(auth.settings, "bootstrap_admin_email", None)
    monkeypatch.setattr(auth.settings, "bootstrap_admin_password", None)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "test-password"},
    )

    assert response.status_code == 503
