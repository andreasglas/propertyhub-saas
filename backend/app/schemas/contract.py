from datetime import date

from pydantic import BaseModel, model_validator


class ContractBase(BaseModel):
    unit_id: str
    tenant_id: str
    start_date: date
    end_date: date | None = None
    cold_rent: float
    service_charge_advance: float = 0

    @model_validator(mode="after")
    def validate_dates(self) -> "ContractBase":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ContractCreate(ContractBase):
    pass


class ContractUpdate(ContractBase):
    pass


class ContractRead(ContractBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
