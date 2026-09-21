from datetime import date

from pydantic import BaseModel


class ContractBase(BaseModel):
    unit_id: str
    tenant_id: str
    start_date: date
    end_date: date | None = None
    cold_rent: float
    service_charge_advance: float = 0


class ContractCreate(ContractBase):
    pass


class ContractRead(ContractBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
