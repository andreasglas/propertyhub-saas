from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TenantScopedModel


class Document(TenantScopedModel):
    __tablename__ = "documents"

    related_model: Mapped[str] = mapped_column(String(100), nullable=False)
    related_id: Mapped[str] = mapped_column(String(36), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    version_label: Mapped[str | None] = mapped_column(String(100))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    review_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[str | None] = mapped_column(String(36))
    ocr_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    ocr_error: Mapped[str | None] = mapped_column(Text)
    ocr_attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    ocr_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ocr_result: Mapped[dict | None] = mapped_column(JSON)
    ocr_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
