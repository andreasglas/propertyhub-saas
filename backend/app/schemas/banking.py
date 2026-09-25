from datetime import date

from pydantic import BaseModel, Field


class BankTransactionBase(BaseModel):
    payment_id: str | None = None
    external_id: str | None = None
    account_name: str
    transaction_type: str = "bank"
    booking_date: date | None = None
    value_date: date | None = None
    amount: float = Field(..., gt=0)
    currency: str = "EUR"
    counterparty_name: str | None = None
    iban: str | None = None
    reference: str | None = None
    status: str = "imported"


class BankTransactionCreate(BankTransactionBase):
    pass


class BankTransactionUpdate(BankTransactionBase):
    pass


class BankTransactionRead(BankTransactionBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}


class BankTransactionMatchRequest(BaseModel):
    payment_id: str


class BankImportResult(BaseModel):
    imported_count: int
    transactions: list[BankTransactionRead]
