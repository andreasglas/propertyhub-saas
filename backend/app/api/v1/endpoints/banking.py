from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.banking import (
    BankImportResult,
    BankTransactionCreate,
    BankTransactionRead,
    BankTransactionUpdate,
)
from app.services.banking_service import BankingService

router = APIRouter()
service = BankingService()


@router.get("/", response_model=list[BankTransactionRead])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BankTransactionRead]:
    return service.list_transactions(db, current_user.organization_id)


@router.post(
    "/transactions", response_model=BankTransactionRead, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    payload: BankTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BankTransactionRead:
    return service.create_transaction(db, current_user.organization_id, payload)


@router.get("/transactions/{transaction_id}", response_model=BankTransactionRead)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BankTransactionRead:
    return service.get_transaction(db, current_user.organization_id, transaction_id)


@router.put("/transactions/{transaction_id}", response_model=BankTransactionRead)
async def update_transaction(
    transaction_id: str,
    payload: BankTransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BankTransactionRead:
    return service.update_transaction(
        db, current_user.organization_id, transaction_id, payload
    )


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service.delete_transaction(db, current_user.organization_id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/import-stub", response_model=BankImportResult)
async def import_stub_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BankImportResult:
    transactions = service.import_stub_transactions(db, current_user.organization_id)
    return BankImportResult(imported_count=len(transactions), transactions=transactions)
