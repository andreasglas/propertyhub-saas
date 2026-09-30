from pydantic import BaseModel


class DashboardReportRead(BaseModel):
    properties_count: int
    units_count: int
    tenants_count: int
    contracts_count: int
    invoices_count: int
    open_invoices_count: int
    payments_count: int
    accounting_entries_count: int
    total_invoice_amount: float
    total_payment_amount: float
    total_income_amount: float
    total_expense_amount: float


class OpenInvoiceReportRow(BaseModel):
    invoice_id: str
    vendor_name: str
    invoice_number: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    gross_amount: float
    status: str
    days_overdue: int
    latest_reminder_level: int = 0
