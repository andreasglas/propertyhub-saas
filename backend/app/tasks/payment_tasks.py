from app.tasks.celery_app import celery_app


@celery_app.task
def reconcile_payments(batch_id: str) -> dict[str, str]:
    return {"batch_id": batch_id, "status": "queued"}
