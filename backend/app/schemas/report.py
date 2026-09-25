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
