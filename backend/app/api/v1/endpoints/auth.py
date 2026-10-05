from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.core.dependencies import get_current_user
from app.core.exceptions import PropertyHubError
from app.db.models.organization import Organization
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import InvitationInfo, SetupPasswordRequest, SetupPasswordResult, Token, UserRead
from app.services.audit_log_service import AuditLogService
from app.services.user_service import UserService
from sqlalchemy import select

router = APIRouter()
service = UserService()
audit_service = AuditLogService()


@router.post("/token", response_model=Token)
async def issue_access_token(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = db.scalar(select(User).where(User.email == credentials.username))
    if (
        user is None
        or not user.hashed_password
        or not user.is_active
        or not verify_password(credentials.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=user.email)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
async def get_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return current_user


@router.get("/invitations/{token}", response_model=InvitationInfo)
async def get_invitation_details(
    token: str,
    db: Session = Depends(get_db),
) -> InvitationInfo:
    try:
        user = service.get_user_by_invitation_token(db, token)
    except PropertyHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    organization = db.scalar(
        select(Organization).where(Organization.id == user.organization_id)
    )
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    return InvitationInfo(
        email=user.email,
        full_name=user.full_name,
        organization_name=organization.name,
        role=user.role,
    )


@router.post("/setup-password", response_model=SetupPasswordResult)
async def setup_password(
    payload: SetupPasswordRequest,
    db: Session = Depends(get_db),
) -> SetupPasswordResult:
    try:
        user = service.accept_invitation(db, payload.token, payload.password, payload.full_name)
    except PropertyHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    audit_service.record(
        db,
        organization_id=user.organization_id,
        actor=user,
        action="user.invitation_accepted",
        resource_type="user",
        resource_id=user.id,
        summary=f"Einladung von {user.email} angenommen",
        details={"role": user.role},
    )
    return SetupPasswordResult()
