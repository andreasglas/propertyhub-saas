from app.tasks.celery_app import celery_app


@celery_app.task
def send_notification(notification_id: str) -> dict[str, str]:
    return {"notification_id": notification_id, "status": "queued"}
