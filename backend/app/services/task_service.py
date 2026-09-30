from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.property import Property
from app.db.models.task import Task
from app.db.models.unit import Unit
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def list_tasks(self, db: Session, organization_id: str) -> list[Task]:
        statement = (
            select(Task)
            .where(Task.organization_id == organization_id)
            .order_by(Task.created_at.desc())
        )
        return list(db.scalars(statement))

    def get_task(self, db: Session, organization_id: str, task_id: str) -> Task:
        task = db.scalar(
            select(Task).where(Task.id == task_id, Task.organization_id == organization_id)
        )
        if task is None:
            raise PropertyHubError("Task not found", status_code=404)
        return task

    def create_task(self, db: Session, organization_id: str, payload: TaskCreate) -> Task:
        normalized_payload = self._validate_relations(db, organization_id, payload.model_dump())
        task = Task(organization_id=organization_id, **normalized_payload)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update_task(
        self, db: Session, organization_id: str, task_id: str, payload: TaskUpdate
    ) -> Task:
        task = self.get_task(db, organization_id, task_id)
        normalized_payload = self._validate_relations(db, organization_id, payload.model_dump())
        for field, value in normalized_payload.items():
            setattr(task, field, value)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def delete_task(self, db: Session, organization_id: str, task_id: str) -> None:
        task = self.get_task(db, organization_id, task_id)
        db.delete(task)
        db.commit()

    def _validate_relations(
        self, db: Session, organization_id: str, payload: dict
    ) -> dict:
        property_id = payload.get("property_id")
        unit_id = payload.get("unit_id")

        property_obj: Property | None = None
        if property_id:
            property_obj = db.scalar(
                select(Property).where(
                    Property.id == property_id,
                    Property.organization_id == organization_id,
                )
            )
            if property_obj is None:
                raise PropertyHubError("Property not found", status_code=404)

        if unit_id:
            unit_obj = db.scalar(
                select(Unit).where(Unit.id == unit_id, Unit.organization_id == organization_id)
            )
            if unit_obj is None:
                raise PropertyHubError("Unit not found", status_code=404)
            if property_obj is not None and unit_obj.property_id != property_obj.id:
                raise PropertyHubError(
                    "Unit does not belong to selected property", status_code=400
                )
            payload["property_id"] = unit_obj.property_id

        return payload
