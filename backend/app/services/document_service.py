from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import PropertyHubError
from app.db.models.document import Document
from app.db.models.invoice import Invoice
from app.db.models.property import Property
from app.ml.invoice_ocr import extract_invoice_metadata


class DocumentService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _storage_dir(self) -> Path:
        storage_dir = self.settings.document_storage_path
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir

    def _validate_related_entity(
        self, db: Session, organization_id: str, related_model: str, related_id: str
    ) -> None:
        model_map = {
            "invoice": Invoice,
            "property": Property,
        }
        model = model_map.get(related_model)
        if model is None:
            raise PropertyHubError("Unsupported related model", status_code=400)

        entity = db.scalar(
            select(model).where(model.id == related_id, model.organization_id == organization_id)
        )
        if entity is None:
            raise PropertyHubError(f"{related_model.title()} not found", status_code=404)

    def list_documents(self, db: Session, organization_id: str) -> list[Document]:
        statement = (
            select(Document)
            .where(Document.organization_id == organization_id)
            .order_by(Document.created_at.desc())
        )
        return list(db.scalars(statement))

    def get_document(self, db: Session, organization_id: str, document_id: str) -> Document:
        document = db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.organization_id == organization_id,
            )
        )
        if document is None:
            raise PropertyHubError("Document not found", status_code=404)
        return document

    def upload_document(
        self,
        db: Session,
        organization_id: str,
        *,
        related_model: str,
        related_id: str,
        document_type: str,
        file: UploadFile,
    ) -> Document:
        self._validate_related_entity(db, organization_id, related_model, related_id)
        safe_name = Path(file.filename or "document.bin").name
        if not safe_name:
            raise PropertyHubError("File name is required", status_code=400)

        content = file.file.read()
        if not content:
            raise PropertyHubError("Uploaded file is empty", status_code=400)

        target_dir = self._storage_dir() / organization_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{uuid4()}-{safe_name}"
        target_path.write_bytes(content)

        document = Document(
            organization_id=organization_id,
            related_model=related_model,
            related_id=related_id,
            document_type=document_type,
            file_name=safe_name,
            storage_path=str(target_path),
            ocr_status="pending",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    def process_ocr(self, db: Session, organization_id: str, document_id: str) -> Document:
        document = self.get_document(db, organization_id, document_id)
        if not document.storage_path:
            raise PropertyHubError("Document storage path missing", status_code=400)

        file_path = Path(document.storage_path)
        if not file_path.exists():
            raise PropertyHubError("Document file not found", status_code=404)

        result = extract_invoice_metadata(document.file_name, file_path.read_bytes())
        document.ocr_status = "processed"
        document.ocr_result = result
        document.ocr_processed_at = datetime.now(timezone.utc)
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    def apply_ocr_to_invoice(
        self, db: Session, organization_id: str, document_id: str
    ) -> tuple[Document, Invoice]:
        document = self.get_document(db, organization_id, document_id)
        if document.related_model != "invoice":
            raise PropertyHubError(
                "OCR application is only supported for invoice documents",
                status_code=400,
            )
        if document.ocr_status != "processed" or not document.ocr_result:
            raise PropertyHubError("Document OCR must be processed first", status_code=400)

        invoice = db.scalar(
            select(Invoice).where(
                Invoice.id == document.related_id,
                Invoice.organization_id == organization_id,
            )
        )
        if invoice is None:
            raise PropertyHubError("Invoice not found", status_code=404)

        ocr_result = document.ocr_result
        vendor_name = ocr_result.get("vendor_name")
        if isinstance(vendor_name, str) and vendor_name.strip():
            invoice.vendor_name = vendor_name.strip()

        invoice_number = ocr_result.get("invoice_number")
        if isinstance(invoice_number, str) and invoice_number.strip():
            invoice.invoice_number = invoice_number.strip()

        invoice_date = ocr_result.get("invoice_date")
        if isinstance(invoice_date, str) and invoice_date.strip():
            invoice.invoice_date = date.fromisoformat(invoice_date)

        gross_amount = ocr_result.get("gross_amount")
        if isinstance(gross_amount, int | float) and gross_amount > 0:
            invoice.gross_amount = float(gross_amount)

        if invoice.status == "draft":
            invoice.status = "received"

        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        db.refresh(document)
        return document, invoice
