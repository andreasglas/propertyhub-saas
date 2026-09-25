from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.unit import UnitCreate, UnitRead, UnitUpdate
from app.services.unit_service import UnitService

router = APIRouter()
service = UnitService()


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
    return service.create_unit(db, current_user.organization_id, payload)


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
    return service.update_unit(db, current_user.organization_id, unit_id, payload)


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(
    unit_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    service.delete_unit(db, current_user.organization_id, unit_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
