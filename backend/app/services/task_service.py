from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.audit_log import AuditLog
from app.db.models.document import Document
from app.db.models.property import Property
from app.db.models.task import Task
from app.db.models.task_comment import TaskComment
from app.db.models.task_template import TaskTemplate
from app.db.models.unit import Unit
from app.db.models.user import User
from app.db.models.vendor import Vendor
from app.schemas.task import (
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskHistoryEntry,
    TaskTemplateCreate,
    TaskTemplateRead,
    TaskTemplateUpdate,
    TaskUpdate,
)


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
        normalized_payload = self._apply_completion_state(normalized_payload)
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
        normalized_payload = self._apply_completion_state(normalized_payload, existing_task=task)
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

    def list_comments(
        self, db: Session, organization_id: str, task_id: str
    ) -> list[TaskComment]:
        self.get_task(db, organization_id, task_id)
        return list(
            db.scalars(
                select(TaskComment)
                .where(
                    TaskComment.organization_id == organization_id,
                    TaskComment.task_id == task_id,
                )
                .order_by(TaskComment.created_at.desc())
            )
        )

    def add_comment(
        self,
        db: Session,
        organization_id: str,
        task_id: str,
        actor: User,
        payload: TaskCommentCreate,
    ) -> TaskComment:
        self.get_task(db, organization_id, task_id)
        comment = TaskComment(
            organization_id=organization_id,
            task_id=task_id,
            author_user_id=actor.id,
            author_email=actor.email,
            message=payload.message.strip(),
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    def list_task_attachments(
        self, db: Session, organization_id: str, task_id: str
    ) -> list[Document]:
        self.get_task(db, organization_id, task_id)
        return list(
            db.scalars(
                select(Document)
                .where(
                    Document.organization_id == organization_id,
                    Document.related_model == "task",
                    Document.related_id == task_id,
                )
                .order_by(Document.created_at.desc())
            )
        )

    def list_task_history(
        self, db: Session, organization_id: str, task_id: str
    ) -> list[TaskHistoryEntry]:
        task = self.get_task(db, organization_id, task_id)
        audit_logs = list(
            db.scalars(
                select(AuditLog)
                .where(
                    AuditLog.organization_id == organization_id,
                    AuditLog.resource_type == "task",
                    AuditLog.resource_id == task_id,
                )
                .order_by(AuditLog.created_at.desc())
            )
        )
        comments = self.list_comments(db, organization_id, task_id)
        attachments = self.list_task_attachments(db, organization_id, task_id)

        history_entries: list[TaskHistoryEntry] = []
        history_entries.extend(
            TaskHistoryEntry(
                entry_type="audit",
                entry_id=entry.id,
                created_at=entry.created_at,
                actor_email=entry.actor_email,
                title=entry.action,
                message=entry.summary,
                metadata=entry.details,
            )
            for entry in audit_logs
        )
        history_entries.extend(
            TaskHistoryEntry(
                entry_type="comment",
                entry_id=comment.id,
                created_at=comment.created_at,
                actor_email=comment.author_email,
                title="Kommentar",
                message=comment.message,
                metadata={"task_id": comment.task_id},
            )
            for comment in comments
        )
        history_entries.extend(
            TaskHistoryEntry(
                entry_type="attachment",
                entry_id=document.id,
                created_at=document.created_at,
                actor_email=None,
                title="Anhang",
                message=f"Anhang {document.file_name} hochgeladen",
                metadata={"document_type": document.document_type, "document_id": document.id},
            )
            for document in attachments
        )
        history_entries.sort(key=lambda entry: entry.created_at, reverse=True)
        return history_entries

    def list_templates(self, db: Session, organization_id: str) -> list[TaskTemplate]:
        return list(
            db.scalars(
                select(TaskTemplate)
                .where(TaskTemplate.organization_id == organization_id)
                .order_by(TaskTemplate.created_at.desc())
            )
        )

    def get_template(
        self, db: Session, organization_id: str, template_id: str
    ) -> TaskTemplate:
        template = db.scalar(
            select(TaskTemplate).where(
                TaskTemplate.id == template_id,
                TaskTemplate.organization_id == organization_id,
            )
        )
        if template is None:
            raise PropertyHubError("Task template not found", status_code=404)
        return template

    def create_template(
        self, db: Session, organization_id: str, payload: TaskTemplateCreate
    ) -> TaskTemplate:
        normalized_payload = self._validate_template_relations(
            db, organization_id, payload.model_dump()
        )
        template = TaskTemplate(organization_id=organization_id, **normalized_payload)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def update_template(
        self,
        db: Session,
        organization_id: str,
        template_id: str,
        payload: TaskTemplateUpdate,
    ) -> TaskTemplate:
        template = self.get_template(db, organization_id, template_id)
        normalized_payload = self._validate_template_relations(
            db, organization_id, payload.model_dump()
        )
        for field, value in normalized_payload.items():
            setattr(template, field, value)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def delete_template(self, db: Session, organization_id: str, template_id: str) -> None:
        template = self.get_template(db, organization_id, template_id)
        db.delete(template)
        db.commit()

    def generate_due_tasks(
        self, db: Session, organization_id: str, *, today: date | None = None
    ) -> list[Task]:
        reference_date = today or date.today()
        templates = list(
            db.scalars(
                select(TaskTemplate).where(
                    TaskTemplate.organization_id == organization_id,
                    TaskTemplate.active.is_(True),
                    TaskTemplate.next_due_date <= reference_date,
                )
            )
        )
        generated_tasks: list[Task] = []
        for template in templates:
            task = Task(
                organization_id=organization_id,
                property_id=template.property_id,
                unit_id=template.unit_id,
                vendor_id=template.vendor_id,
                recurring_template_id=template.id,
                title=template.title,
                description=template.description,
                category=template.category,
                priority=template.priority,
                status="open",
                due_date=template.next_due_date,
                estimated_cost=None,
                actual_cost=None,
                assignee_name=template.assignee_name,
                completion_notes=None,
                completed_at=None,
                source="recurring",
            )
            db.add(task)
            generated_tasks.append(task)
            template.next_due_date = self._increment_due_date(
                template.next_due_date, template.recurrence_frequency
            )
            db.add(template)
        db.commit()
        for task in generated_tasks:
            db.refresh(task)
        return generated_tasks

    def generate_due_tasks_for_all_organizations(
        self, db: Session, *, today: date | None = None
    ) -> dict[str, int]:
        reference_date = today or date.today()
        organization_ids = list(
            db.scalars(
                select(TaskTemplate.organization_id)
                .where(
                    TaskTemplate.active.is_(True),
                    TaskTemplate.next_due_date <= reference_date,
                )
                .distinct()
            )
        )
        generated_counts: dict[str, int] = {}
        for organization_id in organization_ids:
            generated_tasks = self.generate_due_tasks(db, organization_id, today=reference_date)
            if generated_tasks:
                generated_counts[organization_id] = len(generated_tasks)
        return generated_counts

    def _validate_relations(self, db: Session, organization_id: str, payload: dict) -> dict:
        payload = self._validate_template_relations(db, organization_id, payload)
        recurring_template_id = payload.get("recurring_template_id")
        if recurring_template_id:
            template = db.scalar(
                select(TaskTemplate).where(
                    TaskTemplate.id == recurring_template_id,
                    TaskTemplate.organization_id == organization_id,
                )
            )
            if template is None:
                raise PropertyHubError("Task template not found", status_code=404)
        return payload

    def _validate_template_relations(
        self, db: Session, organization_id: str, payload: dict
    ) -> dict:
        property_id = payload.get("property_id")
        unit_id = payload.get("unit_id")
        vendor_id = payload.get("vendor_id")

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

        if vendor_id:
            vendor = db.scalar(
                select(Vendor).where(
                    Vendor.id == vendor_id,
                    Vendor.organization_id == organization_id,
                )
            )
            if vendor is None:
                raise PropertyHubError("Vendor not found", status_code=404)
        return payload

    def _apply_completion_state(self, payload: dict, existing_task: Task | None = None) -> dict:
        status = payload.get("status")
        existing_completed_at = existing_task.completed_at if existing_task is not None else None
        if status == "done":
            payload["completed_at"] = existing_completed_at or datetime.now(timezone.utc)
        else:
            payload["completed_at"] = None
            payload["actual_cost"] = payload.get("actual_cost")
        return payload

    def _increment_due_date(self, due_date: date, frequency: str) -> date:
        if frequency == "weekly":
            return due_date + timedelta(days=7)
        if frequency == "quarterly":
            month = due_date.month + 3
            year = due_date.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = min(due_date.day, self._days_in_month(year, month))
            return date(year, month, day)
        if frequency == "yearly":
            year = due_date.year + 1
            day = min(due_date.day, self._days_in_month(year, due_date.month))
            return date(year, due_date.month, day)
        month = due_date.month + 1
        year = due_date.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day = min(due_date.day, self._days_in_month(year, month))
        return date(year, month, day)

    def _days_in_month(self, year: int, month: int) -> int:
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        return (next_month - timedelta(days=1)).day
