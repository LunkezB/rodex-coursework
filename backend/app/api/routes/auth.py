from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserRead

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _authenticate_user(email: str, password: str, db: Session) -> Token:
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: DbSession) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email уже зарегистрирован",
        )

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email уже зарегистрирован",
        ) from None

    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login_user(payload: UserLogin, db: DbSession) -> Token:
    return _authenticate_user(payload.email, payload.password, db)


@router.post("/token", response_model=Token)
def token_user(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> Token:
    return _authenticate_user(form.username, form.password, db)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> User:
    return current_user
