from app.db.session import SessionLocal
from app.services.document_service import DocumentService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def process_document_ocr_job(organization_id: str, document_id: str) -> None:
    service = DocumentService()
    try:
        with SessionLocal() as db:
            service.process_ocr(db, organization_id, document_id)
    except Exception as exc:
        logger.exception(
            "document_ocr_failed",
            organization_id=organization_id,
            document_id=document_id,
            error=str(exc),
        )
        with SessionLocal() as db:
            service.mark_ocr_failed(db, organization_id, document_id, str(exc))
