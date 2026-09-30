from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: str
    organization_id: str
    email: EmailStr
    full_name: str | None = None
    role: str
    is_active: bool
    invitation_sent_at: datetime | None = None
    invitation_accepted_at: datetime | None = None
    invitation_delivery_status: str = "pending"
    invitation_delivery_error: str | None = None
    invitation_last_attempt_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str
    role: str = "viewer"
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    role: str
    is_active: bool


class UserInvitationCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: str = "viewer"


class UserInvitationResult(BaseModel):
    user: UserRead
    invitation_token: str
    setup_path: str
    setup_url: str


class InvitationInfo(BaseModel):
    email: EmailStr
    full_name: str | None = None
    organization_name: str
    role: str


class SetupPasswordRequest(BaseModel):
    token: str
    password: str
    full_name: str | None = None


class SetupPasswordResult(BaseModel):
    message: str = "Password set successfully"
