from pydantic import BaseModel


class UnitBase(BaseModel):
    property_id: str
    name: str
    unit_type: str = "apartment"
    status: str = "vacant"
    area_sqm: float | None = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(UnitBase):
    pass


class UnitRead(UnitBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
