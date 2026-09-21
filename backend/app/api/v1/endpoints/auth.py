from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.core.security import create_access_token
from app.schemas.user import LoginRequest, Token

router = APIRouter()
settings = get_settings()


@router.post("/token", response_model=Token)
async def issue_access_token(credentials: LoginRequest) -> Token:
    configured_password = settings.bootstrap_admin_password
    if not settings.bootstrap_admin_email or configured_password is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bootstrap admin credentials are not configured",
        )

    if (
        credentials.email != settings.bootstrap_admin_email
        or credentials.password != configured_password.get_secret_value()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=credentials.email)
    return Token(access_token=token)
