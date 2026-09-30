from pydantic import BaseModel


class VendorBase(BaseModel):
    name: str
    service_type: str = "maintenance"
    contact_email: str | None = None
    contact_phone: str | None = None
    notes: str | None = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(VendorBase):
    pass


class VendorRead(VendorBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
