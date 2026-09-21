from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from app.services.property_service import PropertyService

router = APIRouter()
service = PropertyService()


@router.get("/", response_model=list[PropertyRead])
async def list_properties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PropertyRead]:
    return service.list_properties(db, current_user.organization_id)


@router.post("/", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
async def create_property(
    payload: PropertyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PropertyRead:
    return service.create_property(db, current_user.organization_id, payload)


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PropertyRead:
    return service.update_property(db, current_user.organization_id, property_id, payload)


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service.delete_property(db, current_user.organization_id, property_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
