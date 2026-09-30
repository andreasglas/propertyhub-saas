from pydantic import BaseModel


class DashboardReportRead(BaseModel):
    properties_count: int
    units_count: int
    tenants_count: int
    contracts_count: int
    invoices_count: int
    open_invoices_count: int
    open_tasks_count: int
    overdue_tasks_count: int
    completed_tasks_count: int
    payments_count: int
    accounting_entries_count: int
    total_invoice_amount: float
    total_payment_amount: float
    total_income_amount: float
    total_expense_amount: float
    total_estimated_task_cost: float
    total_actual_task_cost: float


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


class TaskReportRow(BaseModel):
    task_id: str
    title: str
    property_name: str | None = None
    unit_name: str | None = None
    vendor_name: str | None = None
    category: str
    priority: str
    status: str
    due_date: str | None = None
    completed_at: str | None = None
    estimated_cost: float | None = None
    actual_cost: float | None = None
    days_overdue: int
    source: str
