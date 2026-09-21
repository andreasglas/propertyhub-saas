from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.models.user import User
from app.db.session import SessionLocal


def test_properties_endpoint_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/properties/")

    assert response.status_code == 401


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


def test_properties_crud_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Musterhaus Berlin",
            "property_type": "residential",
            "street": "Musterstraße 1",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 450000,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Musterhaus Berlin"
    assert created["organization_id"] == "00000000-0000-0000-0000-000000000001"

    list_response = client.get("/api/v1/properties/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    property_id = created["id"]
    get_response = client.get(f"/api/v1/properties/{property_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["city"] == "Berlin"

    update_response = client.put(
        f"/api/v1/properties/{property_id}",
        headers=auth_headers,
        json={
            "name": "Musterhaus Berlin Mitte",
            "property_type": "residential",
            "street": "Musterstraße 1",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 470000,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["purchase_price"] == 470000

    delete_response = client.delete(
        f"/api/v1/properties/{property_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    final_list_response = client.get("/api/v1/properties/", headers=auth_headers)
    assert final_list_response.status_code == 200
    assert final_list_response.json() == []


def test_properties_are_scoped_to_authenticated_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Org A Objekt",
            "property_type": "residential",
            "street": "Ring 1",
            "postal_code": "20095",
            "city": "Hamburg",
            "purchase_price": 300000,
        },
    )
    assert create_response.status_code == 201
    property_id = create_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="other@example.com",
                full_name="Other User",
                hashed_password=get_password_hash("other-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "other@example.com", "password": "other-password"},
    )
    other_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }

    list_response = client.get("/api/v1/properties/", headers=other_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(
        f"/api/v1/properties/{property_id}", headers=other_headers
    )
    assert detail_response.status_code == 404
