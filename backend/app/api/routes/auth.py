"""
Authentication routes.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import LoginRequest, Token
from app.auth.security import create_access_token
from app.auth.service import authenticate_user
from app.config import get_settings
from app.storage.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


class TokenWithUser(Token):
    """Token response with user info."""

    username: str
    role: str


@router.post("/login", response_model=TokenWithUser)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenWithUser:
    """
    Authenticate user and return access token with user info.

    Default credentials:
    - username: wnkadmin
    - password: wnkadmin
    """
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Include role in token payload for frontend use
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return TokenWithUser(
        access_token=access_token,
        username=user.username,
        role=user.role,
    )
