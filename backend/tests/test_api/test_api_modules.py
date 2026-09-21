from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.models.property import Property
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


def test_units_crud_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Wohnanlage Köln",
            "property_type": "residential",
            "street": "Domplatz 1",
            "postal_code": "50667",
            "city": "Köln",
            "purchase_price": 800000,
        },
    )
    property_id = property_response.json()["id"]

    create_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Wohnung 1A",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 72.5,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    unit_id = created["id"]
    assert created["property_id"] == property_id

    list_response = client.get("/api/v1/units/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/units/{unit_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Wohnung 1A"

    update_response = client.put(
        f"/api/v1/units/{unit_id}",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Wohnung 1A renoviert",
            "unit_type": "apartment",
            "status": "vacant",
            "area_sqm": 74,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "vacant"

    delete_response = client.delete(f"/api/v1/units/{unit_id}", headers=auth_headers)
    assert delete_response.status_code == 204


def test_unit_creation_requires_property_in_same_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SessionLocal() as db:
        property_obj = Property(
            organization_id="00000000-0000-0000-0000-000000000099",
            name="Fremdes Objekt",
            property_type="residential",
            street="Fremdweg 9",
            postal_code="99999",
            city="Extern",
        )
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        foreign_property_id = property_obj.id

    response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": foreign_property_id,
            "name": "Unit X",
            "unit_type": "apartment",
            "status": "vacant",
            "area_sqm": 55,
        },
    )
    assert response.status_code == 404


def test_tenants_crud_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "max@example.com",
            "phone": "+49123456789",
            "move_in_date": "2026-01-01",
            "move_out_date": None,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    tenant_id = created["id"]
    assert created["email"] == "max@example.com"

    list_response = client.get("/api/v1/tenants/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/tenants/{tenant_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["first_name"] == "Max"

    update_response = client.put(
        f"/api/v1/tenants/{tenant_id}",
        headers=auth_headers,
        json={
            "first_name": "Maximilian",
            "last_name": "Mustermann",
            "email": "max@example.com",
            "phone": "+49111111111",
            "move_in_date": "2026-01-01",
            "move_out_date": None,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["phone"] == "+49111111111"

    delete_response = client.delete(
        f"/api/v1/tenants/{tenant_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204


def test_tenants_are_scoped_to_authenticated_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Erika",
            "last_name": "Musterfrau",
            "email": "erika@example.com",
            "phone": "+49222222222",
            "move_in_date": "2026-02-01",
            "move_out_date": None,
        },
    )
    tenant_id = create_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="tenant-scope@example.com",
                full_name="Tenant Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "tenant-scope@example.com", "password": "scope-password"},
    )
    other_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }

    list_response = client.get("/api/v1/tenants/", headers=other_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(
        f"/api/v1/tenants/{tenant_id}", headers=other_headers
    )
    assert detail_response.status_code == 404
