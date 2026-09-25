from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.contract import Contract
from app.db.models.invoice import Invoice
from app.db.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate


class PaymentService:
    def list_payments(self, db: Session, organization_id: str) -> list[Payment]:
        statement = (
            select(Payment)
            .where(Payment.organization_id == organization_id)
            .order_by(Payment.created_at.desc())
        )
        return list(db.scalars(statement))

    def _ensure_invoice(
        self, db: Session, organization_id: str, invoice_id: str | None
    ) -> Invoice | None:
        if invoice_id is None:
            return None
        invoice = db.scalar(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.organization_id == organization_id,
            )
        )
        if invoice is None:
            raise PropertyHubError("Invoice not found", status_code=404)
        return invoice

    def _ensure_contract(
        self, db: Session, organization_id: str, contract_id: str | None
    ) -> Contract | None:
        if contract_id is None:
            return None
        contract = db.scalar(
            select(Contract).where(
                Contract.id == contract_id,
                Contract.organization_id == organization_id,
            )
        )
        if contract is None:
            raise PropertyHubError("Contract not found", status_code=404)
        return contract

    def get_payment(self, db: Session, organization_id: str, payment_id: str) -> Payment:
        payment = db.scalar(
            select(Payment).where(
                Payment.id == payment_id,
                Payment.organization_id == organization_id,
            )
        )
        if payment is None:
            raise PropertyHubError("Payment not found", status_code=404)
        return payment

    def create_payment(
        self, db: Session, organization_id: str, payload: PaymentCreate
    ) -> Payment:
        self._ensure_invoice(db, organization_id, payload.invoice_id)
        self._ensure_contract(db, organization_id, payload.contract_id)
        payment = Payment(organization_id=organization_id, **payload.model_dump())
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def update_payment(
        self,
        db: Session,
        organization_id: str,
        payment_id: str,
        payload: PaymentUpdate,
    ) -> Payment:
        self._ensure_invoice(db, organization_id, payload.invoice_id)
        self._ensure_contract(db, organization_id, payload.contract_id)
        payment = self.get_payment(db, organization_id, payment_id)
        for field, value in payload.model_dump().items():
            setattr(payment, field, value)
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def delete_payment(self, db: Session, organization_id: str, payment_id: str) -> None:
        payment = self.get_payment(db, organization_id, payment_id)
        db.delete(payment)
        db.commit()
