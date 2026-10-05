from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from app.services.audit_log_service import AuditLogService
from app.services.property_service import PropertyService

router = APIRouter()
service = PropertyService()
audit_service = AuditLogService()


@router.get("/", response_model=list[PropertyRead])
async def list_properties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PropertyRead]:
    return service.list_properties(db, current_user.organization_id)


@router.post("/", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
async def create_property(
    payload: PropertyCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> PropertyRead:
    property_obj = service.create_property(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="property.created",
        resource_type="property",
        resource_id=property_obj.id,
        summary=f"Immobilie {property_obj.name} angelegt",
        details={"property_type": property_obj.property_type},
    )
    return property_obj


@router.get("/{property_id}", response_model=PropertyRead)
async def get_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PropertyRead:
    return service.get_property(db, current_user.organization_id, property_id)


@router.put("/{property_id}", response_model=PropertyRead)
async def update_property(
    property_id: str,
    payload: PropertyUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> PropertyRead:
    property_obj = service.update_property(db, current_user.organization_id, property_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="property.updated",
        resource_type="property",
        resource_id=property_obj.id,
        summary=f"Immobilie {property_obj.name} aktualisiert",
        details={"property_type": property_obj.property_type},
    )
    return property_obj


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    property_obj = service.get_property(db, current_user.organization_id, property_id)
    service.delete_property(db, current_user.organization_id, property_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="property.deleted",
        resource_type="property",
        resource_id=property_id,
        summary=f"Immobilie {property_obj.name} gelöscht",
        details={"property_type": property_obj.property_type},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
