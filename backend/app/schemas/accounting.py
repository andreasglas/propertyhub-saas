from datetime import date

from pydantic import BaseModel, Field


class AccountingEntryBase(BaseModel):
    property_id: str | None = None
    entry_type: str
    category: str | None = None
    amount: float = Field(gt=0)
    booking_date: date | None = None


class AccountingEntryCreate(AccountingEntryBase):
    pass


class AccountingEntryUpdate(AccountingEntryBase):
    pass


class AccountingEntryRead(AccountingEntryBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
