from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.organization import OrganizationRead, OrganizationUpdate
from app.services.user_service import UserService

router = APIRouter()
service = UserService()


@router.get("/me", response_model=OrganizationRead)
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    return service.get_organization(db, current_user.organization_id)


@router.put("/me", response_model=OrganizationRead)
async def update_current_organization(
    payload: OrganizationUpdate,
    current_user: User = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    return service.update_organization(db, current_user.organization_id, payload)
