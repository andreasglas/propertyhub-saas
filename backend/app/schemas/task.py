from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, model_validator

ALLOWED_TASK_PRIORITIES = {"low", "medium", "high", "urgent"}
ALLOWED_TASK_STATUSES = {"open", "in_progress", "blocked", "done", "cancelled"}
ALLOWED_TASK_CATEGORIES = {
    "maintenance",
    "inspection",
    "tenant_request",
    "accounting",
    "compliance",
    "other",
}
ALLOWED_TASK_RECURRENCE_FREQUENCIES = {"weekly", "monthly", "quarterly", "yearly"}


class TaskBase(BaseModel):
    property_id: str | None = None
    unit_id: str | None = None
    vendor_id: str | None = None
    title: str
    description: str | None = None
    category: str = "maintenance"
    priority: str = "medium"
    status: str = "open"
    due_date: date | None = None
    assignee_name: str | None = None
    source: str = "manual"

    @model_validator(mode="after")
    def validate_enums(self) -> "TaskBase":
        if self.priority not in ALLOWED_TASK_PRIORITIES:
            raise ValueError(
                "priority must be one of " + ", ".join(sorted(ALLOWED_TASK_PRIORITIES))
            )
        if self.status not in ALLOWED_TASK_STATUSES:
            raise ValueError(
                "status must be one of " + ", ".join(sorted(ALLOWED_TASK_STATUSES))
            )
        if self.category not in ALLOWED_TASK_CATEGORIES:
            raise ValueError(
                "category must be one of " + ", ".join(sorted(ALLOWED_TASK_CATEGORIES))
            )
        return self


class TaskCreate(TaskBase):
    recurring_template_id: str | None = None


class TaskUpdate(TaskBase):
    recurring_template_id: str | None = None


class TaskRead(TaskBase):
    id: str
    organization_id: str
    recurring_template_id: str | None = None

    model_config = {"from_attributes": True}


class TaskCommentCreate(BaseModel):
    message: str


class TaskCommentRead(BaseModel):
    id: str
    organization_id: str
    task_id: str
    author_user_id: str | None = None
    author_email: str | None = None
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskHistoryEntry(BaseModel):
    entry_type: str
    entry_id: str
    created_at: datetime
    actor_email: str | None = None
    title: str
    message: str
    metadata: dict[str, Any] | None = None


class TaskTemplateBase(BaseModel):
    property_id: str | None = None
    unit_id: str | None = None
    vendor_id: str | None = None
    title: str
    description: str | None = None
    category: str = "maintenance"
    priority: str = "medium"
    recurrence_frequency: str = "monthly"
    next_due_date: date
    assignee_name: str | None = None
    active: bool = True

    @model_validator(mode="after")
    def validate_template(self) -> "TaskTemplateBase":
        if self.priority not in ALLOWED_TASK_PRIORITIES:
            raise ValueError(
                "priority must be one of " + ", ".join(sorted(ALLOWED_TASK_PRIORITIES))
            )
        if self.category not in ALLOWED_TASK_CATEGORIES:
            raise ValueError(
                "category must be one of " + ", ".join(sorted(ALLOWED_TASK_CATEGORIES))
            )
        if self.recurrence_frequency not in ALLOWED_TASK_RECURRENCE_FREQUENCIES:
            raise ValueError(
                "recurrence_frequency must be one of "
                + ", ".join(sorted(ALLOWED_TASK_RECURRENCE_FREQUENCIES))
            )
        return self


class TaskTemplateCreate(TaskTemplateBase):
    pass


class TaskTemplateUpdate(TaskTemplateBase):
    pass


class TaskTemplateRead(TaskTemplateBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}


class GeneratedTasksResult(BaseModel):
    generated_count: int
    tasks: list[TaskRead]
