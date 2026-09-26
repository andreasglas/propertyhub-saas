from fastapi.testclient import TestClient
from io import BytesIO

from app.core.security import get_password_hash
from app.db.models.property import Property
from app.db.models.tenant import Tenant
from app.db.models.unit import Unit
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


def test_auth_me_returns_authenticated_user(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "admin@example.com"
    assert payload["role"] == "owner"
    assert payload["is_active"] is True


def test_viewer_role_is_read_only(
    client: TestClient,
    auth_headers: dict[str, str],
    viewer_auth_headers: dict[str, str],
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Viewer Test Objekt",
            "property_type": "residential",
            "street": "Viewerstraße 1",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 250000,
        },
    )
    assert property_response.status_code == 201

    read_response = client.get("/api/v1/properties/", headers=viewer_auth_headers)
    assert read_response.status_code == 200
    assert len(read_response.json()) == 1

    create_response = client.post(
        "/api/v1/properties/",
        headers=viewer_auth_headers,
        json={
            "name": "Nicht erlaubt",
            "property_type": "residential",
            "street": "Viewerstraße 2",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 260000,
        },
    )
    assert create_response.status_code == 403

    import_response = client.post(
        "/api/v1/banking/import-stub",
        headers=viewer_auth_headers,
    )
    assert import_response.status_code == 403


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


def test_contracts_crud_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Contract Haus",
            "property_type": "residential",
            "street": "Vertragsweg 2",
            "postal_code": "80331",
            "city": "München",
            "purchase_price": 950000,
        },
    )
    property_id = property_response.json()["id"]

    unit_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Wohnung 2B",
            "unit_type": "apartment",
            "status": "vacant",
            "area_sqm": 68.0,
        },
    )
    tenant_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Anna",
            "last_name": "Mieterin",
            "email": "anna@example.com",
            "phone": "+49301234567",
            "move_in_date": "2026-03-01",
            "move_out_date": None,
        },
    )
    unit_id = unit_response.json()["id"]
    tenant_id = tenant_response.json()["id"]

    create_response = client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_id,
            "tenant_id": tenant_id,
            "start_date": "2026-04-01",
            "end_date": None,
            "cold_rent": 1250,
            "service_charge_advance": 280,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    contract_id = created["id"]
    assert created["unit_id"] == unit_id
    assert created["tenant_id"] == tenant_id

    list_response = client.get("/api/v1/contracts/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(
        f"/api/v1/contracts/{contract_id}", headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["cold_rent"] == 1250

    update_response = client.put(
        f"/api/v1/contracts/{contract_id}",
        headers=auth_headers,
        json={
            "unit_id": unit_id,
            "tenant_id": tenant_id,
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
            "cold_rent": 1290,
            "service_charge_advance": 300,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["end_date"] == "2027-03-31"
    assert update_response.json()["service_charge_advance"] == 300

    delete_response = client.delete(
        f"/api/v1/contracts/{contract_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204


def test_contract_creation_requires_unit_and_tenant_in_same_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SessionLocal() as db:
        foreign_property = Property(
            organization_id="00000000-0000-0000-0000-000000000099",
            name="Fremdobjekt",
            property_type="residential",
            street="Außen 8",
            postal_code="11111",
            city="Extern",
        )
        db.add(foreign_property)
        db.flush()

        foreign_unit = Unit(
            organization_id="00000000-0000-0000-0000-000000000099",
            property_id=foreign_property.id,
            name="Unit Fremd",
            unit_type="apartment",
            status="vacant",
        )
        foreign_tenant = Tenant(
            organization_id="00000000-0000-0000-0000-000000000099",
            first_name="Fremd",
            last_name="Mieter",
            email="fremd@example.com",
        )
        db.add_all([foreign_unit, foreign_tenant])
        db.commit()
        db.refresh(foreign_unit)
        db.refresh(foreign_tenant)

        foreign_unit_id = foreign_unit.id
        foreign_tenant_id = foreign_tenant.id

    response = client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": foreign_unit_id,
            "tenant_id": foreign_tenant_id,
            "start_date": "2026-04-01",
            "end_date": None,
            "cold_rent": 1000,
            "service_charge_advance": 200,
        },
    )
    assert response.status_code == 404


def test_contracts_are_scoped_to_authenticated_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Scope Haus",
            "property_type": "residential",
            "street": "Scope 1",
            "postal_code": "50667",
            "city": "Köln",
            "purchase_price": 600000,
        },
    )
    property_id = property_response.json()["id"]
    unit_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Scope Unit",
            "unit_type": "apartment",
            "status": "vacant",
            "area_sqm": 60,
        },
    )
    tenant_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Scope",
            "last_name": "Tenant",
            "email": "scope@example.com",
            "phone": "+4930555555",
            "move_in_date": "2026-05-01",
            "move_out_date": None,
        },
    )
    create_response = client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_response.json()["id"],
            "tenant_id": tenant_response.json()["id"],
            "start_date": "2026-06-01",
            "end_date": None,
            "cold_rent": 1100,
            "service_charge_advance": 250,
        },
    )
    contract_id = create_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="contract-scope@example.com",
                full_name="Contract Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "contract-scope@example.com", "password": "scope-password"},
    )
    other_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }

    list_response = client.get("/api/v1/contracts/", headers=other_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(
        f"/api/v1/contracts/{contract_id}", headers=other_headers
    )
    assert detail_response.status_code == 404


def test_contract_end_date_must_not_precede_start_date(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Date Haus",
            "property_type": "residential",
            "street": "Datum 1",
            "postal_code": "04109",
            "city": "Leipzig",
            "purchase_price": 400000,
        },
    )
    unit_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_response.json()["id"],
            "name": "Date Unit",
            "unit_type": "apartment",
            "status": "vacant",
            "area_sqm": 50,
        },
    )
    tenant_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Datum",
            "last_name": "Test",
            "email": "datum@example.com",
            "phone": "+49123400000",
            "move_in_date": "2026-06-01",
            "move_out_date": None,
        },
    )

    response = client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_response.json()["id"],
            "tenant_id": tenant_response.json()["id"],
            "start_date": "2026-06-15",
            "end_date": "2026-06-01",
            "cold_rent": 950,
            "service_charge_advance": 180,
        },
    )
    assert response.status_code == 422


