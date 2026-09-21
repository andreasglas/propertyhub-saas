from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import get_password_hash
from app.db.models.user import User


class UserService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

    def ensure_bootstrap_admin(self, db: Session) -> User | None:
        configured_password = self.settings.bootstrap_admin_password
        configured_email = self.settings.bootstrap_admin_email
        if not configured_email or configured_password is None:
            return None

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
