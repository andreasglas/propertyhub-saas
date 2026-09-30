from datetime import date

from pydantic import BaseModel, Field, model_validator

ALLOWED_OPERATING_COST_ALLOCATION_METHODS = {
    "area",
    "unit_count",
    "occupancy_days",
    "advance_share",
}


class OperatingCostPeriodBase(BaseModel):
    property_id: str
    name: str
    period_start: date
    period_end: date
    status: str = "draft"

    @model_validator(mode="after")
    def validate_dates(self) -> "OperatingCostPeriodBase":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class OperatingCostPeriodCreate(OperatingCostPeriodBase):
    pass


class OperatingCostPeriodUpdate(OperatingCostPeriodBase):
    pass


class OperatingCostPeriodRead(OperatingCostPeriodBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}


class OperatingCostItemBase(BaseModel):
    category: str
    description: str | None = None
    allocation_method: str = "area"
    amount: float = Field(gt=0)
    billable: bool = True

    @model_validator(mode="after")
    def validate_allocation_method(self) -> "OperatingCostItemBase":
        if self.allocation_method not in ALLOWED_OPERATING_COST_ALLOCATION_METHODS:
            raise ValueError(
                "allocation_method must be one of "
                + ", ".join(sorted(ALLOWED_OPERATING_COST_ALLOCATION_METHODS))
            )
        return self


class OperatingCostItemCreate(OperatingCostItemBase):
    pass


class OperatingCostItemUpdate(OperatingCostItemBase):
    pass


class OperatingCostItemRead(OperatingCostItemBase):
    id: str
    organization_id: str
    period_id: str

    model_config = {"from_attributes": True}


class OperatingCostSettlementLine(BaseModel):
    line_type: str
    contract_id: str | None = None
    tenant_id: str | None = None
    tenant_name: str | None = None
    unit_id: str
    unit_name: str
    allocation_factor: float
    occupied_days: int
    share_amount: float
    advance_paid_amount: float
    balance_amount: float


class OperatingCostSettlementPreview(BaseModel):
    period: OperatingCostPeriodRead
    items: list[OperatingCostItemRead]
    total_billable_amount: float
    total_advance_amount: float
    lines: list[OperatingCostSettlementLine]
