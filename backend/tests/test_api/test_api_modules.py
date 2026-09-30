from fastapi.testclient import TestClient
from io import BytesIO
from datetime import date, timedelta
from unittest.mock import patch

from pypdf import PdfReader

from app.ml.invoice_ocr import extract_invoice_metadata
from app.tasks.document_tasks import process_document_ocr_job
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
    assert payload["organization_id"] == "00000000-0000-0000-0000-000000000001"


def test_organization_me_can_be_read_and_updated(
    client: TestClient, auth_headers: dict[str, str], viewer_auth_headers: dict[str, str]
) -> None:
    get_response = client.get("/api/v1/organization/me", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "PropertyHub Demo Organisation"

    update_response = client.put(
        "/api/v1/organization/me",
        headers=auth_headers,
        json={
            "name": "PropertyHub Verwaltung Berlin",
            "legal_name": "PropertyHub Verwaltung Berlin GmbH",
            "street": "Musterstraße 10",
            "postal_code": "10115",
            "city": "Berlin",
            "country": "Deutschland",
            "contact_email": "office@propertyhub.de",
            "contact_phone": "+49 30 1234567",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["legal_name"] == "PropertyHub Verwaltung Berlin GmbH"

    viewer_update_response = client.put(
        "/api/v1/organization/me",
        headers=viewer_auth_headers,
        json={
            "name": "Nicht erlaubt",
            "legal_name": None,
            "street": None,
            "postal_code": None,
            "city": None,
            "country": "Deutschland",
            "contact_email": None,
            "contact_phone": None,
        },
    )
    assert viewer_update_response.status_code == 403


def test_users_can_be_managed_within_current_organization(
    client: TestClient, auth_headers: dict[str, str], viewer_auth_headers: dict[str, str]
) -> None:
    create_response = client.post(
        "/api/v1/users/",
        headers=auth_headers,
        json={
            "email": "manager@example.com",
            "full_name": "Manager User",
            "password": "manager-password",
            "role": "manager",
            "is_active": True,
        },
    )
    assert create_response.status_code == 201
    created_user = create_response.json()
    assert created_user["organization_id"] == "00000000-0000-0000-0000-000000000001"
    user_id = created_user["id"]

    list_response = client.get("/api/v1/users/", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 2

    viewer_list_response = client.get("/api/v1/users/", headers=viewer_auth_headers)
    assert viewer_list_response.status_code == 403

    update_response = client.put(
        f"/api/v1/users/{user_id}",
        headers=auth_headers,
        json={
            "full_name": "Manager User Updated",
            "password": "new-manager-password",
            "role": "manager",
            "is_active": False,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Manager User Updated"
    assert update_response.json()["is_active"] is False


def test_users_are_scoped_to_authenticated_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create_response = client.post(
        "/api/v1/users/",
        headers=auth_headers,
        json={
            "email": "org-owned@example.com",
            "full_name": "Org Owned User",
            "password": "org-owned-password",
            "role": "viewer",
            "is_active": True,
        },
    )
    assert create_response.status_code == 201
    created_user_id = create_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="foreign-owner@example.com",
                full_name="Foreign Owner",
                hashed_password=get_password_hash("foreign-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "foreign-owner@example.com", "password": "foreign-password"},
    )
    foreign_headers = {
        "Authorization": "Bearer " + login_response.json()["access_token"]
    }

    list_response = client.get("/api/v1/users/", headers=foreign_headers)
    assert list_response.status_code == 200
    assert all(user["id"] != created_user_id for user in list_response.json())

    update_response = client.put(
        f"/api/v1/users/{created_user_id}",
        headers=foreign_headers,
        json={
            "full_name": "Should Not Work",
            "password": None,
            "role": "viewer",
            "is_active": True,
        },
    )
    assert update_response.status_code == 404


def test_user_invitation_and_password_setup_flow(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invite_response = client.post(
        "/api/v1/users/invitations",
        headers=auth_headers,
        json={
            "email": "invitee@example.com",
            "full_name": "Invitee User",
            "role": "viewer",
        },
    )
    assert invite_response.status_code == 201
    invitation_payload = invite_response.json()
    invitation_token = invitation_payload["invitation_token"]
    assert invitation_payload["user"]["is_active"] is False
    assert invitation_payload["setup_path"].endswith(invitation_token)

    invitation_info_response = client.get(
        f"/api/v1/auth/invitations/{invitation_token}"
    )
    assert invitation_info_response.status_code == 200
    assert invitation_info_response.json()["email"] == "invitee@example.com"

    setup_response = client.post(
        "/api/v1/auth/setup-password",
        json={
            "token": invitation_token,
            "password": "invitee-password",
            "full_name": "Invitee Accepted",
        },
    )
    assert setup_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "invitee@example.com", "password": "invitee-password"},
    )
    assert login_response.status_code == 200


def test_owner_can_resend_invitation_for_pending_user(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invite_response = client.post(
        "/api/v1/users/invitations",
        headers=auth_headers,
        json={
            "email": "resend@example.com",
            "full_name": "Resend User",
            "role": "manager",
        },
    )
    first_token = invite_response.json()["invitation_token"]
    user_id = invite_response.json()["user"]["id"]

    resend_response = client.post(
        f"/api/v1/users/{user_id}/invite",
        headers=auth_headers,
    )
    assert resend_response.status_code == 200
    second_token = resend_response.json()["invitation_token"]
    assert second_token != first_token


def test_document_ocr_endpoint_queues_celery_task(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": None,
            "vendor_name": "Queue Vendor",
            "invoice_number": None,
            "invoice_date": None,
            "gross_amount": 10,
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
                "queue.txt",
                BytesIO(b"Vendor: Queue GmbH"),
                "text/plain",
            )
        },
    )
    document_id = upload_response.json()["id"]

    with patch.object(process_document_ocr_job, "delay") as mocked_delay:
        mocked_delay.return_value = None
        queue_response = client.post(
            f"/api/v1/documents/{document_id}/process-ocr",
            headers=auth_headers,
        )

    assert queue_response.status_code == 202
    mocked_delay.assert_called_once_with(
        "00000000-0000-0000-0000-000000000001", document_id
    )


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
    assert ocr_response.status_code == 202
    queued_document = ocr_response.json()["document"]
    assert queued_document["ocr_status"] == "queued"

    detail_response = client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    processed_document = detail_response.json()
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


def test_document_ocr_can_be_applied_to_invoice(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": None,
            "vendor_name": "Placeholder Vendor",
            "invoice_number": None,
            "invoice_date": None,
            "gross_amount": 99,
            "status": "draft",
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
                "invoice-apply.txt",
                BytesIO(
                    b"Vendor: Better Vendor GmbH\nInvoice Number: OCR-9001\nInvoice Date: 2026-09-01\nGross Amount: 777.70\n"
                ),
                "text/plain",
            )
        },
    )
    document_id = upload_response.json()["id"]

    process_response = client.post(
        f"/api/v1/documents/{document_id}/process-ocr",
        headers=auth_headers,
    )
    assert process_response.status_code == 202

    apply_response = client.post(
        f"/api/v1/documents/{document_id}/apply-ocr-to-invoice",
        headers=auth_headers,
    )
    assert apply_response.status_code == 200
    payload = apply_response.json()
    assert payload["document"]["ocr_status"] == "processed"
    assert payload["invoice"]["vendor_name"] == "Better Vendor GmbH"
    assert payload["invoice"]["invoice_number"] == "OCR-9001"
    assert payload["invoice"]["invoice_date"] == "2026-09-01"
    assert payload["invoice"]["gross_amount"] == 777.7
    assert payload["invoice"]["status"] == "received"


def test_documents_pdf_upload_and_process_ocr(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": None,
            "vendor_name": "PDF Vendor",
            "invoice_number": None,
            "invoice_date": None,
            "gross_amount": 10,
            "status": "draft",
        },
    )
    invoice_id = invoice_response.json()["id"]

    pdf_lines = [
        "Vendor: PDF Vendor GmbH",
        "Invoice Number: PDF-2026-88",
        "Invoice Date: 2026-09-26",
        "Gross Amount: 555.40",
    ]
    content_stream = "BT\n/F1 12 Tf\n72 720 Td\n" + "\n".join(
        [f"({line}) Tj\n0 -20 Td" for line in pdf_lines]
    ) + "\nET"

    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(content_stream.encode('latin-1'))} >>\nstream\n{content_stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf_buffer = BytesIO()
    pdf_buffer.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(pdf_buffer.tell())
        pdf_buffer.write(f"{index} 0 obj\n{obj}\nendobj\n".encode("latin-1"))
    xref_offset = pdf_buffer.tell()
    pdf_buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf_buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf_buffer.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf_buffer.write(
        f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\nstartxref\n{xref_offset}\n%%EOF".encode(
            "latin-1"
        )
    )

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
                "invoice-pdf.pdf",
                BytesIO(pdf_buffer.getvalue()),
                "application/pdf",
            )
        },
    )
    document_id = upload_response.json()["id"]

    ocr_response = client.post(
        f"/api/v1/documents/{document_id}/process-ocr",
        headers=auth_headers,
    )
    assert ocr_response.status_code == 202
    detail_response = client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
    processed_document = detail_response.json()
    assert processed_document["ocr_result"]["vendor_name"] == "PDF Vendor GmbH"
    assert processed_document["ocr_result"]["invoice_number"] == "PDF-2026-88"
    assert processed_document["ocr_result"]["gross_amount"] == 555.4
    assert processed_document["ocr_result"]["source"] == "pdf_text"


