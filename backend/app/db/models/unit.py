from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class Unit(TenantScopedModel):
    __tablename__ = "units"

    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(50), nullable=False, default="apartment")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="vacant")
    area_sqm: Mapped[float | None] = mapped_column(Numeric(8, 2))
