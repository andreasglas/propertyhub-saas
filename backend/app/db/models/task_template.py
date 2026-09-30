from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class TaskTemplate(TenantScopedModel):
    __tablename__ = "task_templates"

    property_id: Mapped[str | None] = mapped_column(ForeignKey("properties.id"), index=True)
    unit_id: Mapped[str | None] = mapped_column(ForeignKey("units.id"), index=True)
    vendor_id: Mapped[str | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="maintenance")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    recurrence_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    assignee_name: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
