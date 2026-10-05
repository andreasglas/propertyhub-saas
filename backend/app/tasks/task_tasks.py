from datetime import date

from app.db.session import SessionLocal
from app.services.task_service import TaskService
from app.tasks.celery_app import celery_app
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="tasks.generate_due_recurring_tasks")
def generate_due_recurring_tasks_job(reference_date: str | None = None) -> dict[str, object]:
    target_date = date.fromisoformat(reference_date) if reference_date else date.today()
    with SessionLocal() as db:
        summary = TaskService().generate_due_tasks_for_all_organizations(db, today=target_date)

    generated_count = sum(summary.values())
    logger.info(
        "generated_due_recurring_tasks",
        reference_date=target_date.isoformat(),
        generated_count=generated_count,
        organization_counts=summary,
    )
    return {
        "reference_date": target_date.isoformat(),
        "generated_count": generated_count,
        "organization_counts": summary,
    }
