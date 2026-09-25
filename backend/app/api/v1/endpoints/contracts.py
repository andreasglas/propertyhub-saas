from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.contract import ContractCreate, ContractRead, ContractUpdate
from app.services.contract_service import ContractService

router = APIRouter()
service = ContractService()


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
    return service.create_contract(db, current_user.organization_id, payload)


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
    return service.update_contract(db, current_user.organization_id, contract_id, payload)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    service.delete_contract(db, current_user.organization_id, contract_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
