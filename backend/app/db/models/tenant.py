from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class Tenant(TenantScopedModel):
    __tablename__ = "tenants"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    move_in_date: Mapped[date | None] = mapped_column(Date)
    move_out_date: Mapped[date | None] = mapped_column(Date)
