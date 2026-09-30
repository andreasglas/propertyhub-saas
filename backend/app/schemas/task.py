from datetime import date

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


class TaskBase(BaseModel):
    property_id: str | None = None
    unit_id: str | None = None
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
    pass


class TaskUpdate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
