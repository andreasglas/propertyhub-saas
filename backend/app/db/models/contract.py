from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class Contract(TenantScopedModel):
    __tablename__ = "contracts"

    unit_id: Mapped[str] = mapped_column(ForeignKey("units.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    cold_rent: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    service_charge_advance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
