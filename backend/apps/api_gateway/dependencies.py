"""Shared FastAPI dependencies for the API gateway."""
from typing import Callable, Generator, Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.config import Settings, get_settings
from apps.core.database import db_manager
from apps.core.models import User
from apps.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db_session() -> Generator:
    """Yield a default MySQL session for dependency injection."""

    with db_manager.session_scope("mysql") as session:
        yield session


def get_current_settings() -> Settings:
    """Expose cached settings for injection."""

    return get_settings()


def get_current_token(token: str = Depends(oauth2_scheme)) -> str:
    """Return the current JWT token (placeholder validation)."""

    return token


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_db_session)
) -> User:
    """Resolve the current authenticated user from JWT."""

    try:
        payload = decode_access_token(token)
    except ValueError as exc:  # pragma: no cover - invalid token
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: str) -> Callable[[User], User]:
    """Generate a dependency that ensures the current user has at least one required role."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if not roles:
            return user
        user_roles = {role.name for role in user.roles}
        required: Iterable[str] = set(roles)
        if user_roles.intersection(required):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    return dependency
