from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.banking import (
    BankImportResult,
    BankTransactionCreate,
    BankTransactionMatchRequest,
    BankTransactionRead,
    BankTransactionUpdate,
)
from app.services.audit_log_service import AuditLogService
from app.services.banking_service import BankingService

router = APIRouter()
service = BankingService()
audit_service = AuditLogService()


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
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> BankTransactionRead:
    transaction = service.create_transaction(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="bank_transaction.created",
        resource_type="bank_transaction",
        resource_id=transaction.id,
        summary=f"Banktransaktion {transaction.id} angelegt",
        details={"amount": transaction.amount, "status": transaction.status},
    )
    return transaction


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
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> BankTransactionRead:
    transaction = service.update_transaction(
        db, current_user.organization_id, transaction_id, payload
    )
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="bank_transaction.updated",
        resource_type="bank_transaction",
        resource_id=transaction.id,
        summary=f"Banktransaktion {transaction.id} aktualisiert",
        details={"amount": transaction.amount, "status": transaction.status},
    )
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    transaction = service.get_transaction(db, current_user.organization_id, transaction_id)
    service.delete_transaction(db, current_user.organization_id, transaction_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="bank_transaction.deleted",
        resource_type="bank_transaction",
        resource_id=transaction_id,
        summary=f"Banktransaktion {transaction.id} gelöscht",
        details={"amount": float(transaction.amount), "status": transaction.status},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/transactions/{transaction_id}/match-payment",
    response_model=BankTransactionRead,
)
async def match_payment(
    transaction_id: str,
    payload: BankTransactionMatchRequest,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> BankTransactionRead:
    transaction = service.match_payment(db, current_user.organization_id, transaction_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="bank_transaction.matched",
        resource_type="bank_transaction",
        resource_id=transaction.id,
        summary=f"Banktransaktion {transaction.id} mit Zahlung verknüpft",
        details={"payment_id": transaction.payment_id},
    )
    return transaction


@router.post("/import-stub", response_model=BankImportResult)
async def import_stub_transactions(
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> BankImportResult:
    transactions = service.import_stub_transactions(db, current_user.organization_id)
    result = BankImportResult(imported_count=len(transactions), transactions=transactions)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="bank_transaction.stub_imported",
        resource_type="bank_transaction",
        resource_id=None,
        summary="Stub-Banktransaktionen importiert",
        details={"imported_count": result.imported_count},
    )
    return result


@router.post("/import", response_model=BankImportResult)
async def import_transactions(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> BankImportResult:
    file_bytes = await file.read()
    result = service.import_transactions(
        db,
        current_user.organization_id,
        file_name=file.filename or "bank-import",
        file_bytes=file_bytes,
    )
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="bank_transaction.imported",
        resource_type="bank_transaction",
        resource_id=None,
        summary=f"Bankdatei {file.filename or 'bank-import'} importiert",
        details={
            "imported_count": result.imported_count,
            "duplicate_count": result.duplicate_count,
            "matched_count": result.matched_count,
        },
    )
    return result
