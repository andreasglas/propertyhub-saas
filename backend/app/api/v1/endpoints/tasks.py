from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.audit_log_service import AuditLogService
from app.services.task_service import TaskService

router = APIRouter()
service = TaskService()
audit_service = AuditLogService()


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
        },
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
