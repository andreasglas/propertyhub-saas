from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.unit import UnitCreate, UnitRead, UnitUpdate
from app.services.audit_log_service import AuditLogService
from app.services.unit_service import UnitService

router = APIRouter()
service = UnitService()
audit_service = AuditLogService()


@router.get("/", response_model=list[UnitRead])
async def list_units(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UnitRead]:
    return service.list_units(db, current_user.organization_id)


@router.post("/", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
async def create_unit(
    payload: UnitCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> UnitRead:
    unit = service.create_unit(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="unit.created",
        resource_type="unit",
        resource_id=unit.id,
        summary=f"Einheit {unit.name} angelegt",
        details={"status": unit.status},
    )
    return unit


@router.get("/{unit_id}", response_model=UnitRead)
async def get_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UnitRead:
    return service.get_unit(db, current_user.organization_id, unit_id)


@router.put("/{unit_id}", response_model=UnitRead)
async def update_unit(
    unit_id: str,
    payload: UnitUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> UnitRead:
    unit = service.update_unit(db, current_user.organization_id, unit_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="unit.updated",
        resource_type="unit",
        resource_id=unit.id,
        summary=f"Einheit {unit.name} aktualisiert",
        details={"status": unit.status},
    )
    return unit


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(
    unit_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    unit = service.get_unit(db, current_user.organization_id, unit_id)
    service.delete_unit(db, current_user.organization_id, unit_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="unit.deleted",
        resource_type="unit",
        resource_id=unit_id,
        summary=f"Einheit {unit.name} gelöscht",
        details={"status": unit.status},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
