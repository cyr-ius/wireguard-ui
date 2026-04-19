"""
Database seeding: creates default roles, admin user, and settings on first run.
"""

from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import hash_password
from ..config import app_settings
from ..database import AsyncSessionLocal
from ..models import GlobalSettings, OidcSettings, Role, SmtpSettings, User


async def seed_initial_data() -> None:
    """Seed roles, admin user, and default settings on first run."""
    async with AsyncSessionLocal() as db:
        await _seed_roles(db)
        await _seed_admin(db)
        await _seed_settings(db)
        await _seed_oidc_settings(db)
        await _seed_smtp_settings(db)
        await db.commit()


async def _seed_roles(db: AsyncSession) -> None:
    """Create default admin and user roles if they do not already exist."""
    defaults = [
        {
            "name": "admin",
            "description": "Full administrative access",
            "permissions": "admin-read,admin-write,user-read,user-write",
        },
        {
            "name": "user",
            "description": "Standard user access",
            "permissions": "user-read,user-write",
        },
    ]
    for data in defaults:
        exists = await db.exec(select(Role).where(Role.name == data["name"]))
        if not exists.one_or_none():
            db.add(Role.model_validate(data))


async def _seed_admin(db: AsyncSession) -> None:
    """Create admin user only if no users exist yet."""
    any_user = await db.exec(select(User))
    if any_user.first():
        return

    admin_role = (await db.exec(select(Role).where(Role.name == "admin"))).one_or_none()

    user = User.model_validate(
        {
            "username": app_settings.admin_username,
            "email": app_settings.admin_email,
            "first_name": "Administrator",
            "hashed_password": hash_password(app_settings.admin_password),
            "active": True,
        }
    )
    user.roles = [admin_role] if admin_role else []
    db.add(user)


async def _seed_settings(db: AsyncSession) -> None:
    """Create default GlobalSettings row if none exists."""
    exists = await db.exec(select(GlobalSettings))
    if not exists.one_or_none():
        db.add(
            GlobalSettings.model_validate(
                {
                    "dns_servers": ["1.1.1.1", "8.8.8.8"],
                    "maintenance_mode": False,
                }
            )
        )


async def _seed_oidc_settings(db: AsyncSession) -> None:
    """Create default OidcSettings row if none exists."""
    if not (await db.exec(select(OidcSettings))).one_or_none():
        db.add(OidcSettings())


async def _seed_smtp_settings(db: AsyncSession) -> None:
    """Create default SmtpSettings row if none exists."""
    if not (await db.exec(select(SmtpSettings))).one_or_none():
        db.add(SmtpSettings())
