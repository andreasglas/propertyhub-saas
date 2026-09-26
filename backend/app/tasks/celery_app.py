from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "propertyhub",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.document_tasks"],
)
celery_app.conf.task_default_queue = "propertyhub.default"
celery_app.conf.task_always_eager = settings.celery_task_always_eager
celery_app.conf.task_eager_propagates = settings.celery_task_eager_propagates
