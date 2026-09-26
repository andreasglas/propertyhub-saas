from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class Document(TenantScopedModel):
    __tablename__ = "documents"

    related_model: Mapped[str] = mapped_column(String(100), nullable=False)
    related_id: Mapped[str] = mapped_column(String(36), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    ocr_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    ocr_result: Mapped[dict | None] = mapped_column(JSON)
    ocr_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
