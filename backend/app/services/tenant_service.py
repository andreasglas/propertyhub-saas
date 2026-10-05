from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate


class TenantService:
    def list_tenants(self, db: Session, organization_id: str) -> list[Tenant]:
        statement = (
            select(Tenant)
            .where(Tenant.organization_id == organization_id)
            .order_by(Tenant.created_at.desc())
        )
        return list(db.scalars(statement))

    def get_tenant(self, db: Session, organization_id: str, tenant_id: str) -> Tenant:
        tenant = db.scalar(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.organization_id == organization_id,
            )
        )
        if tenant is None:
            raise PropertyHubError("Tenant not found", status_code=404)
        return tenant

    def create_tenant(
        self, db: Session, organization_id: str, payload: TenantCreate
    ) -> Tenant:
        tenant = Tenant(organization_id=organization_id, **payload.model_dump())
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    def update_tenant(
        self, db: Session, organization_id: str, tenant_id: str, payload: TenantUpdate
    ) -> Tenant:
        tenant = self.get_tenant(db, organization_id, tenant_id)
        for field, value in payload.model_dump().items():
            setattr(tenant, field, value)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    def delete_tenant(self, db: Session, organization_id: str, tenant_id: str) -> None:
        tenant = self.get_tenant(db, organization_id, tenant_id)
        db.delete(tenant)
        db.commit()
