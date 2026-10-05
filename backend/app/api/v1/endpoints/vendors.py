from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.vendor import VendorCreate, VendorRead, VendorUpdate
from app.services.audit_log_service import AuditLogService
from app.services.vendor_service import VendorService

router = APIRouter()
service = VendorService()
audit_service = AuditLogService()


@router.get("/", response_model=list[VendorRead])
async def list_vendors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[VendorRead]:
    return service.list_vendors(db, current_user.organization_id)


@router.post("/", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    payload: VendorCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> VendorRead:
    vendor = service.create_vendor(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="vendor.created",
        resource_type="vendor",
        resource_id=vendor.id,
        summary=f"Dienstleister {vendor.name} angelegt",
        details={"service_type": vendor.service_type},
    )
    return vendor


@router.put("/{vendor_id}", response_model=VendorRead)
async def update_vendor(
    vendor_id: str,
    payload: VendorUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> VendorRead:
    vendor = service.update_vendor(db, current_user.organization_id, vendor_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="vendor.updated",
        resource_type="vendor",
        resource_id=vendor.id,
        summary=f"Dienstleister {vendor.name} aktualisiert",
        details={"service_type": vendor.service_type},
    )
    return vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    vendor = service.get_vendor(db, current_user.organization_id, vendor_id)
    service.delete_vendor(db, current_user.organization_id, vendor_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="vendor.deleted",
        resource_type="vendor",
        resource_id=vendor_id,
        summary=f"Dienstleister {vendor.name} gelöscht",
        details={"service_type": vendor.service_type},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
