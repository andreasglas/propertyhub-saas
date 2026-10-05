from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.accounting import (
    AccountingEntryCreate,
    AccountingEntryRead,
    AccountingEntryUpdate,
)
from app.services.audit_log_service import AuditLogService
from app.services.accounting_service import AccountingService

router = APIRouter()
service = AccountingService()
audit_service = AuditLogService()


@router.get("/", response_model=list[AccountingEntryRead])
async def list_accounting_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AccountingEntryRead]:
    return service.list_entries(db, current_user.organization_id)


@router.post("/", response_model=AccountingEntryRead, status_code=status.HTTP_201_CREATED)
async def create_accounting_entry(
    payload: AccountingEntryCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> AccountingEntryRead:
    entry = service.create_entry(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="accounting.created",
        resource_type="accounting_entry",
        resource_id=entry.id,
        summary=f"Accounting-Eintrag {entry.id} angelegt",
        details={"entry_type": entry.entry_type, "category": entry.category},
    )
    return entry


@router.get("/{entry_id}", response_model=AccountingEntryRead)
async def get_accounting_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountingEntryRead:
    return service.get_entry(db, current_user.organization_id, entry_id)


@router.put("/{entry_id}", response_model=AccountingEntryRead)
async def update_accounting_entry(
    entry_id: str,
    payload: AccountingEntryUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> AccountingEntryRead:
    entry = service.update_entry(db, current_user.organization_id, entry_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="accounting.updated",
        resource_type="accounting_entry",
        resource_id=entry.id,
        summary=f"Accounting-Eintrag {entry.id} aktualisiert",
        details={"entry_type": entry.entry_type, "category": entry.category},
    )
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accounting_entry(
    entry_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    entry = service.get_entry(db, current_user.organization_id, entry_id)
    service.delete_entry(db, current_user.organization_id, entry_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="accounting.deleted",
        resource_type="accounting_entry",
        resource_id=entry_id,
        summary=f"Accounting-Eintrag {entry.id} gelöscht",
        details={"entry_type": entry.entry_type, "category": entry.category},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
