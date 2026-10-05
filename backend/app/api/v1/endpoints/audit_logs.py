from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.audit_log import AuditLogRead
from app.services.audit_log_service import AuditLogService

router = APIRouter()
service = AuditLogService()


@router.get("/", response_model=list[AuditLogRead])
async def list_audit_logs(
    resource_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    return service.list_logs(
        db,
        current_user.organization_id,
        resource_type=resource_type,
        action=action,
        limit=limit,
    )
