from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.document import DocumentRead
from app.schemas.task import (
    GeneratedTasksResult,
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskHistoryEntry,
    TaskRead,
    TaskTemplateCreate,
    TaskTemplateRead,
    TaskTemplateUpdate,
    TaskUpdate,
)
from app.services.audit_log_service import AuditLogService
from app.services.task_service import TaskService

router = APIRouter()
service = TaskService()
audit_service = AuditLogService()


@router.get("/templates", response_model=list[TaskTemplateRead])
async def list_task_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskTemplateRead]:
    return service.list_templates(db, current_user.organization_id)


@router.post("/templates", response_model=TaskTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_task_template(
    payload: TaskTemplateCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> TaskTemplateRead:
    template = service.create_template(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="task_template.created",
        resource_type="task_template",
        resource_id=template.id,
        summary=f"Wiederkehrende Aufgabe {template.title} angelegt",
        details={"frequency": template.recurrence_frequency, "next_due_date": template.next_due_date},
    )
    return template


@router.put("/templates/{template_id}", response_model=TaskTemplateRead)
async def update_task_template(
    template_id: str,
    payload: TaskTemplateUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> TaskTemplateRead:
    template = service.update_template(db, current_user.organization_id, template_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="task_template.updated",
        resource_type="task_template",
        resource_id=template.id,
        summary=f"Wiederkehrende Aufgabe {template.title} aktualisiert",
        details={"frequency": template.recurrence_frequency, "next_due_date": template.next_due_date},
    )
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_template(
    template_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    template = service.get_template(db, current_user.organization_id, template_id)
    service.delete_template(db, current_user.organization_id, template_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="task_template.deleted",
        resource_type="task_template",
        resource_id=template_id,
        summary=f"Wiederkehrende Aufgabe {template.title} gelöscht",
        details={"frequency": template.recurrence_frequency},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/templates/generate-due", response_model=GeneratedTasksResult)
async def generate_due_tasks(
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> GeneratedTasksResult:
    tasks = service.generate_due_tasks(db, current_user.organization_id)
    if tasks:
        audit_service.record(
            db,
            organization_id=current_user.organization_id,
            actor=current_user,
            action="task_template.generated",
            resource_type="task_template",
            resource_id=None,
            summary=f"{len(tasks)} wiederkehrende Aufgaben erzeugt",
            details={"task_ids": [task.id for task in tasks]},
        )
    return GeneratedTasksResult(generated_count=len(tasks), tasks=tasks)


@router.get("/", response_model=list[TaskRead])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    return service.list_tasks(db, current_user.organization_id)


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> TaskRead:
    task = service.create_task(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="task.created",
        resource_type="task",
        resource_id=task.id,
        summary=f"Aufgabe {task.title} angelegt",
        details={
            "status": task.status,
            "priority": task.priority,
            "property_id": task.property_id,
            "unit_id": task.unit_id,
            "vendor_id": task.vendor_id,
            "recurring_template_id": task.recurring_template_id,
        },
    )
    return task


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskRead:
    return service.get_task(db, current_user.organization_id, task_id)


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> TaskRead:
    task = service.update_task(db, current_user.organization_id, task_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="task.updated",
        resource_type="task",
        resource_id=task.id,
        summary=f"Aufgabe {task.title} aktualisiert",
        details={
            "status": task.status,
            "priority": task.priority,
            "property_id": task.property_id,
            "unit_id": task.unit_id,
            "vendor_id": task.vendor_id,
            "recurring_template_id": task.recurring_template_id,
        },
    )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    task = service.get_task(db, current_user.organization_id, task_id)
    service.delete_task(db, current_user.organization_id, task_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="task.deleted",
        resource_type="task",
        resource_id=task_id,
        summary=f"Aufgabe {task.title} gelöscht",
        details={
            "status": task.status,
            "priority": task.priority,
            "property_id": task.property_id,
            "unit_id": task.unit_id,
            "vendor_id": task.vendor_id,
        },
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{task_id}/comments", response_model=list[TaskCommentRead])
async def list_task_comments(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskCommentRead]:
    return service.list_comments(db, current_user.organization_id, task_id)


@router.post("/{task_id}/comments", response_model=TaskCommentRead, status_code=status.HTTP_201_CREATED)
async def create_task_comment(
    task_id: str,
    payload: TaskCommentCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> TaskCommentRead:
    return service.add_comment(db, current_user.organization_id, task_id, current_user, payload)


@router.get("/{task_id}/attachments", response_model=list[DocumentRead])
async def list_task_attachments(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return service.list_task_attachments(db, current_user.organization_id, task_id)


@router.get("/{task_id}/history", response_model=list[TaskHistoryEntry])
async def list_task_history(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskHistoryEntry]:
    return service.list_task_history(db, current_user.organization_id, task_id)