def test_document_ocr_failure_is_persisted_and_can_be_retried(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": None,
            "vendor_name": "Retry Vendor",
            "invoice_number": None,
            "invoice_date": None,
            "gross_amount": 50,
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
                "retry.txt",
                BytesIO(b"Vendor: Retry GmbH"),
                "text/plain",
            )
        },
    )
    document_id = upload_response.json()["id"]

    with patch(
        "app.services.document_service.extract_invoice_metadata",
        side_effect=RuntimeError("OCR engine unavailable"),
    ):
        first_process_response = client.post(
            f"/api/v1/documents/{document_id}/process-ocr",
            headers=auth_headers,
        )

    assert first_process_response.status_code == 202
    failed_detail_response = client.get(
        f"/api/v1/documents/{document_id}", headers=auth_headers
    )
    failed_document = failed_detail_response.json()
    assert failed_document["ocr_status"] == "failed"
    assert failed_document["ocr_error"] == "OCR engine unavailable"
    assert failed_document["ocr_attempt_count"] == 1

    with patch(
        "app.services.document_service.extract_invoice_metadata",
        return_value={
            "vendor_name": "Retry Success GmbH",
            "invoice_number": "RETRY-1",
            "invoice_date": "2026-09-26",
            "gross_amount": 123.45,
            "confidence": 1.0,
            "source": "content",
            "status": "processed",
        },
    ):
        retry_response = client.post(
            f"/api/v1/documents/{document_id}/retry-ocr",
            headers=auth_headers,
        )

    assert retry_response.status_code == 202
    retried_document = retry_response.json()["document"]
    assert retried_document["ocr_status"] == "queued"

    processed_detail_response = client.get(
        f"/api/v1/documents/{document_id}", headers=auth_headers
    )
    processed_document = processed_detail_response.json()
    assert processed_document["ocr_status"] == "processed"
    assert processed_document["ocr_error"] is None
    assert processed_document["ocr_attempt_count"] == 2
    assert processed_document["ocr_result"]["vendor_name"] == "Retry Success GmbH"


