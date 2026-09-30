from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class OperatingCostItem(TenantScopedModel):
    __tablename__ = "operating_cost_items"

    period_id: Mapped[str] = mapped_column(
        ForeignKey("operating_cost_periods.id"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    allocation_method: Mapped[str] = mapped_column(String(50), nullable=False, default="area")
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    billable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
