from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.accounting import AccountingEntry
from app.db.models.contract import Contract
from app.db.models.invoice import Invoice
from app.db.models.payment import Payment
from app.db.models.property import Property
from app.db.models.tenant import Tenant
from app.db.models.unit import Unit
from app.schemas.report import DashboardReportRead


class ReportService:
    def get_dashboard_summary(
        self, db: Session, organization_id: str
    ) -> DashboardReportRead:
        def count_for(model) -> int:
            return int(
                db.scalar(
                    select(func.count()).select_from(model).where(
                        model.organization_id == organization_id
                    )
                )
                or 0
            )

        def scalar_sum(statement) -> float:
            return float(db.scalar(statement) or 0)

        total_invoice_amount = scalar_sum(
            select(func.coalesce(func.sum(Invoice.gross_amount), 0)).where(
                Invoice.organization_id == organization_id
            )
        )
        total_payment_amount = scalar_sum(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.organization_id == organization_id
            )
        )
        total_income_amount = scalar_sum(
            select(func.coalesce(func.sum(AccountingEntry.amount), 0)).where(
                AccountingEntry.organization_id == organization_id,
                AccountingEntry.entry_type == "income",
            )
        )
        total_expense_amount = scalar_sum(
            select(func.coalesce(func.sum(AccountingEntry.amount), 0)).where(
                AccountingEntry.organization_id == organization_id,
                AccountingEntry.entry_type == "expense",
            )
        )
        open_invoices_count = int(
            db.scalar(
                select(func.count()).select_from(Invoice).where(
                    Invoice.organization_id == organization_id,
                    Invoice.status != "paid",
                )
            )
            or 0
        )

        return DashboardReportRead(
            properties_count=count_for(Property),
            units_count=count_for(Unit),
            tenants_count=count_for(Tenant),
            contracts_count=count_for(Contract),
            invoices_count=count_for(Invoice),
            open_invoices_count=open_invoices_count,
            payments_count=count_for(Payment),
            accounting_entries_count=count_for(AccountingEntry),
            total_invoice_amount=total_invoice_amount,
            total_payment_amount=total_payment_amount,
            total_income_amount=total_income_amount,
            total_expense_amount=total_expense_amount,
        )