def test_image_ocr_path_can_extract_invoice_fields() -> None:
    png_signature_only = b"\x89PNG\r\n\x1a\n"
    with patch("app.ml.invoice_ocr._ocr_image_bytes") as mock_ocr:
        mock_ocr.return_value = (
            "Vendor: Image Vendor GmbH\nInvoice Number: IMG-77\nInvoice Date: 2026-10-01\nGross Amount: 333.90",
            True,
        )
        result = extract_invoice_metadata("receipt.png", png_signature_only)

    assert result["vendor_name"] == "Image Vendor GmbH"
    assert result["invoice_number"] == "IMG-77"
    assert result["invoice_date"] == "2026-10-01"
    assert result["gross_amount"] == 333.9
    assert result["source"] == "image_ocr"


def test_invitation_tracks_delivery_status_and_setup_url(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/users/invitations",
        headers=auth_headers,
        json={
            "email": "mailinvite@example.com",
            "full_name": "Mail Invite",
            "role": "viewer",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["setup_url"].endswith(payload["invitation_token"])
    assert payload["user"]["invitation_delivery_status"] == "manual"
    assert payload["user"]["invitation_last_attempt_at"] is not None
    assert payload["user"]["invitation_delivery_error"] is None


def test_audit_logs_capture_mutations_and_support_filters(
    client: TestClient, auth_headers: dict[str, str], viewer_auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Audit Objekt",
            "property_type": "residential",
            "street": "Logstraße 1",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 123000,
        },
    )
    assert property_response.status_code == 201
    property_id = property_response.json()["id"]

    update_org_response = client.put(
        "/api/v1/organization/me",
        headers=auth_headers,
        json={
            "name": "Audit Verwaltung GmbH",
            "legal_name": "Audit Verwaltung GmbH",
            "street": "Logstraße 1",
            "postal_code": "10115",
            "city": "Berlin",
            "country": "Deutschland",
            "contact_email": "audit@propertyhub.de",
            "contact_phone": "+49 30 1000",
        },
    )
    assert update_org_response.status_code == 200

    logs_response = client.get("/api/v1/audit-logs/", headers=auth_headers)
    assert logs_response.status_code == 200
    payload = logs_response.json()
    assert any(
        entry["resource_type"] == "property"
        and entry["action"] == "property.created"
        and entry["resource_id"] == property_id
        for entry in payload
    )
    assert any(entry["action"] == "organization.updated" for entry in payload)

    filtered_logs_response = client.get(
        "/api/v1/audit-logs/?resource_type=property&action=property.created",
        headers=auth_headers,
    )
    assert filtered_logs_response.status_code == 200
    filtered_payload = filtered_logs_response.json()
    assert len(filtered_payload) >= 1
    assert all(entry["resource_type"] == "property" for entry in filtered_payload)
    assert all(entry["action"] == "property.created" for entry in filtered_payload)

    viewer_logs_response = client.get("/api/v1/audit-logs/", headers=viewer_auth_headers)
    assert viewer_logs_response.status_code == 200


def test_audit_logs_are_scoped_to_authenticated_organization(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create_property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Org Eins Objekt",
            "property_type": "residential",
            "street": "Mandantweg 1",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 222000,
        },
    )
    assert create_property_response.status_code == 201
    own_property_id = create_property_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000099",
                email="audit-scope@example.com",
                full_name="Audit Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "audit-scope@example.com", "password": "scope-password"},
    )
    other_headers = {"Authorization": "Bearer " + login_response.json()["access_token"]}

    other_property_response = client.post(
        "/api/v1/properties/",
        headers=other_headers,
        json={
            "name": "Org Zwei Objekt",
            "property_type": "commercial",
            "street": "Mandantweg 2",
            "postal_code": "20095",
            "city": "Hamburg",
            "purchase_price": 333000,
        },
    )
    assert other_property_response.status_code == 201

    own_logs_response = client.get("/api/v1/audit-logs/?resource_type=property", headers=auth_headers)
    assert own_logs_response.status_code == 200
    assert any(entry["resource_id"] == own_property_id for entry in own_logs_response.json())
    assert all(
        entry["summary"] != "Immobilie Org Zwei Objekt angelegt"
        for entry in own_logs_response.json()
    )


