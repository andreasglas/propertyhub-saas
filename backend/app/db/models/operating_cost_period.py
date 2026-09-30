from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class OperatingCostPeriod(TenantScopedModel):
    __tablename__ = "operating_cost_periods"

    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
