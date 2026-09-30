from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class Task(TenantScopedModel):
    __tablename__ = "tasks"

    property_id: Mapped[str | None] = mapped_column(ForeignKey("properties.id"), index=True)
    unit_id: Mapped[str | None] = mapped_column(ForeignKey("units.id"), index=True)
    vendor_id: Mapped[str | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    recurring_template_id: Mapped[str | None] = mapped_column(
        ForeignKey("task_templates.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="maintenance")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    due_date: Mapped[date | None] = mapped_column(Date)
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(10, 2))
    actual_cost: Mapped[float | None] = mapped_column(Numeric(10, 2))
    assignee_name: Mapped[str | None] = mapped_column(String(255))
    completion_notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
