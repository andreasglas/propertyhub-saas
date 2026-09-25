from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceRead, InvoiceUpdate
from app.services.invoice_service import InvoiceService

router = APIRouter()
service = InvoiceService()


@router.get("/", response_model=list[InvoiceRead])
async def list_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InvoiceRead]:
    return service.list_invoices(db, current_user.organization_id)


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> InvoiceRead:
    return service.create_invoice(db, current_user.organization_id, payload)


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvoiceRead:
    return service.get_invoice(db, current_user.organization_id, invoice_id)


@router.put("/{invoice_id}", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: str,
    payload: InvoiceUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> InvoiceRead:
    return service.update_invoice(db, current_user.organization_id, invoice_id, payload)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    service.delete_invoice(db, current_user.organization_id, invoice_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
