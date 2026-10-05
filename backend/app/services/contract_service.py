from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.contract import Contract
from app.db.models.tenant import Tenant
from app.db.models.unit import Unit
from app.schemas.contract import ContractCreate, ContractUpdate


class ContractService:
    def list_contracts(self, db: Session, organization_id: str) -> list[Contract]:
        statement = (
            select(Contract)
            .where(Contract.organization_id == organization_id)
            .order_by(Contract.created_at.desc())
        )
        return list(db.scalars(statement))

    def _ensure_unit(self, db: Session, organization_id: str, unit_id: str) -> Unit:
        unit = db.scalar(
            select(Unit).where(Unit.id == unit_id, Unit.organization_id == organization_id)
        )
        if unit is None:
            raise PropertyHubError("Unit not found", status_code=404)
        return unit

    def _ensure_tenant(self, db: Session, organization_id: str, tenant_id: str) -> Tenant:
        tenant = db.scalar(
            select(Tenant).where(
                Tenant.id == tenant_id, Tenant.organization_id == organization_id
            )
        )
        if tenant is None:
            raise PropertyHubError("Tenant not found", status_code=404)
        return tenant

    def get_contract(self, db: Session, organization_id: str, contract_id: str) -> Contract:
        contract = db.scalar(
            select(Contract).where(
                Contract.id == contract_id,
                Contract.organization_id == organization_id,
            )
        )
        if contract is None:
            raise PropertyHubError("Contract not found", status_code=404)
        return contract

    def create_contract(
        self, db: Session, organization_id: str, payload: ContractCreate
    ) -> Contract:
        self._ensure_unit(db, organization_id, payload.unit_id)
        self._ensure_tenant(db, organization_id, payload.tenant_id)
        contract = Contract(organization_id=organization_id, **payload.model_dump())
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract

    def update_contract(
        self,
        db: Session,
        organization_id: str,
        contract_id: str,
        payload: ContractUpdate,
    ) -> Contract:
        self._ensure_unit(db, organization_id, payload.unit_id)
        self._ensure_tenant(db, organization_id, payload.tenant_id)
        contract = self.get_contract(db, organization_id, contract_id)
        for field, value in payload.model_dump().items():
            setattr(contract, field, value)
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract

    def delete_contract(self, db: Session, organization_id: str, contract_id: str) -> None:
        contract = self.get_contract(db, organization_id, contract_id)
        db.delete(contract)
        db.commit()
