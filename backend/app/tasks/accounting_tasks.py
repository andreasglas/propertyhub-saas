from app.tasks.celery_app import celery_app


@celery_app.task
def build_monthly_report(period: str) -> dict[str, str]:
    return {"period": period, "status": "queued"}
