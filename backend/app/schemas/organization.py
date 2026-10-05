from pydantic import BaseModel, EmailStr


class OrganizationBase(BaseModel):
    name: str
    legal_name: str | None = None
    street: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str = "Deutschland"
    contact_email: EmailStr | None = None
    contact_phone: str | None = None


class OrganizationUpdate(OrganizationBase):
    pass


class OrganizationRead(OrganizationBase):
    id: str

    model_config = {"from_attributes": True}
