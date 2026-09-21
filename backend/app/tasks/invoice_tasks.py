from app.tasks.celery_app import celery_app


@celery_app.task
def process_invoice_upload(document_id: str) -> dict[str, str]:
    return {"document_id": document_id, "status": "queued"}
