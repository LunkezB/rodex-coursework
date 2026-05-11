import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")
BearerToken = Annotated[str, Depends(oauth2_scheme)]
DbSession = Annotated[Session, Depends(get_db)]


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(subject: str | uuid.UUID, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ACCESS_TOKEN_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ACCESS_TOKEN_ALGORITHM],
    )


def get_current_user(
    token: BearerToken,
    db: DbSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = uuid.UUID(subject)
    except (InvalidTokenError, ValueError):
        raise credentials_exception from None

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    return user
