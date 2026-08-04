"""Personal Access Token management — each user manages their own tokens."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_user
from ..config import app_settings
from ..database import get_db
from ..models import PersonalAccessToken, User
from ..schemas import PatCreate, PatCreateResponse, PatResponse
from ..services.audit import log_event
from ..services.pat import expires_at_for, generate_raw_token, hash_token

router = APIRouter()


def _require_api_keys_enabled() -> None:
    if not app_settings.api_keys_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Personal Access Tokens are disabled on this instance.",
        )


@router.get("", response_model=list[PatResponse])
async def list_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's Personal Access Tokens (never the token value)."""
    _require_api_keys_enabled()
    result = await db.exec(
        select(PersonalAccessToken)
        .where(PersonalAccessToken.user_id == current_user.id)
        .order_by(PersonalAccessToken.created_at.desc())  # type: ignore[attr-defined]
    )
    return result.all()


@router.post("", response_model=PatCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    data: PatCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Issue a new Personal Access Token. The raw token is only ever returned here."""
    _require_api_keys_enabled()

    raw_token, prefix = generate_raw_token()
    pat = PersonalAccessToken(
        user_id=current_user.id,
        name=data.name,
        token_prefix=prefix,
        token_hash=hash_token(raw_token),
        expires_at=expires_at_for(data.duration),
    )
    db.add(pat)
    await db.commit()
    await db.refresh(pat)

    await log_event(
        db,
        "pat.created",
        actor=current_user,
        target=f"pat:{pat.name}",
        details=f"duration={data.duration}",
        request=request,
    )

    return PatCreateResponse(token=raw_token, pat=PatResponse.model_validate(pat))


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    token_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke (delete) one of the current user's Personal Access Tokens."""
    pat = (
        await db.exec(
            select(PersonalAccessToken).where(
                PersonalAccessToken.id == token_id,
                PersonalAccessToken.user_id == current_user.id,
            )
        )
    ).one_or_none()
    if not pat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Token not found")

    name = pat.name
    await db.delete(pat)
    await db.commit()

    await log_event(
        db, "pat.revoked", actor=current_user, target=f"pat:{name}", request=request
    )
