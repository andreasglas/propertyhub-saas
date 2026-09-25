from datetime import date

from pydantic import BaseModel, Field


class InvoiceBase(BaseModel):
    property_id: str | None = None
    vendor_name: str
    invoice_number: str | None = None
    invoice_date: date | None = None
    gross_amount: float = Field(gt=0)
    status: str = "draft"


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(InvoiceBase):
    pass


class InvoiceRead(InvoiceBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
