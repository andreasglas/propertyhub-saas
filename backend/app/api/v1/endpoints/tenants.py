from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.tenant import TenantCreate, TenantRead, TenantUpdate
from app.services.audit_log_service import AuditLogService
from app.services.tenant_service import TenantService

router = APIRouter()
service = TenantService()
audit_service = AuditLogService()


@router.get("/", response_model=list[TenantRead])
async def list_tenants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TenantRead]:
    return service.list_tenants(db, current_user.organization_id)


@router.post("/", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> TenantRead:
    tenant = service.create_tenant(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="tenant.created",
        resource_type="tenant",
        resource_id=tenant.id,
        summary=f"Mieter {tenant.first_name} {tenant.last_name} angelegt",
        details={"email": tenant.email},
    )
    return tenant


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantRead:
    return service.get_tenant(db, current_user.organization_id, tenant_id)


@router.put("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> TenantRead:
    tenant = service.update_tenant(db, current_user.organization_id, tenant_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="tenant.updated",
        resource_type="tenant",
        resource_id=tenant.id,
        summary=f"Mieter {tenant.first_name} {tenant.last_name} aktualisiert",
        details={"email": tenant.email},
    )
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    tenant = service.get_tenant(db, current_user.organization_id, tenant_id)
    service.delete_tenant(db, current_user.organization_id, tenant_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="tenant.deleted",
        resource_type="tenant",
        resource_id=tenant_id,
        summary=f"Mieter {tenant.first_name} {tenant.last_name} gelöscht",
        details={"email": tenant.email},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
