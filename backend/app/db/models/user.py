from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, OrganizationMixin, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, OrganizationMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="owner")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    invitation_token: Mapped[str | None] = mapped_column(String(255), index=True)
    invitation_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invitation_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invitation_delivery_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    invitation_delivery_error: Mapped[str | None] = mapped_column(Text)
    invitation_last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