def test_operating_cost_periods_items_and_settlement_preview(
    client: TestClient, auth_headers: dict[str, str], viewer_auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Mehrfamilienhaus Nord",
            "property_type": "residential",
            "street": "Abrechnungsweg 1",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 900000,
        },
    )
    property_id = property_response.json()["id"]

    unit_a_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Wohnung A",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 50,
        },
    )
    unit_b_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Wohnung B",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 100,
        },
    )
    unit_a_id = unit_a_response.json()["id"]
    unit_b_id = unit_b_response.json()["id"]

    tenant_a_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Anna",
            "last_name": "Mieter",
            "email": "anna.mieter@example.com",
            "phone": None,
            "move_in_date": "2026-01-01",
            "move_out_date": None,
        },
    )
    tenant_b_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Bernd",
            "last_name": "Mieter",
            "email": "bernd.mieter@example.com",
            "phone": None,
            "move_in_date": "2026-01-01",
            "move_out_date": None,
        },
    )
    tenant_a_id = tenant_a_response.json()["id"]
    tenant_b_id = tenant_b_response.json()["id"]

    client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_a_id,
            "tenant_id": tenant_a_id,
            "start_date": "2026-01-01",
            "end_date": None,
            "cold_rent": 900,
            "service_charge_advance": 100,
        },
    )
    client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_b_id,
            "tenant_id": tenant_b_id,
            "start_date": "2026-01-01",
            "end_date": None,
            "cold_rent": 1200,
            "service_charge_advance": 100,
        },
    )

    create_period_response = client.post(
        "/api/v1/operating-costs/periods",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Nebenkosten 2026 Q1",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "status": "draft",
        },
    )
    assert create_period_response.status_code == 201
    period_id = create_period_response.json()["id"]

    viewer_create_period_response = client.post(
        "/api/v1/operating-costs/periods",
        headers=viewer_auth_headers,
        json={
            "property_id": property_id,
            "name": "Nicht erlaubt",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "status": "draft",
        },
    )
    assert viewer_create_period_response.status_code == 403

    item_area_response = client.post(
        f"/api/v1/operating-costs/periods/{period_id}/items",
        headers=auth_headers,
        json={
            "category": "heating",
            "description": "Heizkosten",
            "allocation_method": "area",
            "amount": 300,
            "billable": True,
        },
    )
    assert item_area_response.status_code == 201

    item_count_response = client.post(
        f"/api/v1/operating-costs/periods/{period_id}/items",
        headers=auth_headers,
        json={
            "category": "janitor",
            "description": "Hausmeister",
            "allocation_method": "unit_count",
            "amount": 150,
            "billable": True,
        },
    )
    assert item_count_response.status_code == 201

    periods_response = client.get("/api/v1/operating-costs/periods", headers=auth_headers)
    assert periods_response.status_code == 200
    assert len(periods_response.json()) == 1

    items_response = client.get(
        f"/api/v1/operating-costs/periods/{period_id}/items",
        headers=auth_headers,
    )
    assert items_response.status_code == 200
    assert len(items_response.json()) == 2

    preview_response = client.get(
        f"/api/v1/operating-costs/periods/{period_id}/settlement-preview",
        headers=auth_headers,
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["total_billable_amount"] == 450
    assert preview_payload["total_advance_amount"] == 600
    assert len(preview_payload["lines"]) == 2
    first_line = next(line for line in preview_payload["lines"] if line["unit_name"] == "Wohnung A")
    second_line = next(line for line in preview_payload["lines"] if line["unit_name"] == "Wohnung B")
    assert first_line["share_amount"] == 175
    assert first_line["advance_paid_amount"] == 300
    assert first_line["balance_amount"] == -125
    assert second_line["share_amount"] == 275
    assert second_line["advance_paid_amount"] == 300
    assert second_line["balance_amount"] == -25
    assert first_line["occupied_days"] == 90
    assert second_line["occupied_days"] == 90

    finalize_response = client.post(
        f"/api/v1/operating-costs/periods/{period_id}/finalize",
        headers=auth_headers,
    )
    assert finalize_response.status_code == 200
    assert finalize_response.json()["status"] == "finalized"

    viewer_finalize_response = client.post(
        f"/api/v1/operating-costs/periods/{period_id}/finalize",
        headers=viewer_auth_headers,
    )
    assert viewer_finalize_response.status_code == 403

    csv_export_response = client.get(
        f"/api/v1/operating-costs/periods/{period_id}/export.csv",
        headers=auth_headers,
    )
    assert csv_export_response.status_code == 200
    assert "settlement_lines" in csv_export_response.text
    assert "Wohnung A" in csv_export_response.text

    pdf_export_response = client.get(
        f"/api/v1/operating-costs/periods/{period_id}/export.pdf",
        headers=auth_headers,
    )
    assert pdf_export_response.status_code == 200
    assert pdf_export_response.headers["content-type"] == "application/pdf"
    pdf_reader = PdfReader(BytesIO(pdf_export_response.content))
    extracted_text = "\\n".join(page.extract_text() or "" for page in pdf_reader.pages)
    assert "PropertyHub Betriebskostenabrechnung" in extracted_text
    assert "Nebenkosten 2026 Q1" in extracted_text

    audit_response = client.get(
        "/api/v1/audit-logs/?resource_type=operating_cost_period",
        headers=auth_headers,
    )
    assert audit_response.status_code == 200
    audit_actions = {entry["action"] for entry in audit_response.json()}
    assert "operating_cost_period.created" in audit_actions
    assert "operating_cost_period.finalized" in audit_actions
    assert "operating_cost_period.exported_csv" in audit_actions
    assert "operating_cost_period.exported_pdf" in audit_actions


def test_operating_cost_preview_supports_vacancy_partial_year_and_advanced_allocation_methods(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Mehrfamilienhaus Süd",
            "property_type": "residential",
            "street": "Umlagestraße 3",
            "postal_code": "50667",
            "city": "Köln",
            "purchase_price": 750000,
        },
    )
    property_id = property_response.json()["id"]

    unit_a_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Wohnung 1",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 50,
        },
    )
    unit_b_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Wohnung 2",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 100,
        },
    )
    unit_a_id = unit_a_response.json()["id"]
    unit_b_id = unit_b_response.json()["id"]

    tenant_a_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "Clara",
            "last_name": "Kurz",
            "email": "clara.kurz@example.com",
            "phone": None,
            "move_in_date": "2026-01-01",
            "move_out_date": None,
        },
    )
    tenant_b_response = client.post(
        "/api/v1/tenants/",
        headers=auth_headers,
        json={
            "first_name": "David",
            "last_name": "Spät",
            "email": "david.spaet@example.com",
            "phone": None,
            "move_in_date": "2026-02-15",
            "move_out_date": None,
        },
    )

    client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_a_id,
            "tenant_id": tenant_a_response.json()["id"],
            "start_date": "2026-01-01",
            "end_date": None,
            "cold_rent": 850,
            "service_charge_advance": 100,
        },
    )
    client.post(
        "/api/v1/contracts/",
        headers=auth_headers,
        json={
            "unit_id": unit_b_id,
            "tenant_id": tenant_b_response.json()["id"],
            "start_date": "2026-02-15",
            "end_date": None,
            "cold_rent": 1100,
            "service_charge_advance": 200,
        },
    )

    period_response = client.post(
        "/api/v1/operating-costs/periods",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Nebenkosten 2026 Q1 Teiljahr",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "status": "draft",
        },
    )
    assert period_response.status_code == 201
    period_id = period_response.json()["id"]

    for item_payload in [
        {
            "category": "heating",
            "description": "Flächenabhängige Heizkosten",
            "allocation_method": "area",
            "amount": 360,
            "billable": True,
        },
        {
            "category": "janitor",
            "description": "Hausmeister nach Einheit",
            "allocation_method": "unit_count",
            "amount": 90,
            "billable": True,
        },
        {
            "category": "lighting",
            "description": "Allgemeinstrom nach Belegungstagen",
            "allocation_method": "occupancy_days",
            "amount": 180,
            "billable": True,
        },
        {
            "category": "water",
            "description": "Wasser nach Vorauszahlungsanteil",
            "allocation_method": "advance_share",
            "amount": 270,
            "billable": True,
        },
    ]:
        item_response = client.post(
            f"/api/v1/operating-costs/periods/{period_id}/items",
            headers=auth_headers,
            json=item_payload,
        )
        assert item_response.status_code == 201

    preview_response = client.get(
        f"/api/v1/operating-costs/periods/{period_id}/settlement-preview",
        headers=auth_headers,
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()

    assert preview_payload["total_billable_amount"] == 900
    assert preview_payload["total_advance_amount"] == 600
    assert len(preview_payload["lines"]) == 3

    unit_1_line = next(
        line
        for line in preview_payload["lines"]
        if line["unit_name"] == "Wohnung 1" and line["line_type"] == "contract"
    )
    unit_2_contract_line = next(
        line
        for line in preview_payload["lines"]
        if line["unit_name"] == "Wohnung 2" and line["line_type"] == "contract"
    )
    vacancy_line = next(
        line
        for line in preview_payload["lines"]
        if line["unit_name"] == "Wohnung 2" and line["line_type"] == "vacancy"
    )

    assert unit_1_line["occupied_days"] == 90
    assert unit_1_line["tenant_name"] == "Clara Kurz"
    assert unit_1_line["share_amount"] == 420
    assert unit_1_line["advance_paid_amount"] == 300
    assert unit_1_line["balance_amount"] == 120

    assert unit_2_contract_line["occupied_days"] == 45
    assert unit_2_contract_line["tenant_name"] == "David Spät"
    assert unit_2_contract_line["share_amount"] == 337.5
    assert unit_2_contract_line["advance_paid_amount"] == 300
    assert unit_2_contract_line["balance_amount"] == 37.5

    assert vacancy_line["occupied_days"] == 45
    assert vacancy_line["tenant_name"] == "Leerstand"
    assert vacancy_line["share_amount"] == 142.5
    assert vacancy_line["advance_paid_amount"] == 0
    assert vacancy_line["balance_amount"] == 142.5


def test_tasks_crud_scoping_and_permissions(
    client: TestClient, auth_headers: dict[str, str], viewer_auth_headers: dict[str, str]
) -> None:
    create_vendor_response = client.post(
        "/api/v1/vendors/",
        headers=auth_headers,
        json={
            "name": "Wärme Service GmbH",
            "service_type": "maintenance",
            "contact_email": "service@example.com",
            "contact_phone": "+49 30 999999",
            "notes": "24/7 Notdienst",
        },
    )
    assert create_vendor_response.status_code == 201
    vendor_id = create_vendor_response.json()["id"]

    viewer_vendor_response = client.post(
        "/api/v1/vendors/",
        headers=viewer_auth_headers,
        json={
            "name": "Nicht erlaubt",
            "service_type": "other",
            "contact_email": None,
            "contact_phone": None,
            "notes": None,
        },
    )
    assert viewer_vendor_response.status_code == 403

    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Serviceobjekt Berlin",
            "property_type": "residential",
            "street": "Serviceweg 7",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 420000,
        },
    )
    property_id = property_response.json()["id"]

    unit_response = client.post(
        "/api/v1/units/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "name": "Einheit 1",
            "unit_type": "apartment",
            "status": "occupied",
            "area_sqm": 80,
        },
    )
    unit_id = unit_response.json()["id"]

    create_task_response = client.post(
        "/api/v1/tasks/",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "unit_id": unit_id,
            "vendor_id": vendor_id,
            "title": "Heizung prüfen",
            "description": "Thermostate kontrollieren und Wartung terminieren",
            "category": "maintenance",
            "priority": "high",
            "status": "open",
            "due_date": "2026-10-15",
            "assignee_name": "Hausmeister Team",
            "source": "manual",
        },
    )
    assert create_task_response.status_code == 201
    task_payload = create_task_response.json()
    task_id = task_payload["id"]
    assert task_payload["property_id"] == property_id
    assert task_payload["unit_id"] == unit_id
    assert task_payload["vendor_id"] == vendor_id

    viewer_create_response = client.post(
        "/api/v1/tasks/",
        headers=viewer_auth_headers,
        json={
            "title": "Nicht erlaubt",
            "category": "other",
            "priority": "low",
            "status": "open",
            "source": "manual",
        },
    )
    assert viewer_create_response.status_code == 403

    get_task_response = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert get_task_response.status_code == 200
    assert get_task_response.json()["title"] == "Heizung prüfen"

    update_task_response = client.put(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "unit_id": unit_id,
            "vendor_id": vendor_id,
            "title": "Heizung prüfen",
            "description": "Termin mit Fachfirma bestätigt",
            "category": "maintenance",
            "priority": "urgent",
            "status": "in_progress",
            "due_date": "2026-10-12",
            "assignee_name": "Fachfirma Wärme GmbH",
            "source": "manual",
        },
    )
    assert update_task_response.status_code == 200
    assert update_task_response.json()["status"] == "in_progress"
    assert update_task_response.json()["priority"] == "urgent"

    create_comment_response = client.post(
        f"/api/v1/tasks/{task_id}/comments",
        headers=auth_headers,
        json={"message": "Techniker für Donnerstag bestätigt"},
    )
    assert create_comment_response.status_code == 201
    assert create_comment_response.json()["author_email"] == "admin@example.com"

    viewer_comment_response = client.post(
        f"/api/v1/tasks/{task_id}/comments",
        headers=viewer_auth_headers,
        json={"message": "Nicht erlaubt"},
    )
    assert viewer_comment_response.status_code == 403

    list_comments_response = client.get(
        f"/api/v1/tasks/{task_id}/comments",
        headers=auth_headers,
    )
    assert list_comments_response.status_code == 200
    assert list_comments_response.json()[0]["message"] == "Techniker für Donnerstag bestätigt"

    upload_attachment_response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        data={
            "related_model": "task",
            "related_id": task_id,
            "document_type": "task_attachment",
        },
        files={"file": ("auftrag.txt", BytesIO(b"Wartungsprotokoll"), "text/plain")},
    )
    assert upload_attachment_response.status_code == 201

    attachments_response = client.get(
        f"/api/v1/tasks/{task_id}/attachments",
        headers=auth_headers,
    )
    assert attachments_response.status_code == 200
    assert attachments_response.json()[0]["file_name"] == "auftrag.txt"

    history_response = client.get(
        f"/api/v1/tasks/{task_id}/history",
        headers=auth_headers,
    )
    assert history_response.status_code == 200
    history_types = {entry["entry_type"] for entry in history_response.json()}
    assert "audit" in history_types
    assert "comment" in history_types
    assert "attachment" in history_types

    viewer_update_response = client.put(
        f"/api/v1/tasks/{task_id}",
        headers=viewer_auth_headers,
        json={
            "property_id": property_id,
            "unit_id": unit_id,
            "vendor_id": vendor_id,
            "title": "Heizung prüfen",
            "description": "Nicht erlaubt",
            "category": "maintenance",
            "priority": "low",
            "status": "done",
            "due_date": "2026-10-10",
            "assignee_name": "Viewer",
            "source": "manual",
        },
    )
    assert viewer_update_response.status_code == 403

    with SessionLocal() as db:
        db.add(
            User(
                organization_id="00000000-0000-0000-0000-000000000098",
                email="task-scope@example.com",
                full_name="Task Scope User",
                hashed_password=get_password_hash("scope-password"),
                role="owner",
                is_active=True,
            )
        )
        db.commit()

    other_login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "task-scope@example.com", "password": "scope-password"},
    )
    other_headers = {"Authorization": "Bearer " + other_login_response.json()["access_token"]}

    other_property_response = client.post(
        "/api/v1/properties/",
        headers=other_headers,
        json={
            "name": "Serviceobjekt Hamburg",
            "property_type": "commercial",
            "street": "Serviceweg 8",
            "postal_code": "20095",
            "city": "Hamburg",
            "purchase_price": 520000,
        },
    )
    other_property_id = other_property_response.json()["id"]
    other_task_response = client.post(
        "/api/v1/tasks/",
        headers=other_headers,
        json={
            "property_id": other_property_id,
            "unit_id": None,
            "title": "Dach prüfen",
            "description": "Nur andere Organisation",
            "category": "inspection",
            "priority": "medium",
            "status": "open",
            "due_date": "2026-11-01",
            "assignee_name": "Extern",
            "source": "manual",
        },
    )
    assert other_task_response.status_code == 201
    other_task_id = other_task_response.json()["id"]

    template_response = client.post(
        "/api/v1/tasks/templates",
        headers=auth_headers,
        json={
            "property_id": property_id,
            "unit_id": unit_id,
            "vendor_id": vendor_id,
            "title": "Filterwechsel",
            "description": "Monatliche Routineprüfung",
            "category": "maintenance",
            "priority": "medium",
            "recurrence_frequency": "monthly",
            "next_due_date": date.today().isoformat(),
            "assignee_name": "Wärme Service GmbH",
            "active": True,
        },
    )
    assert template_response.status_code == 201

    generate_tasks_response = client.post(
        "/api/v1/tasks/templates/generate-due",
        headers=auth_headers,
    )
    assert generate_tasks_response.status_code == 200
    assert generate_tasks_response.json()["generated_count"] == 1
    assert generate_tasks_response.json()["tasks"][0]["source"] == "recurring"

    own_tasks_response = client.get("/api/v1/tasks/", headers=auth_headers)
    assert own_tasks_response.status_code == 200
    own_task_ids = {task["id"] for task in own_tasks_response.json()}
    assert task_id in own_task_ids
    assert other_task_id not in own_task_ids
    assert len(own_tasks_response.json()) >= 2

    audit_response = client.get("/api/v1/audit-logs/?resource_type=task", headers=auth_headers)
    assert audit_response.status_code == 200
    audit_actions = {entry["action"] for entry in audit_response.json()}
    assert "task.created" in audit_actions
    assert "task.updated" in audit_actions

    viewer_delete_response = client.delete(f"/api/v1/tasks/{task_id}", headers=viewer_auth_headers)
    assert viewer_delete_response.status_code == 403

    delete_task_response = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert delete_task_response.status_code == 204

    deleted_list_response = client.get("/api/v1/tasks/", headers=auth_headers)
    assert all(task["id"] != task_id for task in deleted_list_response.json())