def test_invoices_crud_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Invoice Haus",
            "property_type": "residential",
            "street": "Rechnungsgasse 5",
            "postal_code": "20095",
            "city": "Hamburg",
            "purchase_price": 720000,
        },
    )
    property_id = property_response.json()["id"]

    create_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "vendor_name": "Stadtwerke Hamburg",
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-07-01",
            "gross_amount": 325.5,
            "status": "received",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    invoice_id = created["id"]
    assert created["vendor_name"] == "Stadtwerke Hamburg"

    list_response = client.get("/api/v1/invoices/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(
        f"/api/v1/invoices/{invoice_id}", headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["gross_amount"] == 325.5

    update_response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "vendor_name": "Stadtwerke Hamburg",
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-07-01",
            "gross_amount": 349.9,
            "status": "approved",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "approved"

    delete_response = client.delete(
        f"/api/v1/invoices/{invoice_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204


def test_invoice_creation_requires_property_in_same_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SessionLocal() as db:
        foreign_property = Property(
            organization_id="00000000-0000-0000-0000-000000000099",
            name="Fremdes Rechnungsobjekt",
            property_type="residential",
            street="Extern 11",
            postal_code="99999",
            city="Extern",
        )
        db.add(foreign_property)
        db.commit()
        db.refresh(foreign_property)
        foreign_property_id = foreign_property.id

    response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": foreign_property_id,
            "vendor_name": "Fremdlieferant",
            "invoice_number": "INV-X",
            "invoice_date": "2026-07-01",
            "gross_amount": 99,
            "status": "received",
        },
    )
    assert response.status_code == 404


