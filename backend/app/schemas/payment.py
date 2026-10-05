from datetime import date

from pydantic import BaseModel, Field, model_validator


class PaymentBase(BaseModel):
    invoice_id: str | None = None
    contract_id: str | None = None
    amount: float = Field(gt=0)
    booking_date: date | None = None
    reference: str | None = None

    @model_validator(mode="after")
    def validate_references(self) -> "PaymentBase":
        if self.invoice_id is None and self.contract_id is None:
            raise ValueError("invoice_id or contract_id must be provided")
        return self


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
