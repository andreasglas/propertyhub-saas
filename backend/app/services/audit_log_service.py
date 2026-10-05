from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.user import User


class AuditLogService:
    def list_logs(
        self,
        db: Session,
        organization_id: str,
        *,
        resource_type: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .limit(max(1, min(limit, 500)))
        )
        if resource_type:
            statement = statement.where(AuditLog.resource_type == resource_type)
        if action:
            statement = statement.where(AuditLog.action == action)
        return list(db.scalars(statement))

    def record(
        self,
        db: Session,
        *,
        organization_id: str,
        actor: User | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        summary: str,
        details: dict | None = None,
    ) -> AuditLog:
        log_entry = AuditLog(
            organization_id=organization_id,
            actor_user_id=actor.id if actor is not None else None,
            actor_email=actor.email if actor is not None else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            summary=summary,
            details=self._normalize_details(details),
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    def _normalize_details(self, value):
        if value is None:
            return None
        if isinstance(value, dict):
            return {str(key): self._normalize_details(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._normalize_details(item) for item in value]
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value
