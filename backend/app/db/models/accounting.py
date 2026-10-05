from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class AccountingEntry(TenantScopedModel):
    __tablename__ = "accounting_entries"

    property_id: Mapped[str | None] = mapped_column(ForeignKey("properties.id"))
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    booking_date: Mapped[date | None] = mapped_column(Date)
