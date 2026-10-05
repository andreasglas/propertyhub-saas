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
from app.services.audit_log_service import AuditLogService
from app.services.notification_service import NotificationService
from app.services.user_service import UserService

router = APIRouter()
service = UserService()
notification_service = NotificationService()
audit_service = AuditLogService()


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
    user = service.create_user(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="user.created",
        resource_type="user",
        resource_id=user.id,
        summary=f"Benutzer {user.email} angelegt",
        details={"role": user.role, "is_active": user.is_active},
    )
    return user


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
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="user.invited",
        resource_type="user",
        resource_id=user.id,
        summary=f"Einladung für {user.email} erstellt",
        details={"role": user.role, "delivery_status": user.invitation_delivery_status},
    )
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
    user = service.update_user(db, current_user.organization_id, user_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="user.updated",
        resource_type="user",
        resource_id=user.id,
        summary=f"Benutzer {user.email} aktualisiert",
        details={"role": user.role, "is_active": user.is_active},
    )
    return user


@router.post("/{user_id}/invite", response_model=UserInvitationResult)
async def resend_invite(
    user_id: str,
    current_user: User = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
) -> UserInvitationResult:
    user, invitation_token = service.resend_invitation(
        db, current_user.organization_id, user_id
    )
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="user.reinvited",
        resource_type="user",
        resource_id=user.id,
        summary=f"Einladung für {user.email} erneut versendet",
        details={"delivery_status": user.invitation_delivery_status},
    )
    return UserInvitationResult(
        user=user,
        invitation_token=invitation_token,
        setup_path=f"/setup-password?token={invitation_token}",
        setup_url=notification_service.build_setup_url(invitation_token),
    )
