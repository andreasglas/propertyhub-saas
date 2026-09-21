from fastapi.testclient import TestClient


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
