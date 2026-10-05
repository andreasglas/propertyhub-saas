from pydantic import BaseModel


class PropertyBase(BaseModel):
    name: str
    property_type: str = "residential"
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    purchase_price: float | None = None


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(PropertyBase):
    pass


class PropertyRead(PropertyBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
