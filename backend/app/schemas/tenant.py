from datetime import date

from pydantic import BaseModel, EmailStr


class TenantBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str | None = None
    move_in_date: date | None = None
    move_out_date: date | None = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(TenantBase):
    pass


class TenantRead(TenantBase):
    id: str
    organization_id: str

    model_config = {"from_attributes": True}
