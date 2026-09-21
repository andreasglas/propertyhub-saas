from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.tenant import TenantCreate, TenantRead, TenantUpdate
from app.services.tenant_service import TenantService

router = APIRouter()
service = TenantService()


@router.get("/", response_model=list[TenantRead])
async def list_tenants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TenantRead]:
    return service.list_tenants(db, current_user.organization_id)


@router.post("/", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantRead:
    return service.create_tenant(db, current_user.organization_id, payload)


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantRead:
    return service.update_tenant(db, current_user.organization_id, tenant_id, payload)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service.delete_tenant(db, current_user.organization_id, tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
