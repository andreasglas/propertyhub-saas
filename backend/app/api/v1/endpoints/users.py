from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import (
    UserCreate,
    UserInvitationCreate,
    UserInvitationResult,
    UserRead,
    UserUpdate,
)
from app.services.notification_service import NotificationService
from app.services.user_service import UserService

router = APIRouter()
service = UserService()
notification_service = NotificationService()


@router.get("/", response_model=list[UserRead])
async def list_users(
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    return service.list_users(db, current_user.organization_id)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
) -> UserRead:
    return service.create_user(db, current_user.organization_id, payload)


@router.post(
    "/invitations",
    response_model=UserInvitationResult,
    status_code=status.HTTP_201_CREATED,
)
async def invite_user(
    payload: UserInvitationCreate,
    current_user: User = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
) -> UserInvitationResult:
    user, invitation_token = service.invite_user(db, current_user.organization_id, payload)
    return UserInvitationResult(
        user=user,
        invitation_token=invitation_token,
        setup_path=f"/setup-password?token={invitation_token}",
        setup_url=notification_service.build_setup_url(invitation_token),
    )


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: User = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
) -> UserRead:
    if user_id == current_user.id and (not payload.is_active or payload.role != "owner"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owners cannot deactivate or demote their own account",
        )
    return service.update_user(db, current_user.organization_id, user_id, payload)


@router.post("/{user_id}/invite", response_model=UserInvitationResult)
async def resend_invite(
    user_id: str,
    current_user: User = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
) -> UserInvitationResult:
    user, invitation_token = service.resend_invitation(
        db, current_user.organization_id, user_id
    )
    return UserInvitationResult(
        user=user,
        invitation_token=invitation_token,
        setup_path=f"/setup-password?token={invitation_token}",
        setup_url=notification_service.build_setup_url(invitation_token),
    )
