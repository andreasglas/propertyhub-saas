import csv
import io
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.accounting import AccountingEntry
from app.db.models.contract import Contract
from app.db.models.invoice import Invoice
from app.db.models.payment import Payment
from app.db.models.payment_reminder import PaymentReminder
from app.db.models.property import Property
from app.db.models.task import Task
from app.db.models.tenant import Tenant
from app.db.models.unit import Unit
from app.db.models.vendor import Vendor
from app.schemas.report import DashboardReportRead, OpenInvoiceReportRow, TaskReportRow


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
        open_tasks_count = int(
            db.scalar(
                select(func.count()).select_from(Task).where(
                    Task.organization_id == organization_id,
                    Task.status.in_(("open", "in_progress", "blocked")),
                )
            )
            or 0
        )
        completed_tasks_count = int(
            db.scalar(
                select(func.count()).select_from(Task).where(
                    Task.organization_id == organization_id,
                    Task.status == "done",
                )
            )
            or 0
        )
        overdue_tasks_count = int(
            db.scalar(
                select(func.count()).select_from(Task).where(
                    Task.organization_id == organization_id,
                    Task.status.in_(("open", "in_progress", "blocked")),
                    Task.due_date.is_not(None),
                    Task.due_date < date.today(),
                )
            )
            or 0
        )
        total_estimated_task_cost = scalar_sum(
            select(func.coalesce(func.sum(Task.estimated_cost), 0)).where(
                Task.organization_id == organization_id
            )
        )
        total_actual_task_cost = scalar_sum(
            select(func.coalesce(func.sum(Task.actual_cost), 0)).where(
                Task.organization_id == organization_id
            )
        )

        return DashboardReportRead(
            properties_count=count_for(Property),
            units_count=count_for(Unit),
            tenants_count=count_for(Tenant),
            contracts_count=count_for(Contract),
            invoices_count=count_for(Invoice),
            open_invoices_count=open_invoices_count,
            open_tasks_count=open_tasks_count,
            overdue_tasks_count=overdue_tasks_count,
            completed_tasks_count=completed_tasks_count,
            payments_count=count_for(Payment),
            accounting_entries_count=count_for(AccountingEntry),
            total_invoice_amount=total_invoice_amount,
            total_payment_amount=total_payment_amount,
            total_income_amount=total_income_amount,
            total_expense_amount=total_expense_amount,
            total_estimated_task_cost=total_estimated_task_cost,
            total_actual_task_cost=total_actual_task_cost,
        )

    def list_open_invoices(
        self, db: Session, organization_id: str, *, reference_date: date | None = None
    ) -> list[OpenInvoiceReportRow]:
        today = reference_date or date.today()
        invoices = list(
            db.scalars(
                select(Invoice)
                .where(
                    Invoice.organization_id == organization_id,
                    Invoice.status != "paid",
                )
                .order_by(Invoice.due_date.asc().nullslast(), Invoice.created_at.desc())
            )
        )
        reminder_levels = {
            invoice_id: int(level or 0)
            for invoice_id, level in db.execute(
                select(PaymentReminder.invoice_id, func.max(PaymentReminder.reminder_level))
                .where(PaymentReminder.organization_id == organization_id)
                .group_by(PaymentReminder.invoice_id)
            ).all()
        }
        rows: list[OpenInvoiceReportRow] = []
        for invoice in invoices:
            days_overdue = 0
            if invoice.due_date and invoice.due_date < today:
                days_overdue = (today - invoice.due_date).days
            rows.append(
                OpenInvoiceReportRow(
                    invoice_id=invoice.id,
                    vendor_name=invoice.vendor_name,
                    invoice_number=invoice.invoice_number,
                    invoice_date=invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                    due_date=invoice.due_date.isoformat() if invoice.due_date else None,
                    gross_amount=float(invoice.gross_amount),
                    status=invoice.status,
                    days_overdue=days_overdue,
                    latest_reminder_level=reminder_levels.get(invoice.id, 0),
                )
            )
        return rows

    def export_dashboard_summary_csv(self, summary: DashboardReportRead) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["metric", "value"])
        for key, value in summary.model_dump().items():
            writer.writerow([key, value])
        return output.getvalue()

    def export_open_invoices_csv(self, rows: list[OpenInvoiceReportRow]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "invoice_id",
                "vendor_name",
                "invoice_number",
                "invoice_date",
                "due_date",
                "gross_amount",
                "status",
                "days_overdue",
                "latest_reminder_level",
            ]
        )
        for row in rows:
            writer.writerow(list(row.model_dump().values()))
        return output.getvalue()

    def list_tasks_report(
        self, db: Session, organization_id: str, *, reference_date: date | None = None
    ) -> list[TaskReportRow]:
        today = reference_date or date.today()
        tasks = list(
            db.scalars(
                select(Task)
                .where(Task.organization_id == organization_id)
                .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
            )
        )
        property_names = {
            property_.id: property_.name
            for property_ in db.scalars(
                select(Property).where(Property.organization_id == organization_id)
            )
        }
        unit_names = {
            unit.id: unit.name
            for unit in db.scalars(select(Unit).where(Unit.organization_id == organization_id))
        }
        vendor_names = {
            vendor.id: vendor.name
            for vendor in db.scalars(select(Vendor).where(Vendor.organization_id == organization_id))
        }
        rows: list[TaskReportRow] = []
        for task in tasks:
            days_overdue = 0
            if task.due_date and task.status in {"open", "in_progress", "blocked"} and task.due_date < today:
                days_overdue = (today - task.due_date).days
            rows.append(
                TaskReportRow(
                    task_id=task.id,
                    title=task.title,
                    property_name=property_names.get(task.property_id or ""),
                    unit_name=unit_names.get(task.unit_id or ""),
                    vendor_name=vendor_names.get(task.vendor_id or ""),
                    category=task.category,
                    priority=task.priority,
                    status=task.status,
                    due_date=task.due_date.isoformat() if task.due_date else None,
                    completed_at=task.completed_at.isoformat() if task.completed_at else None,
                    estimated_cost=float(task.estimated_cost) if task.estimated_cost is not None else None,
                    actual_cost=float(task.actual_cost) if task.actual_cost is not None else None,
                    days_overdue=days_overdue,
                    source=task.source,
                )
            )
        return rows

    def export_tasks_csv(self, rows: list[TaskReportRow]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "task_id",
                "title",
                "property_name",
                "unit_name",
                "vendor_name",
                "category",
                "priority",
                "status",
                "due_date",
                "completed_at",
                "estimated_cost",
                "actual_cost",
                "days_overdue",
                "source",
            ]
        )
        for row in rows:
            writer.writerow(list(row.model_dump().values()))
        return output.getvalue()
