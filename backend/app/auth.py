"""
JWT authentication helpers and FastAPI dependency functions.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal

import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status
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

# Names of the cookies / header used for the browser session and CSRF protection.
ACCESS_COOKIE = "access_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"

# Cookie security is fixed, not configurable: "lax" blocks cross-site unsafe
# requests while keeping top-level navigation working, and the CSRF middleware
# covers the residual cases. "Secure" is derived from the (proxy-aware) scheme.
COOKIE_SAMESITE: Literal["lax"] = "lax"

# auto_error=False so the Bearer header stays optional: the browser SPA
# authenticates via the HttpOnly cookie, while API clients may still use Bearer.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def _cookie_secure(request: Request) -> bool:
    """Whether cookies should carry the Secure flag for this request.

    Derived from the request scheme, which uvicorn rewrites from the trusted
    proxy's ``X-Forwarded-Proto`` header, so TLS-terminating proxies are handled.
    """
    return request.url.scheme == "https"


def set_auth_cookies(response: Response, request: Request, token: str) -> None:
    """Set the HttpOnly session cookie and a JS-readable CSRF cookie."""
    secure = _cookie_secure(request)
    max_age = EXPIRE_MIN * 60
    response.set_cookie(
        ACCESS_COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        secrets.token_urlsafe(32),
        max_age=max_age,
        httponly=False,
        secure=secure,
        samesite=COOKIE_SAMESITE,
        path="/",
    )


def clear_auth_cookies(response: Response, request: Request) -> None:
    """Remove the session and CSRF cookies (used on logout)."""
    secure = _cookie_secure(request)
    response.delete_cookie(
        ACCESS_COOKIE, path="/", httponly=True, secure=secure, samesite=COOKIE_SAMESITE
    )
    response.delete_cookie(
        CSRF_COOKIE, path="/", httponly=False, secure=secure, samesite=COOKIE_SAMESITE
    )


def _bcrypt_input(password: str) -> bytes:
    """SHA-256 + base64 encode password to avoid bcrypt 72-byte truncation."""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    """Return bcrypt hash of plain password."""
    return bcrypt.hashpw(
        _bcrypt_input(password),
        bcrypt.gensalt(rounds=PASSWORD_HASH_ROUNDS),
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches hashed; supports legacy raw-bcrypt hashes."""
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


async def get_token(
    request: Request,
    bearer: str | None = Depends(oauth2_scheme),
) -> str:
    """Return the JWT from the session cookie, falling back to the Bearer header."""
    token = request.cookies.get(ACCESS_COOKIE) or bearer
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the JWT and return the authenticated User, raise 401 if invalid."""
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
    """Raise 403 unless the current user has the 'admin' role."""
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
