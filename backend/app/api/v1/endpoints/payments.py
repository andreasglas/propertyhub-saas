from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.services.payment_service import PaymentService

router = APIRouter()
service = PaymentService()


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
    return service.create_payment(db, current_user.organization_id, payload)


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
    return service.update_payment(db, current_user.organization_id, payment_id, payload)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    service.delete_payment(db, current_user.organization_id, payment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
