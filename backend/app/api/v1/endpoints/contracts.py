from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.contract import ContractCreate, ContractRead, ContractUpdate
from app.services.audit_log_service import AuditLogService
from app.services.contract_service import ContractService

router = APIRouter()
service = ContractService()
audit_service = AuditLogService()


@router.get("/", response_model=list[ContractRead])
async def list_contracts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ContractRead]:
    return service.list_contracts(db, current_user.organization_id)


@router.post("/", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
async def create_contract(
    payload: ContractCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> ContractRead:
    contract = service.create_contract(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="contract.created",
        resource_type="contract",
        resource_id=contract.id,
        summary=f"Vertrag {contract.id} angelegt",
        details={"unit_id": contract.unit_id, "tenant_id": contract.tenant_id},
    )
    return contract


@router.get("/{contract_id}", response_model=ContractRead)
async def get_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContractRead:
    return service.get_contract(db, current_user.organization_id, contract_id)


@router.put("/{contract_id}", response_model=ContractRead)
async def update_contract(
    contract_id: str,
    payload: ContractUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> ContractRead:
    contract = service.update_contract(db, current_user.organization_id, contract_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="contract.updated",
        resource_type="contract",
        resource_id=contract.id,
        summary=f"Vertrag {contract.id} aktualisiert",
        details={"unit_id": contract.unit_id, "tenant_id": contract.tenant_id},
    )
    return contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    contract = service.get_contract(db, current_user.organization_id, contract_id)
    service.delete_contract(db, current_user.organization_id, contract_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="contract.deleted",
        resource_type="contract",
        resource_id=contract_id,
        summary=f"Vertrag {contract.id} gelöscht",
        details={"unit_id": contract.unit_id, "tenant_id": contract.tenant_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
