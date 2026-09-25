from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.bank_transaction import BankTransaction
from app.db.models.payment import Payment
from app.schemas.banking import BankTransactionCreate, BankTransactionUpdate


class BankingService:
    def list_transactions(
        self, db: Session, organization_id: str
    ) -> list[BankTransaction]:
        statement = (
            select(BankTransaction)
            .where(BankTransaction.organization_id == organization_id)
            .order_by(BankTransaction.booking_date.desc(), BankTransaction.created_at.desc())
        )
        return list(db.scalars(statement))

    def _ensure_payment(
        self, db: Session, organization_id: str, payment_id: str | None
    ) -> Payment | None:
        if payment_id is None:
            return None
        payment = db.scalar(
            select(Payment).where(
                Payment.id == payment_id,
                Payment.organization_id == organization_id,
            )
        )
        if payment is None:
            raise PropertyHubError("Payment not found", status_code=404)
        return payment

    def get_transaction(
        self, db: Session, organization_id: str, transaction_id: str
    ) -> BankTransaction:
        transaction = db.scalar(
            select(BankTransaction).where(
                BankTransaction.id == transaction_id,
                BankTransaction.organization_id == organization_id,
            )
        )
        if transaction is None:
            raise PropertyHubError("Bank transaction not found", status_code=404)
        return transaction

    def create_transaction(
        self, db: Session, organization_id: str, payload: BankTransactionCreate
    ) -> BankTransaction:
        self._ensure_payment(db, organization_id, payload.payment_id)
        transaction = BankTransaction(
            organization_id=organization_id, **payload.model_dump()
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    def update_transaction(
        self,
        db: Session,
        organization_id: str,
        transaction_id: str,
        payload: BankTransactionUpdate,
    ) -> BankTransaction:
        self._ensure_payment(db, organization_id, payload.payment_id)
        transaction = self.get_transaction(db, organization_id, transaction_id)
        for field, value in payload.model_dump().items():
            setattr(transaction, field, value)
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    def delete_transaction(
        self, db: Session, organization_id: str, transaction_id: str
    ) -> None:
        transaction = self.get_transaction(db, organization_id, transaction_id)
        db.delete(transaction)
        db.commit()

    def import_stub_transactions(
        self, db: Session, organization_id: str
    ) -> list[BankTransaction]:
        samples = [
            BankTransaction(
                organization_id=organization_id,
                external_id="stub-001",
                account_name="Geschäftskonto",
                transaction_type="credit",
                booking_date=date(2026, 12, 1),
                value_date=date(2026, 12, 1),
                amount=1350.00,
                currency="EUR",
                counterparty_name="Max Mustermann",
                iban="DE44500105175407324931",
                reference="Miete Dezember Wohnung 2B",
                status="imported",
            ),
            BankTransaction(
                organization_id=organization_id,
                external_id="stub-002",
                account_name="Geschäftskonto",
                transaction_type="debit",
                booking_date=date(2026, 12, 2),
                value_date=date(2026, 12, 2),
                amount=420.00,
                currency="EUR",
                counterparty_name="Stadtwerke Hamburg",
                iban="DE89370400440532013000",
                reference="Abschlag Energie",
                status="imported",
            ),
        ]
        db.add_all(samples)
        db.commit()
        for sample in samples:
            db.refresh(sample)
        return samples