def test_payments_crud_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Payment Haus",
            "property_type": "residential",
            "street": "Zahlungsweg 4",
            "postal_code": "50667",
            "city": "Köln",
            "purchase_price": 610000,
        },
    )
    property_id = property_response.json()["id"]
    unit_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Payment Unit",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 63,
        },
    )
    tenant_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Peter",
            "last_name": "Zahler",
            "email": "peter@example.com",
            "phone": "+49221123456",
            "move_in_date": "2026-08-01",
            "move_out_date": None,
        },
    )
    contract_response = client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_response.json()["id"],
            "tenant_id": tenant_response.json()["id"],
            "start_date": "2026-08-01",
            "end_date": None,
            "cold_rent": 1150,
            "service_charge_advance": 240,
        },
    )
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "vendor_name": "Versicherung AG",
            "invoice_number": "INV-2026-900",
            "invoice_date": "2026-08-15",
            "gross_amount": 480,
            "status": "received",
        },
    )

    create_response = client.post(
        "/api/v1/payments/",
        headers=auth_headers,
        json={
            "invoice_id": invoice_response.json()["id"],
            "contract_id": contract_response.json()["id"],
            "amount": 480,
            "booking_date": "2026-08-20",
            "reference": "SEPA-2026-08",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    payment_id = created["id"]
    assert created["reference"] == "SEPA-2026-08"

    list_response = client.get("/api/v1/payments/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(
        f"/api/v1/payments/{payment_id}", headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["amount"] == 480

    update_response = client.put(
        f"/api/v1/payments/{payment_id}",
        headers=auth_headers,
        json={
            "invoice_id": invoice_response.json()["id"],
            "contract_id": contract_response.json()["id"],
            "amount": 500,
            "booking_date": "2026-08-21",
            "reference": "SEPA-2026-08-UPD",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == 500

    delete_response = client.delete(
        f"/api/v1/payments/{payment_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204


def test_payment_requires_reference_to_invoice_or_contract(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/payments/",
        headers=auth_headers,
        json={
            "invoice_id": None,
            "contract_id": None,
            "amount": 100,
            "booking_date": "2026-08-20",
            "reference": "INVALID",
        },
    )
    assert response.status_code == 422


def test_payments_are_scoped_to_authenticated_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Scoped Payment Haus",
            "property_type": "residential",
            "street": "Scope Zahlung 1",
            "postal_code": "01067",
            "city": "Dresden",
            "purchase_price": 550000,
        },
    )
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": property_response.json()["id"],
            "vendor_name": "Scoped Lieferant",
            "invoice_number": "INV-SCOPE-1",
            "invoice_date": "2026-09-01",
            "gross_amount": 150,
            "status": "received",
        },
    )
    create_response = client.post(
        "/api/v1/payments/",
        headers=auth_headers,
        json={
            "invoice_id": invoice_response.json()["id"],
            "contract_id": None,
            "amount": 150,
            "booking_date": "2026-09-02",
            "reference": "SCOPE-PAY",
        },
    )
    payment_id = create_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="payment-scope@example.com",
                full_name="Payment Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "payment-scope@example.com", "password": "scope-password"},
    )
    other_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }

    list_response = client.get("/api/v1/payments/", headers=other_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(
        f"/api/v1/payments/{payment_id}", headers=other_headers
    )
    assert detail_response.status_code == 404


def test_accounting_entries_crud_flow(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Accounting Haus",
            "property_type": "residential",
            "street": "Buchungsgasse 7",
            "postal_code": "70173",
            "city": "Stuttgart",
            "purchase_price": 730000,
        },
    )
    property_id = property_response.json()["id"]

    create_response = client.post(
        "/api/v1/accounting/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "entry_type": "expense",
            "category": "insurance",
            "amount": 210.75,
            "booking_date": "2026-10-01",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    entry_id = created["id"]
    assert created["entry_type"] == "expense"

    list_response = client.get("/api/v1/accounting/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(
        f"/api/v1/accounting/{entry_id}", headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["amount"] == 210.75

    update_response = client.put(
        f"/api/v1/accounting/{entry_id}",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "entry_type": "expense",
            "category": "maintenance",
            "amount": 245.0,
            "booking_date": "2026-10-02",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["category"] == "maintenance"

    delete_response = client.delete(
        f"/api/v1/accounting/{entry_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204


def test_accounting_entry_requires_property_in_same_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SessionLocal() as db:
        foreign_property = Property(
            organization_id="00000000-0000-0000-0000-000000000099",
            name="Fremdes Buchungsobjekt",
            property_type="residential",
            street="Extern 15",
            postal_code="99999",
            city="Extern",
        )
        db.add(foreign_property)
        db.commit()
        db.refresh(foreign_property)
        foreign_property_id = foreign_property.id

    response = client.post(
        "/api/v1/accounting/",
        headers=auth_headers,
        json={
            "property_id": foreign_property_id,
            "entry_type": "expense",
            "category": "tax",
            "amount": 100,
            "booking_date": "2026-10-03",
        },
    )
    assert response.status_code == 404


def test_accounting_entries_are_scoped_to_authenticated_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Scoped Accounting Haus",
            "property_type": "residential",
            "street": "Scope Buchung 3",
            "postal_code": "01067",
            "city": "Dresden",
            "purchase_price": 510000,
        },
    )
    create_response = client.post(
        "/api/v1/accounting/",
        headers=auth_headers,
        json={
            "property_id": property_response.json()["id"],
            "entry_type": "income",
            "category": "rent",
            "amount": 1300,
            "booking_date": "2026-10-04",
        },
    )
    entry_id = create_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="accounting-scope@example.com",
                full_name="Accounting Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "accounting-scope@example.com", "password": "scope-password"},
    )
    other_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }

    list_response = client.get("/api/v1/accounting/", headers=other_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(
        f"/api/v1/accounting/{entry_id}", headers=other_headers
    )
    assert detail_response.status_code == 404


def test_reports_dashboard_summary_returns_aggregated_metrics(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Reporting Haus",
            "property_type": "residential",
            "street": "Reportweg 12",
            "postal_code": "60311",
            "city": "Frankfurt",
            "purchase_price": 810000,
        },
    )
    property_id = property_response.json()["id"]

    unit_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Report Unit",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 71,
        },
    )
    tenant_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Report",
            "last_name": "Tenant",
            "email": "report@example.com",
            "phone": "+4969123456",
            "move_in_date": "2026-11-01",
            "move_out_date": None,
        },
    )
    contract_response = client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_response.json()["id"],
            "tenant_id": tenant_response.json()["id"],
            "start_date": "2026-11-01",
            "end_date": None,
            "cold_rent": 1400,
            "service_charge_advance": 300,
        },
    )
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "vendor_name": "Report Energie",
            "invoice_number": "REP-001",
            "invoice_date": "2026-11-02",
            "gross_amount": 420,
            "status": "received",
        },
    )
    client.post(
        "/api/v1/payments/",
        headers=auth_headers,
        json={
            "invoice_id": invoice_response.json()["id"],
            "contract_id": contract_response.json()["id"],
            "amount": 420,
            "booking_date": "2026-11-03",
            "reference": "REPORT-PAY",
        },
    )
    client.post(
        "/api/v1/accounting/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "entry_type": "income",
            "category": "rent",
            "amount": 1400,
            "booking_date": "2026-11-05",
        },
    )
    client.post(
        "/api/v1/accounting/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "entry_type": "expense",
            "category": "heating",
            "amount": 220,
            "booking_date": "2026-11-06",
        },
    )

    response = client.get("/api/v1/reports/", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["properties_count"] == 1
    assert payload["units_count"] == 1
    assert payload["tenants_count"] == 1
    assert payload["contracts_count"] == 1
    assert payload["invoices_count"] == 1
    assert payload["open_invoices_count"] == 1
    assert payload["payments_count"] == 1
    assert payload["accounting_entries_count"] == 2
    assert payload["total_invoice_amount"] == 420
    assert payload["total_payment_amount"] == 420
    assert payload["total_income_amount"] == 1400
    assert payload["total_expense_amount"] == 220


def test_reports_dashboard_summary_is_organization_scoped(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Scope Report Haus",
            "property_type": "residential",
            "street": "Scope 22",
            "postal_code": "90402",
            "city": "Nürnberg",
            "purchase_price": 500000,
        },
    )
    client.post(
        "/api/v1/accounting/",
        headers=auth_headers,
        json={
            "property_id": property_response.json()["id"],
            "entry_type": "income",
            "category": "rent",
            "amount": 1000,
            "booking_date": "2026-11-07",
        },
    )

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="report-scope@example.com",
                full_name="Report Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "report-scope@example.com", "password": "scope-password"},
    )
    other_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }

    response = client.get("/api/v1/reports/", headers=other_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["properties_count"] == 0
    assert payload["accounting_entries_count"] == 0
    assert payload["total_income_amount"] == 0


def test_banking_transactions_crud_and_import_stub(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    import_response = client.post("/api/v1/banking/import-stub", headers=auth_headers)
    assert import_response.status_code == 200
    imported = import_response.json()
    assert imported["imported_count"] == 2
    assert len(imported["transactions"]) == 2

    create_response = client.post(
        "/api/v1/banking/transactions",
        headers=auth_headers,
        json={
            "payment_id": None,
            "external_id": "manual-001",
            "account_name": "Geschäftskonto",
            "transaction_type": "credit",
            "booking_date": "2026-07-20",
            "value_date": "2026-07-20",
            "amount": 1200,
            "currency": "EUR",
            "counterparty_name": "Mieterin Beispiel",
            "iban": "DE44500105175407324931",
            "reference": "Miete Juli",
            "status": "manual",
        },
    )
    assert create_response.status_code == 201
    transaction = create_response.json()
    transaction_id = transaction["id"]
    assert transaction["organization_id"] == "00000000-0000-0000-0000-000000000001"

    list_response = client.get("/api/v1/banking/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 3

    get_response = client.get(
        f"/api/v1/banking/transactions/{transaction_id}", headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["reference"] == "Miete Juli"

    update_response = client.put(
        f"/api/v1/banking/transactions/{transaction_id}",
        headers=auth_headers,
        json={
            "payment_id": None,
            "external_id": "manual-001",
            "account_name": "Geschäftskonto",
            "transaction_type": "credit",
            "booking_date": "2026-07-21",
            "value_date": "2026-07-21",
            "amount": 1250,
            "currency": "EUR",
            "counterparty_name": "Mieterin Beispiel",
            "iban": "DE44500105175407324931",
            "reference": "Miete Juli korrigiert",
            "status": "matched",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == 1250
    assert update_response.json()["status"] == "matched"

    delete_response = client.delete(
        f"/api/v1/banking/transactions/{transaction_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204


def test_banking_transactions_are_scoped_to_authenticated_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create_response = client.post(
        "/api/v1/banking/transactions",
        headers=auth_headers,
        json={
            "payment_id": None,
            "external_id": "org-a-001",
            "account_name": "Geschäftskonto",
            "transaction_type": "credit",
            "booking_date": "2026-08-01",
            "value_date": "2026-08-01",
            "amount": 850,
            "currency": "EUR",
            "counterparty_name": "Org A Mieter",
            "iban": "DE44500105175407324931",
            "reference": "Augustmiete",
            "status": "imported",
        },
    )
    assert create_response.status_code == 201
    transaction_id = create_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="banking-scope@example.com",
                full_name="Banking Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "banking-scope@example.com", "password": "scope-password"},
    )
    other_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }

    list_response = client.get("/api/v1/banking/", headers=other_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(
        f"/api/v1/banking/transactions/{transaction_id}", headers=other_headers
    )
    assert detail_response.status_code == 404


def test_banking_transaction_can_be_matched_to_payment(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    tenant_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Bank",
            "last_name": "Matcher",
            "email": "bank-matcher@example.com",
            "phone": "+49111111111",
            "move_in_date": "2026-01-01",
            "move_out_date": None,
        },
    )
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Matching Haus",
            "property_type": "residential",
            "street": "Abgleich 1",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 600000,
        },
    )
    unit_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_response.json()["id"],
            "name": "Wohnung A",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 65,
        },
    )
    contract_response = client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_response.json()["id"],
            "tenant_id": tenant_response.json()["id"],
            "start_date": "2026-01-01",
            "end_date": None,
            "cold_rent": 950,
            "service_charge_advance": 180,
        },
    )
    assert contract_response.status_code == 201
    payment_response = client.post(
        "/api/v1/payments/",
        headers=auth_headers,
        json={
            "invoice_id": None,
            "contract_id": contract_response.json()["id"],
            "amount": 950,
            "booking_date": "2026-08-05",
            "reference": "Miete August",
        },
    )
    assert payment_response.status_code == 201

    transaction_response = client.post(
        "/api/v1/banking/transactions",
        headers=auth_headers,
        json={
            "payment_id": None,
            "external_id": "match-001",
            "account_name": "Geschäftskonto",
            "transaction_type": "credit",
            "booking_date": "2026-08-05",
            "value_date": "2026-08-05",
            "amount": 950,
            "currency": "EUR",
            "counterparty_name": "Bank Matcher",
            "iban": "DE44500105175407324931",
            "reference": "Miete August",
            "status": "imported",
        },
    )
    assert transaction_response.status_code == 201
    transaction_id = transaction_response.json()["id"]

    match_response = client.post(
        f"/api/v1/banking/transactions/{transaction_id}/match-payment",
        headers=auth_headers,
        json={"payment_id": payment_response.json()["id"]},
    )
    assert match_response.status_code == 200
    matched_transaction = match_response.json()
    assert matched_transaction["payment_id"] == payment_response.json()["id"]
    assert matched_transaction["status"] == "matched"


