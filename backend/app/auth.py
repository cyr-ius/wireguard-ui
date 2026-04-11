"""
JWT authentication helpers and FastAPI dependency functions.
"""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .config import app_settings
from .database import get_db
from .models import User

SECRET_KEY = app_settings.secret_key
ALGORITHM = app_settings.jwt_algorithm
EXPIRE_MIN = app_settings.access_token_expire_minutes
PASSWORD_HASH_ROUNDS = app_settings.bcrypt_rounds

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def _bcrypt_input(password: str) -> bytes:
    """
    Normalize passwords to a fixed-size bcrypt input.
    This avoids bcrypt's 72-byte truncation edge case.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    """Return bcrypt hash of plain password."""
    return bcrypt.hashpw(
        _bcrypt_input(password),
        bcrypt.gensalt(rounds=PASSWORD_HASH_ROUNDS),
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Return True if plain matches the stored hash.
    Supports legacy raw-bcrypt verification for older hashes.
    """
    encoded_hash = hashed.encode("utf-8")
    try:
        if bcrypt.checkpw(_bcrypt_input(plain), encoded_hash):
            return True
        return bcrypt.checkpw(plain.encode("utf-8"), encoded_hash)
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create and return a signed JWT."""
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=EXPIRE_MIN)
    )
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT Bearer token and return the authenticated User.
    Raises HTTP 401 when the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.exec(
        select(User).where(User.username == username).options(selectinload(User.roles))  # type: ignore
    )
    user = result.one_or_none()
    if user is None or user.active is False:
        raise credentials_exception
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Raises HTTP 403 unless the authenticated user has the 'admin' role.
    Use as a FastAPI dependency on any admin-only endpoint.
    """
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
