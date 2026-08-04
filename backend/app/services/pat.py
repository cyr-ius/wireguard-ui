"""Personal Access Token generation, hashing and validation."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import PersonalAccessToken, User, utc_now

TOKEN_PREFIX = "wgui_pat_"

_DURATION_TO_DELTA: dict[str, timedelta | None] = {
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "1y": timedelta(days=365),
    "unlimited": None,
}


def hash_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of a raw PAT (tokens are high-entropy, no salt needed)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def expires_at_for(duration: str) -> datetime | None:
    """Return the expiry datetime for a duration code, or None for 'unlimited'."""
    delta = _DURATION_TO_DELTA.get(duration)
    return utc_now() + delta if delta is not None else None


def generate_raw_token() -> tuple[str, str]:
    """Return a (raw_token, token_prefix) pair. The raw token is shown once, never stored."""
    secret = secrets.token_urlsafe(32)
    raw_token = f"{TOKEN_PREFIX}{secret}"
    return raw_token, raw_token[: len(TOKEN_PREFIX) + 8]


async def resolve_user_from_pat(db: AsyncSession, raw_token: str) -> User | None:
    """Return the active User owning a valid, non-expired, non-revoked PAT."""
    if not raw_token.startswith(TOKEN_PREFIX):
        return None

    token_hash = hash_token(raw_token)
    pat = (
        await db.exec(
            select(PersonalAccessToken).where(
                PersonalAccessToken.token_hash == token_hash
            )
        )
    ).one_or_none()
    if pat is None or pat.revoked:
        return None
    if pat.expires_at is not None:
        # SQLite round-trips datetimes as naive; assume UTC (as stored) before comparing.
        expires_at = (
            pat.expires_at.replace(tzinfo=UTC)
            if pat.expires_at.tzinfo is None
            else pat.expires_at
        )
        if expires_at < utc_now():
            return None

    user = (
        await db.exec(
            select(User).where(User.id == pat.user_id).options(selectinload(User.roles))  # type: ignore[arg-type]
        )
    ).one_or_none()
    if user is None or not user.active:
        return None

    pat.last_used_at = utc_now()
    db.add(pat)
    await db.commit()

    return user
