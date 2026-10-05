from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: str
    organization_id: str
    actor_user_id: str | None = None
    actor_email: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    summary: str
    details: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
