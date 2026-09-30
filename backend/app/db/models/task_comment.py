from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class TaskComment(TenantScopedModel):
    __tablename__ = "task_comments"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    author_user_id: Mapped[str | None] = mapped_column(String(36))
    author_email: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text, nullable=False)
