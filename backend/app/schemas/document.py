from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: str
    organization_id: str
    related_model: str
    related_id: str
    document_type: str
    file_name: str
    storage_path: str | None = None
    ocr_status: str
    ocr_result: dict[str, Any] | None = None
    ocr_processed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentOcrResult(BaseModel):
    document: DocumentRead
