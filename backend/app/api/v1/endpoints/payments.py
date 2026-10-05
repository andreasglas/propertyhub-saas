from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.services.audit_log_service import AuditLogService
from app.services.payment_service import PaymentService

router = APIRouter()
service = PaymentService()
audit_service = AuditLogService()


@router.get("/", response_model=list[PaymentRead])
async def list_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PaymentRead]:
    return service.list_payments(db, current_user.organization_id)


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> PaymentRead:
    payment = service.create_payment(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="payment.created",
        resource_type="payment",
        resource_id=payment.id,
        summary=f"Zahlung {payment.id} angelegt",
        details={"amount": payment.amount, "invoice_id": payment.invoice_id, "contract_id": payment.contract_id},
    )
    return payment


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentRead:
    return service.get_payment(db, current_user.organization_id, payment_id)


@router.put("/{payment_id}", response_model=PaymentRead)
async def update_payment(
    payment_id: str,
    payload: PaymentUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> PaymentRead:
    payment = service.update_payment(db, current_user.organization_id, payment_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="payment.updated",
        resource_type="payment",
        resource_id=payment.id,
        summary=f"Zahlung {payment.id} aktualisiert",
        details={"amount": payment.amount, "invoice_id": payment.invoice_id, "contract_id": payment.contract_id},
    )
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    payment = service.get_payment(db, current_user.organization_id, payment_id)
    service.delete_payment(db, current_user.organization_id, payment_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="payment.deleted",
        resource_type="payment",
        resource_id=payment_id,
        summary=f"Zahlung {payment.id} gelöscht",
        details={"amount": float(payment.amount), "invoice_id": payment.invoice_id, "contract_id": payment.contract_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
