from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class InvoiceBase(BaseModel):
    property_id: str | None = None
    vendor_name: str
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
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


class PaymentReminderCreate(BaseModel):
    recipient_email: EmailStr
    note: str | None = None


class PaymentReminderRead(BaseModel):
    id: str
    organization_id: str
    invoice_id: str
    recipient_email: EmailStr
    reminder_level: int
    status: str
    note: str | None = None
    sent_at: datetime | None = None
    delivery_error: str | None = None

    model_config = {"from_attributes": True}


class OverdueInvoiceRead(InvoiceRead):
    days_overdue: int
    latest_reminder_level: int = 0
