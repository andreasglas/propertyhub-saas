from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.accounting import AccountingEntry
from app.db.models.property import Property
from app.schemas.accounting import AccountingEntryCreate, AccountingEntryUpdate


class AccountingService:
    def list_entries(self, db: Session, organization_id: str) -> list[AccountingEntry]:
        statement = (
            select(AccountingEntry)
            .where(AccountingEntry.organization_id == organization_id)
            .order_by(AccountingEntry.created_at.desc())
        )
        return list(db.scalars(statement))

    def _ensure_property(
        self, db: Session, organization_id: str, property_id: str | None
    ) -> Property | None:
        if property_id is None:
            return None
        property_obj = db.scalar(
            select(Property).where(
                Property.id == property_id,
                Property.organization_id == organization_id,
            )
        )
        if property_obj is None:
            raise PropertyHubError("Property not found", status_code=404)
        return property_obj

    def get_entry(
        self, db: Session, organization_id: str, entry_id: str
    ) -> AccountingEntry:
        entry = db.scalar(
            select(AccountingEntry).where(
                AccountingEntry.id == entry_id,
                AccountingEntry.organization_id == organization_id,
            )
        )
        if entry is None:
            raise PropertyHubError("Accounting entry not found", status_code=404)
        return entry

    def create_entry(
        self, db: Session, organization_id: str, payload: AccountingEntryCreate
    ) -> AccountingEntry:
        self._ensure_property(db, organization_id, payload.property_id)
        entry = AccountingEntry(organization_id=organization_id, **payload.model_dump())
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def update_entry(
        self,
        db: Session,
        organization_id: str,
        entry_id: str,
        payload: AccountingEntryUpdate,
    ) -> AccountingEntry:
        self._ensure_property(db, organization_id, payload.property_id)
        entry = self.get_entry(db, organization_id, entry_id)
        for field, value in payload.model_dump().items():
            setattr(entry, field, value)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def delete_entry(self, db: Session, organization_id: str, entry_id: str) -> None:
        entry = self.get_entry(db, organization_id, entry_id)
        db.delete(entry)
        db.commit()
