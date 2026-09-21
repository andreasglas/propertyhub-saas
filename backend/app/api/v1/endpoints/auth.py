from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import Token
from sqlalchemy import select

router = APIRouter()


@router.post("/token", response_model=Token)
async def issue_access_token(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = db.scalar(select(User).where(User.email == credentials.username))
    if (
        user is None
        or not user.hashed_password
        or not user.is_active
        or not verify_password(credentials.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=user.email)
    return Token(access_token=token)
