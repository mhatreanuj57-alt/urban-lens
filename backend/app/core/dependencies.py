"""Shared FastAPI dependencies — current user and role guards."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token", auto_error=True)

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/v1/auth/token", auto_error=False
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the bearer token."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error
    sub = payload.get("sub")
    if not sub:
        raise credentials_error
    try:
        user_id = UUID(sub)
    except ValueError:
        raise credentials_error
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_error
    return user


async def get_optional_user(
    token: str = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Resolve the user when a token is present; anonymous otherwise."""
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    try:
        user_id = UUID(sub)
    except ValueError:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def require_roles(*roles: str):
    """Dependency factory enforcing that the current user has one of `roles`."""

    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker


# Common guards
moderator_required = require_roles("moderator", "admin")
admin_required = require_roles("admin")
