from app.tasks.celery_app import celery_app
from app.ml.invoice_ocr import extract_invoice_metadata


@celery_app.task
def process_invoice_upload(document_id: str) -> dict[str, str]:
    result = extract_invoice_metadata(file_name=document_id)
    return {"document_id": document_id, "status": "queued", "source": str(result["source"])}