def test_documents_upload_and_process_ocr(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": None,
            "vendor_name": "Initial Vendor",
            "invoice_number": None,
            "invoice_date": None,
            "gross_amount": 100,
            "status": "received",
        },
    )
    assert invoice_response.status_code == 201
    invoice_id = invoice_response.json()["id"]

    upload_response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        data={
            "related_model": "invoice",
            "related_id": invoice_id,
            "document_type": "invoice_receipt",
        },
        files={
            "file": (
                "invoice-acme.txt",
                BytesIO(
                    b"Vendor: ACME GmbH\nInvoice Number: INV-2026-001\nInvoice Date: 2026-09-26\nGross Amount: 420.50\n"
                ),
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    document = upload_response.json()
    assert document["ocr_status"] == "pending"
    document_id = document["id"]

    list_response = client.get("/api/v1/documents/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    ocr_response = client.post(
        f"/api/v1/documents/{document_id}/process-ocr",
        headers=auth_headers,
    )
    assert ocr_response.status_code == 200
    processed_document = ocr_response.json()["document"]
    assert processed_document["ocr_status"] == "processed"
    assert processed_document["ocr_result"]["vendor_name"] == "ACME GmbH"
    assert processed_document["ocr_result"]["invoice_number"] == "INV-2026-001"
    assert processed_document["ocr_result"]["gross_amount"] == 420.5


def test_documents_are_scoped_and_viewer_cannot_upload(
    client: TestClient,
    auth_headers: dict[str, str],
    viewer_auth_headers: dict[str, str],
) -> None:
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": None,
            "vendor_name": "Doc Scope Vendor",
            "invoice_number": None,
            "invoice_date": None,
            "gross_amount": 120,
            "status": "received",
        },
    )
    invoice_id = invoice_response.json()["id"]

    upload_response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        data={
            "related_model": "invoice",
            "related_id": invoice_id,
            "document_type": "invoice_receipt",
        },
        files={
            "file": (
                "scope.txt",
                BytesIO(b"Vendor: Scope GmbH"),
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]

    viewer_list_response = client.get("/api/v1/documents/", headers=viewer_auth_headers)
    assert viewer_list_response.status_code == 200
    assert len(viewer_list_response.json()) == 1

    viewer_upload_response = client.post(
        "/api/v1/documents/upload",
        headers=viewer_auth_headers,
        data={
            "related_model": "invoice",
            "related_id": invoice_id,
            "document_type": "invoice_receipt",
        },
        files={
            "file": (
                "viewer.txt",
                BytesIO(b"Vendor: Viewer GmbH"),
                "text/plain",
            )
        },
    )
    assert viewer_upload_response.status_code == 403

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="document-scope@example.com",
                full_name="Document Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "document-scope@example.com", "password": "scope-password"},
    )
    other_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }
    other_detail_response = client.get(
        f"/api/v1/documents/{document_id}", headers=other_headers
    )
    assert other_detail_response.status_code == 404