def test_banking_csv_import_deduplicates_and_auto_matches_payment(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": None,
            "vendor_name": "Mieterkonto",
            "invoice_number": "INV-100",
            "invoice_date": "2026-09-01",
            "due_date": "2026-09-05",
            "gross_amount": 1200,
            "status": "received",
        },
    )
    invoice_id = invoice_response.json()["id"]

    payment_response = client.post(
        "/api/v1/payments/",
        headers=auth_headers,
        json={
            "invoice_id": invoice_id,
            "contract_id": None,
            "amount": 1200,
            "booking_date": "2026-09-05",
            "reference": "Miete INV-100",
        },
    )
    payment_id = payment_response.json()["id"]

    csv_content = (
        "external_id,account_name,transaction_type,booking_date,value_date,amount,currency,counterparty_name,iban,reference\n"
        "tx-001,Geschäftskonto,credit,2026-09-05,2026-09-05,1200.00,EUR,Max Mustermann,DE44500105175407324931,Miete INV-100\n"
        "tx-001,Geschäftskonto,credit,2026-09-05,2026-09-05,1200.00,EUR,Max Mustermann,DE44500105175407324931,Miete INV-100\n"
        "tx-002,Geschäftskonto,debit,2026-09-06,2026-09-06,85.10,EUR,Stadtwerke,DE89370400440532013000,Abschlag September\n"
    )
    response = client.post(
        "/api/v1/banking/import",
        headers=auth_headers,
        files={"file": ("bank.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["imported_count"] == 2
    assert payload["duplicate_count"] == 1
    assert payload["matched_count"] == 1
    matched_transactions = [item for item in payload["transactions"] if item["payment_id"]]
    assert len(matched_transactions) == 1
    assert matched_transactions[0]["payment_id"] == payment_id
    assert matched_transactions[0]["status"] == "matched"


def test_overdue_invoices_reminders_and_report_exports(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    invoice_response = client.post(
        "/api/v1/invoices/",
        headers=auth_headers,
        json={
            "property_id": None,
            "vendor_name": "Hausverwaltung Nord",
            "invoice_number": "REM-2026-01",
            "invoice_date": (date.today() - timedelta(days=20)).isoformat(),
            "due_date": (date.today() - timedelta(days=10)).isoformat(),
            "gross_amount": 450,
            "status": "received",
        },
    )
    assert invoice_response.status_code == 201
    invoice_id = invoice_response.json()["id"]

    overdue_response = client.get("/api/v1/invoices/overdue", headers=auth_headers)
    assert overdue_response.status_code == 200
    overdue_payload = overdue_response.json()
    assert any(item["id"] == invoice_id and item["days_overdue"] >= 10 for item in overdue_payload)

    with patch(
        "app.services.invoice_service.NotificationService.send_payment_reminder",
        return_value="sent",
    ):
        reminder_response = client.post(
            f"/api/v1/invoices/{invoice_id}/reminders",
            headers=auth_headers,
            json={"recipient_email": "tenant@example.com", "note": "Bitte um kurzfristige Zahlung"},
        )
    assert reminder_response.status_code == 201
    reminder_payload = reminder_response.json()
    assert reminder_payload["reminder_level"] == 1
    assert reminder_payload["status"] == "sent"

    reminder_list_response = client.get(
        f"/api/v1/invoices/{invoice_id}/reminders",
        headers=auth_headers,
    )
    assert reminder_list_response.status_code == 200
    assert reminder_list_response.json()[0]["recipient_email"] == "tenant@example.com"

    open_invoices_response = client.get("/api/v1/reports/open-invoices", headers=auth_headers)
    assert open_invoices_response.status_code == 200
    report_row = next(item for item in open_invoices_response.json() if item["invoice_id"] == invoice_id)
    assert report_row["latest_reminder_level"] == 1

    open_invoices_csv_response = client.get(
        "/api/v1/reports/export/open-invoices.csv", headers=auth_headers
    )
    assert open_invoices_csv_response.status_code == 200
    assert "REM-2026-01" in open_invoices_csv_response.text

    dashboard_csv_response = client.get(
        "/api/v1/reports/export/dashboard.csv", headers=auth_headers
    )
    assert dashboard_csv_response.status_code == 200
    assert "metric,value" in dashboard_csv_response.text


def test_document_review_metadata_can_be_updated(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    property_response = client.post(
        "/api/v1/properties/",
        headers=auth_headers,
        json={
            "name": "Dokumentenobjekt",
            "property_type": "residential",
            "street": "Prüfstraße 9",
            "postal_code": "10115",
            "city": "Berlin",
            "purchase_price": 200000,
        },
    )
    property_id = property_response.json()["id"]

    upload_response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        data={
            "related_model": "property",
            "related_id": property_id,
            "document_type": "property_record",
        },
        files={"file": ("akte.txt", BytesIO(b"Property file"), "text/plain")},
    )
    document_id = upload_response.json()["id"]

    review_response = client.patch(
        f"/api/v1/documents/{document_id}/review",
        headers=auth_headers,
        json={
            "category": "building_record",
            "version_label": "v2",
            "review_status": "approved",
            "review_notes": "Vollstaendig geprueft",
        },
    )
    assert review_response.status_code == 200
    payload = review_response.json()
    assert payload["category"] == "building_record"
    assert payload["version_label"] == "v2"
    assert payload["review_status"] == "approved"
    assert payload["review_notes"] == "Vollstaendig geprueft"
    assert payload["reviewed_by"] is not None
