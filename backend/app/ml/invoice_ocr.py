from pathlib import Path
import re


def _extract_first(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def extract_invoice_metadata(file_name: str, content: bytes | None = None) -> dict[str, str | float | None]:
    text = ""
    if content:
        text = content.decode("utf-8", errors="ignore")

    vendor_name = _extract_first(
        [
            r"(?:vendor|lieferant)\s*[:\-]\s*(.+)",
            r"(?:company|firma)\s*[:\-]\s*(.+)",
        ],
        text,
    )
    invoice_number = _extract_first(
        [
            r"(?:invoice number|rechnungsnummer|invoice no\.?)\s*[:\-]\s*(.+)",
            r"(?:belegnummer)\s*[:\-]\s*(.+)",
        ],
        text,
    )
    invoice_date = _extract_first(
        [
            r"(?:invoice date|rechnungsdatum|date)\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",
        ],
        text,
    )
    amount_text = _extract_first(
        [
            r"(?:gross amount|bruttobetrag|amount)\s*[:\-]\s*(\d+(?:[.,]\d{1,2})?)",
        ],
        text,
    )

    stem = Path(file_name).stem.replace("-", " ").replace("_", " ")
    if vendor_name is None and stem:
        vendor_name = stem.title()

    gross_amount = None
    if amount_text:
        gross_amount = float(amount_text.replace(",", "."))

    matched_fields = sum(
        value is not None for value in [vendor_name, invoice_number, invoice_date, gross_amount]
    )
    confidence = round(matched_fields / 4, 2)

    return {
        "vendor_name": vendor_name,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "gross_amount": gross_amount,
        "confidence": confidence,
        "source": "content" if text.strip() else "filename",
        "status": "processed",
    }
