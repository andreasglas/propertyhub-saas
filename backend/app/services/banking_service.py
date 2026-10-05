from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.bank_transaction import BankTransaction
from app.db.models.invoice import Invoice
from app.db.models.payment import Payment
from app.schemas.banking import (
    BankTransactionCreate,
    BankImportResult,
    BankTransactionMatchRequest,
    BankTransactionUpdate,
)


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

    def import_transactions(
        self, db: Session, organization_id: str, *, file_name: str, file_bytes: bytes
    ) -> BankImportResult:
        if not file_bytes:
            raise PropertyHubError("Import file is empty", status_code=400)

        candidates = self._parse_import_file(file_name, file_bytes)
        if not candidates:
            return BankImportResult(imported_count=0, duplicate_count=0, matched_count=0, skipped_count=0, transactions=[])

        existing_signatures = self._existing_signatures(db, organization_id)
        matched_payment_ids = {
            payment_id
            for payment_id in db.scalars(
                select(BankTransaction.payment_id).where(
                    BankTransaction.organization_id == organization_id,
                    BankTransaction.payment_id.is_not(None),
                )
            )
            if payment_id
        }
        payment_candidates = self._load_payment_candidates(db, organization_id, matched_payment_ids)

        imported_transactions: list[BankTransaction] = []
        duplicate_count = 0
        skipped_count = 0
        matched_count = 0

        for candidate in candidates:
            signature = self._candidate_signature(candidate)
            if signature in existing_signatures:
                duplicate_count += 1
                continue

            payment_id = self._auto_match_payment(candidate, payment_candidates)
            transaction = BankTransaction(
                organization_id=organization_id,
                payment_id=payment_id,
                status="matched" if payment_id else "imported",
                **candidate,
            )
            db.add(transaction)
            db.flush()
            imported_transactions.append(transaction)
            existing_signatures.add(signature)

            if payment_id:
                matched_count += 1
                matched_payment_ids.add(payment_id)
                payment_candidates = [
                    current for current in payment_candidates if current["payment"].id != payment_id
                ]
            else:
                skipped_count += 0

        db.commit()
        for transaction in imported_transactions:
            db.refresh(transaction)

        return BankImportResult(
            imported_count=len(imported_transactions),
            duplicate_count=duplicate_count,
            matched_count=matched_count,
            skipped_count=skipped_count,
            transactions=imported_transactions,
        )

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

    def match_payment(
        self,
        db: Session,
        organization_id: str,
        transaction_id: str,
        payload: BankTransactionMatchRequest,
    ) -> BankTransaction:
        payment = self._ensure_payment(db, organization_id, payload.payment_id)
        transaction = self.get_transaction(db, organization_id, transaction_id)
        transaction.payment_id = payment.id
        transaction.status = "matched"
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

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

    def _parse_import_file(self, file_name: str, file_bytes: bytes) -> list[dict]:
        lower_name = file_name.lower()
        if lower_name.endswith(".csv"):
            return self._parse_csv(file_bytes)
        if lower_name.endswith(".xml") or lower_name.endswith(".camt"):
            return self._parse_camt(file_bytes)
        raise PropertyHubError("Unsupported bank import format", status_code=400)

    def _parse_csv(self, file_bytes: bytes) -> list[dict]:
        decoded = file_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        if reader.fieldnames is None:
            raise PropertyHubError("CSV header is missing", status_code=400)

        rows: list[dict] = []
        for row in reader:
            normalized = {self._normalize_header(key): (value or "").strip() for key, value in row.items()}
            if not any(normalized.values()):
                continue
            rows.append(
                {
                    "external_id": self._first_value(normalized, "external_id", "transaction_id", "entry_reference"),
                    "account_name": self._required_value(normalized, "account_name", "account", "konto"),
                    "transaction_type": self._first_value(normalized, "transaction_type", "type", "buchungstyp")
                    or "bank",
                    "booking_date": self._parse_date(
                        self._first_value(normalized, "booking_date", "buchungstag", "date")
                    ),
                    "value_date": self._parse_date(
                        self._first_value(normalized, "value_date", "wertstellung")
                    ),
                    "amount": self._parse_amount(
                        self._required_value(normalized, "amount", "betrag")
                    ),
                    "currency": self._first_value(normalized, "currency", "waehrung", "währung")
                    or "EUR",
                    "counterparty_name": self._first_value(
                        normalized, "counterparty_name", "name", "empfaenger", "payer"
                    ),
                    "iban": self._first_value(normalized, "iban"),
                    "reference": self._first_value(
                        normalized, "reference", "verwendungszweck", "purpose"
                    ),
                }
            )
        return rows

    def _parse_camt(self, file_bytes: bytes) -> list[dict]:
        try:
            root = ET.fromstring(file_bytes)
        except ET.ParseError as exc:
            raise PropertyHubError("Invalid CAMT XML file", status_code=400) from exc

        rows: list[dict] = []
        for entry in root.findall(".//{*}Ntry"):
            amount_node = entry.find("{*}Amt")
            amount_text = amount_node.text if amount_node is not None else None
            if not amount_text:
                continue

            tx_details = entry.find(".//{*}TxDtls")
            reference = self._xml_text(
                tx_details,
                "{*}Refs/{*}AcctSvcrRef",
                "{*}RmtInf/{*}Ustrd",
            ) or self._xml_text(entry, "{*}AddtlNtryInf")
            counterparty_name = self._xml_text(
                tx_details,
                "{*}RltdPties/{*}Cdtr/{*}Nm",
                "{*}RltdPties/{*}Dbtr/{*}Nm",
            )
            iban = self._xml_text(
                tx_details,
                "{*}RltdPties/{*}CdtrAcct/{*}Id/{*}IBAN",
                "{*}RltdPties/{*}DbtrAcct/{*}Id/{*}IBAN",
            )

            rows.append(
                {
                    "external_id": self._xml_text(entry, "{*}NtryRef")
                    or self._xml_text(tx_details, "{*}Refs/{*}AcctSvcrRef"),
                    "account_name": "CAMT Import",
                    "transaction_type": (
                        "credit"
                        if (self._xml_text(entry, "{*}CdtDbtInd") or "").upper() == "CRDT"
                        else "debit"
                    ),
                    "booking_date": self._parse_date(self._xml_text(entry, "{*}BookgDt/{*}Dt")),
                    "value_date": self._parse_date(self._xml_text(entry, "{*}ValDt/{*}Dt")),
                    "amount": self._parse_amount(amount_text),
                    "currency": amount_node.attrib.get("Ccy", "EUR") if amount_node is not None else "EUR",
                    "counterparty_name": counterparty_name,
                    "iban": iban,
                    "reference": reference,
                }
            )
        return rows

    def _load_payment_candidates(
        self, db: Session, organization_id: str, matched_payment_ids: set[str]
    ) -> list[dict]:
        rows = db.execute(
            select(Payment, Invoice.invoice_number)
            .outerjoin(Invoice, Payment.invoice_id == Invoice.id)
            .where(Payment.organization_id == organization_id)
        ).all()
        return [
            {
                "payment": payment,
                "invoice_number": invoice_number,
            }
            for payment, invoice_number in rows
            if payment.id not in matched_payment_ids
        ]

    def _auto_match_payment(self, candidate: dict, payment_candidates: list[dict]) -> str | None:
        amount = round(float(candidate["amount"]), 2)
        reference = self._normalize_text(candidate.get("reference"))
        booking_date = candidate.get("booking_date")

        scored_candidates: list[tuple[int, str]] = []
        for item in payment_candidates:
            payment = item["payment"]
            if round(float(payment.amount), 2) != amount:
                continue

            score = 0
            payment_reference = self._normalize_text(payment.reference)
            invoice_number = self._normalize_text(item.get("invoice_number"))
            if reference and payment_reference and (
                payment_reference in reference or reference in payment_reference
            ):
                score += 3
            if reference and invoice_number and invoice_number in reference:
                score += 3
            if booking_date and payment.booking_date and booking_date == payment.booking_date:
                score += 1
            if booking_date and payment.booking_date and abs((booking_date - payment.booking_date).days) <= 7:
                score += 1

            if score > 0:
                scored_candidates.append((score, payment.id))

        if not scored_candidates:
            return None

        scored_candidates.sort(reverse=True)
        best_score, best_payment_id = scored_candidates[0]
        competing = [candidate for candidate in scored_candidates if candidate[0] == best_score]
        if len(competing) > 1:
            return None
        return best_payment_id

    def _existing_signatures(self, db: Session, organization_id: str) -> set[str]:
        transactions = db.scalars(
            select(BankTransaction).where(BankTransaction.organization_id == organization_id)
        )
        return {self._transaction_signature(transaction) for transaction in transactions}

    def _transaction_signature(self, transaction: BankTransaction) -> str:
        if transaction.external_id:
            return "external:" + transaction.external_id.strip().lower()
        return self._fingerprint(
            booking_date=transaction.booking_date,
            value_date=transaction.value_date,
            amount=float(transaction.amount),
            counterparty_name=transaction.counterparty_name,
            reference=transaction.reference,
        )

    def _candidate_signature(self, candidate: dict) -> str:
        external_id = candidate.get("external_id")
        if external_id:
            return "external:" + str(external_id).strip().lower()
        return self._fingerprint(
            booking_date=candidate.get("booking_date"),
            value_date=candidate.get("value_date"),
            amount=float(candidate["amount"]),
            counterparty_name=candidate.get("counterparty_name"),
            reference=candidate.get("reference"),
        )

    def _fingerprint(
        self,
        *,
        booking_date: date | None,
        value_date: date | None,
        amount: float,
        counterparty_name: str | None,
        reference: str | None,
    ) -> str:
        return "|".join(
            [
                booking_date.isoformat() if booking_date else "",
                value_date.isoformat() if value_date else "",
                f"{amount:.2f}",
                self._normalize_text(counterparty_name),
                self._normalize_text(reference),
            ]
        )

    def _required_value(self, row: dict[str, str], *keys: str) -> str:
        value = self._first_value(row, *keys)
        if not value:
            raise PropertyHubError(
                "Bank import file is missing required columns or values", status_code=400
            )
        return value

    def _first_value(self, row: dict[str, str], *keys: str) -> str | None:
        for key in keys:
            value = row.get(key)
            if value:
                return value
        return None

    def _normalize_header(self, header: str | None) -> str:
        return (
            (header or "")
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    def _parse_amount(self, raw: str) -> float:
        normalized = raw.strip().replace(" ", "")
        if "." in normalized and "," in normalized:
            if normalized.rfind(",") > normalized.rfind("."):
                normalized = normalized.replace(".", "").replace(",", ".")
            else:
                normalized = normalized.replace(",", "")
        elif "," in normalized:
            normalized = normalized.replace(",", ".")
        try:
            value = float(normalized)
        except ValueError as exc:
            raise PropertyHubError("Invalid amount in bank import", status_code=400) from exc
        return abs(value)

    def _parse_date(self, raw: str | None) -> date | None:
        if not raw:
            return None
        text = raw.strip()
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y%m%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        raise PropertyHubError("Invalid date in bank import", status_code=400)

    def _normalize_text(self, value: str | None) -> str:
        return (value or "").strip().lower()

    def _xml_text(self, node: ET.Element | None, *paths: str) -> str | None:
        if node is None:
            return None
        for path in paths:
            value = node.findtext(path)
            if value and value.strip():
                return value.strip()
        return None
