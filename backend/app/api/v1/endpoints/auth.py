from fastapi import APIRouter

from app.core.security import create_access_token
from app.schemas.user import LoginRequest, Token

router = APIRouter()


@router.post("/token", response_model=Token)
async def issue_access_token(credentials: LoginRequest) -> Token:
    token = create_access_token(subject=credentials.email)
    return Token(access_token=token)
