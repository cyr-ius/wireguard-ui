"""Local authentication service: user lookup and credential verification."""

from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import verify_password
from ..models import GlobalSettings, User


async def local_login_allowed(db: AsyncSession) -> bool:
    """Return True if local password login is not disabled by OIDC-only mode."""
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is None:
        return True
    return not (settings.oidc_enabled and settings.oidc_only)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    """Verify credentials and return the User, raising 401/403 on failure."""
    result = await db.exec(
        select(User).where(User.username == username).options(selectinload(User.roles))  # type: ignore[arg-type]
    )
    user = result.one_or_none()

    if not user or not verify_password(password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )
    return user
