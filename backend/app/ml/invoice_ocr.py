from io import BytesIO
from pathlib import Path
import re

from PIL import Image, ImageOps
from pypdf import PdfReader
import pypdfium2 as pdfium
import pytesseract

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def _extract_first(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def _decode_text_content(content: bytes | None) -> str:
    if not content:
        return ""
    return content.decode("utf-8", errors="ignore")


def _extract_pdf_text(content: bytes | None) -> str:
    if not content:
        return ""

    reader = PdfReader(BytesIO(content))
    return "\n".join(filter(None, (page.extract_text() or "" for page in reader.pages)))


def _ocr_image_bytes(content: bytes | None) -> tuple[str, bool]:
    if not content:
        return "", False
    try:
        image = Image.open(BytesIO(content))
        image = ImageOps.grayscale(image)
        text = pytesseract.image_to_string(image, config="--psm 6")
        return text, True
    except pytesseract.TesseractNotFoundError:
        return "", False


def _ocr_pdf_bytes(content: bytes | None, max_pages: int = 2) -> tuple[str, bool]:
    if not content:
        return "", False

    try:
        document = pdfium.PdfDocument(BytesIO(content))
        texts: list[str] = []
        try:
            for page_index in range(min(len(document), max_pages)):
                page = document[page_index]
                bitmap = page.render(scale=2)
                image = bitmap.to_pil()
                image = ImageOps.grayscale(image)
                texts.append(pytesseract.image_to_string(image, config="--psm 6"))
                page.close()
        finally:
            document.close()
        return "\n".join(filter(None, texts)), True
    except pytesseract.TesseractNotFoundError:
        return "", False


def _extract_text_for_file(file_name: str, content: bytes | None) -> tuple[str, str]:
    suffix = Path(file_name).suffix.lower()

    if suffix == ".pdf":
        pdf_text = _extract_pdf_text(content)
        if pdf_text.strip():
            return pdf_text, "pdf_text"

        ocr_text, ocr_available = _ocr_pdf_bytes(content)
        if ocr_text.strip():
            return ocr_text, "pdf_ocr"
        return "", "pdf_ocr_unavailable" if not ocr_available else "pdf_empty"

    if suffix in IMAGE_EXTENSIONS:
        ocr_text, ocr_available = _ocr_image_bytes(content)
        if ocr_text.strip():
            return ocr_text, "image_ocr"
        return "", "image_ocr_unavailable" if not ocr_available else "image_empty"

    text = _decode_text_content(content)
    return text, "content" if text.strip() else "filename"


def extract_invoice_metadata(
    file_name: str, content: bytes | None = None
) -> dict[str, str | float | None]:
    text, source = _extract_text_for_file(file_name, content)

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
        "source": source,
        "status": "processed",
    }
