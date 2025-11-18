"""Authentication routes with role-aware JWT tokens."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User
from apps.core.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    """Token plus user info response."""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    roles: list[str]
    display_name: str | None = None


class LoginRequest(BaseModel):
    """Login payload placeholder."""

    email: EmailStr
    password: str


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    """Issue an access token after validating credentials against the DB."""

    user = session.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    roles = [role.name for role in user.roles]
    token = create_access_token(
        subject=user.email,
        roles=roles,
        user_id=user.id,
        expires_delta=timedelta(minutes=60),
    )
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        roles=roles,
        display_name=user.profile.display_name if user.profile else None,
    )


@router.get("/me", response_model=TokenResponse)
def read_me(user: User = Depends(get_current_user)) -> TokenResponse:
    """Return current user profile info and a refreshed token."""

    roles = [role.name for role in user.roles]
    token = create_access_token(user.email, roles=roles, user_id=user.id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        roles=roles,
        display_name=user.profile.display_name if user.profile else None,
    )
