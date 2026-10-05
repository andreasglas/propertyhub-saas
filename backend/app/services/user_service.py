from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import PropertyHubError
from app.core.security import create_random_token, get_password_hash
from app.db.models.organization import Organization
from app.db.models.user import User
from app.schemas.organization import OrganizationUpdate
from app.schemas.user import UserCreate, UserInvitationCreate, UserUpdate
from app.services.notification_service import NotificationService


class UserService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.notification_service = NotificationService()

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

    def ensure_organization(
        self,
        db: Session,
        organization_id: str,
        *,
        name: str = "PropertyHub Organisation",
    ) -> Organization:
        organization = db.scalar(
            select(Organization).where(Organization.id == organization_id)
        )
        if organization is not None:
            return organization

        organization = Organization(id=organization_id, name=name)
        db.add(organization)
        db.commit()
        db.refresh(organization)
        return organization

    def get_organization(self, db: Session, organization_id: str) -> Organization:
        organization = db.scalar(
            select(Organization).where(Organization.id == organization_id)
        )
        if organization is None:
            raise PropertyHubError("Organization not found", status_code=404)
        return organization

    def update_organization(
        self, db: Session, organization_id: str, payload: OrganizationUpdate
    ) -> Organization:
        organization = self.get_organization(db, organization_id)
        for key, value in payload.model_dump().items():
            setattr(organization, key, value)
        db.add(organization)
        db.commit()
        db.refresh(organization)
        return organization

    def list_users(self, db: Session, organization_id: str) -> list[User]:
        statement = (
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.email.asc())
        )
        return list(db.scalars(statement))

    def get_user(self, db: Session, organization_id: str, user_id: str) -> User:
        user = db.scalar(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )
        if user is None:
            raise PropertyHubError("User not found", status_code=404)
        return user

    def create_user(self, db: Session, organization_id: str, payload: UserCreate) -> User:
        existing_user = self.get_user_by_email(db, payload.email)
        if existing_user is not None:
            raise PropertyHubError("User with this email already exists", status_code=400)

        user = User(
            organization_id=organization_id,
            email=str(payload.email),
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
            is_active=payload.is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def invite_user(
        self, db: Session, organization_id: str, payload: UserInvitationCreate
    ) -> tuple[User, str]:
        existing_user = self.get_user_by_email(db, payload.email)
        if existing_user is not None:
            raise PropertyHubError("User with this email already exists", status_code=400)

        invitation_token = create_random_token()
        user = User(
            organization_id=organization_id,
            email=str(payload.email),
            full_name=payload.full_name,
            hashed_password=None,
            role=payload.role,
            is_active=False,
            invitation_token=invitation_token,
            invitation_sent_at=datetime.now(timezone.utc),
            invitation_accepted_at=None,
            invitation_delivery_status="pending",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        self._deliver_invitation_email(db, user)
        return user, invitation_token

    def resend_invitation(
        self, db: Session, organization_id: str, user_id: str
    ) -> tuple[User, str]:
        user = self.get_user(db, organization_id, user_id)
        if user.invitation_accepted_at is not None:
            raise PropertyHubError("Invitation has already been accepted", status_code=400)

        invitation_token = create_random_token()
        user.invitation_token = invitation_token
        user.invitation_sent_at = datetime.now(timezone.utc)
        user.is_active = False
        user.invitation_delivery_status = "pending"
        user.invitation_delivery_error = None
        db.add(user)
        db.commit()
        db.refresh(user)
        self._deliver_invitation_email(db, user)
        return user, invitation_token

    def _deliver_invitation_email(self, db: Session, user: User) -> User:
        organization = self.get_organization(db, user.organization_id)
        user.invitation_last_attempt_at = datetime.now(timezone.utc)
        try:
            delivery_status = self.notification_service.send_user_invitation(
                recipient_email=user.email,
                recipient_name=user.full_name,
                organization_name=organization.name,
                role=user.role,
                setup_url=self.notification_service.build_setup_url(
                    user.invitation_token or ""
                ),
            )
            user.invitation_delivery_status = delivery_status
            user.invitation_delivery_error = None
        except Exception as exc:
            user.invitation_delivery_status = "failed"
            user.invitation_delivery_error = str(exc)[:1000]
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_user_by_invitation_token(self, db: Session, token: str) -> User:
        user = db.scalar(select(User).where(User.invitation_token == token))
        if user is None:
            raise PropertyHubError("Invitation token is invalid", status_code=404)
        return user

    def accept_invitation(
        self, db: Session, token: str, password: str, full_name: str | None = None
    ) -> User:
        user = self.get_user_by_invitation_token(db, token)
        user.hashed_password = get_password_hash(password)
        user.is_active = True
        user.invitation_token = None
        user.invitation_accepted_at = datetime.now(timezone.utc)
        if full_name is not None and full_name.strip():
            user.full_name = full_name.strip()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update_user(
        self, db: Session, organization_id: str, user_id: str, payload: UserUpdate
    ) -> User:
        user = self.get_user(db, organization_id, user_id)
        update_data = payload.model_dump()

        password = update_data.pop("password", None)
        if password:
            user.hashed_password = get_password_hash(password)

        for key, value in update_data.items():
            setattr(user, key, value)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def ensure_bootstrap_admin(self, db: Session) -> User | None:
        configured_password = self.settings.bootstrap_admin_password
        configured_email = self.settings.bootstrap_admin_email
        if not configured_email or configured_password is None:
            return None

        self.ensure_organization(
            db,
            self.settings.bootstrap_admin_organization_id,
            name="PropertyHub Demo Organisation",
        )
        user = self.get_user_by_email(db, configured_email)
        if user is not None:
            return user

        user = User(
            organization_id=self.settings.bootstrap_admin_organization_id,
            email=configured_email,
            full_name="Bootstrap Admin",
            hashed_password=get_password_hash(configured_password.get_secret_value()),
            role="owner",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
