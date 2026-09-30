from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.invoice import InvoiceRead


class DocumentRead(BaseModel):
    id: str
    organization_id: str
    created_at: datetime | None = None
    related_model: str
    related_id: str
    document_type: str
    category: str | None = None
    version_label: str | None = None
    file_name: str
    storage_path: str | None = None
    review_status: str
    review_notes: str | None = None
    reviewed_at: datetime | None = None
    reviewed_by: str | None = None
    ocr_status: str
    ocr_error: str | None = None
    ocr_attempt_count: int
    ocr_started_at: datetime | None = None
    ocr_result: dict[str, Any] | None = None
    ocr_processed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentOcrResult(BaseModel):
    document: DocumentRead


class DocumentInvoiceApplyResult(BaseModel):
    document: DocumentRead
    invoice: InvoiceRead


class DocumentReviewUpdate(BaseModel):
    category: str | None = None
    version_label: str | None = None
    review_status: str
    review_notes: str | None = None
