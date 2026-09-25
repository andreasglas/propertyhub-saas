from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.invoice import Invoice
from app.db.models.property import Property
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
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
