from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.core.exceptions import PropertyHubError
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.document import (
    DocumentInvoiceApplyResult,
    DocumentOcrResult,
    DocumentRead,
    DocumentReviewUpdate,
)
from app.services.document_service import DocumentService
from app.tasks.document_tasks import process_document_ocr_job

router = APIRouter()
service = DocumentService()


@router.get("/", response_model=list[DocumentRead])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return service.list_documents(db, current_user.organization_id)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    return service.get_document(db, current_user.organization_id, document_id)


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    related_model: str = Form(...),
    related_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> DocumentRead:
    return service.upload_document(
        db,
        current_user.organization_id,
        related_model=related_model,
        related_id=related_id,
        document_type=document_type,
        file=file,
    )


@router.post(
    "/{document_id}/process-ocr",
    response_model=DocumentOcrResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_document_ocr(
    document_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> DocumentOcrResult:
    document = service.queue_ocr(db, current_user.organization_id, document_id)
    try:
        process_document_ocr_job.delay(current_user.organization_id, document_id)
    except Exception as exc:
        service.mark_ocr_failed(
            db, current_user.organization_id, document_id, f"Queueing failed: {exc}"
        )
        raise HTTPException(status_code=503, detail="OCR job could not be queued") from exc
    return DocumentOcrResult(document=document)


@router.post(
    "/{document_id}/retry-ocr",
    response_model=DocumentOcrResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_document_ocr(
    document_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> DocumentOcrResult:
    document = service.retry_ocr(db, current_user.organization_id, document_id)
    try:
        process_document_ocr_job.delay(current_user.organization_id, document_id)
    except Exception as exc:
        service.mark_ocr_failed(
            db, current_user.organization_id, document_id, f"Queueing failed: {exc}"
        )
        raise HTTPException(status_code=503, detail="OCR job could not be queued") from exc
    return DocumentOcrResult(document=document)


@router.post("/{document_id}/apply-ocr-to-invoice", response_model=DocumentInvoiceApplyResult)
async def apply_document_ocr_to_invoice(
    document_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> DocumentInvoiceApplyResult:
    document, invoice = service.apply_ocr_to_invoice(
        db, current_user.organization_id, document_id
    )
    return DocumentInvoiceApplyResult(document=document, invoice=invoice)


@router.patch("/{document_id}/review", response_model=DocumentRead)
async def review_document(
    document_id: str,
    payload: DocumentReviewUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> DocumentRead:
    return service.review_document(
        db,
        current_user.organization_id,
        document_id,
        current_user.id,
        payload,
    )
