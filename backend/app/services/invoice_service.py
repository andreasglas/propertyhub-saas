from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.invoice import Invoice
from app.db.models.organization import Organization
from app.db.models.payment_reminder import PaymentReminder
from app.db.models.property import Property
from app.schemas.invoice import InvoiceCreate, PaymentReminderCreate, PaymentReminderRead, OverdueInvoiceRead, InvoiceUpdate
from app.services.notification_service import NotificationService


class InvoiceService:
    def __init__(self) -> None:
        self.notification_service = NotificationService()

    def list_invoices(self, db: Session, organization_id: str) -> list[Invoice]:
        statement = (
            select(Invoice)
            .where(Invoice.organization_id == organization_id)
            .order_by(Invoice.created_at.desc())
        )
        return list(db.scalars(statement))

    def _ensure_property(
        self, db: Session, organization_id: str, property_id: str | None
    ) -> Property | None:
        if property_id is None:
            return None
        property_obj = db.scalar(
            select(Property).where(
                Property.id == property_id,
                Property.organization_id == organization_id,
            )
        )
        if property_obj is None:
            raise PropertyHubError("Property not found", status_code=404)
        return property_obj

    def get_invoice(self, db: Session, organization_id: str, invoice_id: str) -> Invoice:
        invoice = db.scalar(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.organization_id == organization_id,
            )
        )
        if invoice is None:
            raise PropertyHubError("Invoice not found", status_code=404)
        return invoice

    def list_overdue_invoices(
        self, db: Session, organization_id: str, *, reference_date: date | None = None
    ) -> list[OverdueInvoiceRead]:
        today = reference_date or date.today()
        invoices = list(
            db.scalars(
                select(Invoice)
                .where(
                    Invoice.organization_id == organization_id,
                    Invoice.due_date.is_not(None),
                    Invoice.due_date < today,
                    Invoice.status != "paid",
                )
                .order_by(Invoice.due_date.asc(), Invoice.created_at.desc())
            )
        )
        reminder_levels = self._latest_reminder_levels(db, organization_id)
        return [
            OverdueInvoiceRead(
                **self._invoice_payload(invoice),
                days_overdue=(today - invoice.due_date).days if invoice.due_date else 0,
                latest_reminder_level=reminder_levels.get(invoice.id, 0),
            )
            for invoice in invoices
        ]

    def list_reminders(
        self, db: Session, organization_id: str, invoice_id: str
    ) -> list[PaymentReminder]:
        self.get_invoice(db, organization_id, invoice_id)
        return list(
            db.scalars(
                select(PaymentReminder)
                .where(
                    PaymentReminder.organization_id == organization_id,
                    PaymentReminder.invoice_id == invoice_id,
                )
                .order_by(
                    PaymentReminder.reminder_level.desc(),
                    PaymentReminder.created_at.desc(),
                )
            )
        )

    def create_reminder(
        self,
        db: Session,
        organization_id: str,
        invoice_id: str,
        payload: PaymentReminderCreate,
    ) -> PaymentReminder:
        invoice = self.get_invoice(db, organization_id, invoice_id)
        organization = db.scalar(
            select(Organization).where(Organization.id == organization_id)
        )
        if organization is None:
            raise PropertyHubError("Organization not found", status_code=404)

        latest_level = (
            db.scalar(
                select(func.max(PaymentReminder.reminder_level)).where(
                    PaymentReminder.organization_id == organization_id,
                    PaymentReminder.invoice_id == invoice_id,
                )
            )
            or 0
        )
        reminder = PaymentReminder(
            organization_id=organization_id,
            invoice_id=invoice_id,
            recipient_email=str(payload.recipient_email),
            reminder_level=int(latest_level) + 1,
            status="pending",
            note=payload.note,
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        try:
            delivery_status = self.notification_service.send_payment_reminder(
                recipient_email=reminder.recipient_email,
                organization_name=organization.name,
                invoice_label=invoice.invoice_number or invoice.vendor_name,
                gross_amount=float(invoice.gross_amount),
                due_date=invoice.due_date.isoformat() if invoice.due_date else None,
                reminder_level=reminder.reminder_level,
                note=reminder.note,
            )
            reminder.status = delivery_status
            reminder.sent_at = datetime.now(timezone.utc) if delivery_status == "sent" else None
            reminder.delivery_error = None
        except Exception as exc:
            reminder.status = "failed"
            reminder.delivery_error = str(exc)[:1000]
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder

    def create_invoice(
        self, db: Session, organization_id: str, payload: InvoiceCreate
    ) -> Invoice:
        self._ensure_property(db, organization_id, payload.property_id)
        invoice = Invoice(organization_id=organization_id, **payload.model_dump())
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    def update_invoice(
        self,
        db: Session,
        organization_id: str,
        invoice_id: str,
        payload: InvoiceUpdate,
    ) -> Invoice:
        self._ensure_property(db, organization_id, payload.property_id)
        invoice = self.get_invoice(db, organization_id, invoice_id)
        for field, value in payload.model_dump().items():
            setattr(invoice, field, value)
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    def delete_invoice(self, db: Session, organization_id: str, invoice_id: str) -> None:
        invoice = self.get_invoice(db, organization_id, invoice_id)
        db.delete(invoice)
        db.commit()

    def _latest_reminder_levels(
        self, db: Session, organization_id: str
    ) -> dict[str, int]:
        rows = db.execute(
            select(PaymentReminder.invoice_id, func.max(PaymentReminder.reminder_level))
            .where(PaymentReminder.organization_id == organization_id)
            .group_by(PaymentReminder.invoice_id)
        ).all()
        return {invoice_id: int(level or 0) for invoice_id, level in rows}

    def _invoice_payload(self, invoice: Invoice) -> dict:
        return {
            "id": invoice.id,
            "organization_id": invoice.organization_id,
            "property_id": invoice.property_id,
            "vendor_name": invoice.vendor_name,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "gross_amount": float(invoice.gross_amount),
            "status": invoice.status,
        }
