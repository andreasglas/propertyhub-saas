from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class Payment(TenantScopedModel):
    __tablename__ = "payments"

    invoice_id: Mapped[str | None] = mapped_column(ForeignKey("invoices.id"))
    contract_id: Mapped[str | None] = mapped_column(ForeignKey("contracts.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    booking_date: Mapped[date | None] = mapped_column(Date)
    reference: Mapped[str | None] = mapped_column(String(255))
