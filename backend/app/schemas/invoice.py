from datetime import date

from pydantic import BaseModel


class InvoiceBase(BaseModel):
    property_id: str | None = None
    vendor_name: str
    invoice_number: str | None = None
    invoice_date: date | None = None
    gross_amount: float
    status: str = "draft"


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceRead(InvoiceBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
