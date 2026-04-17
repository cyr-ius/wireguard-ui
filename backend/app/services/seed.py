"""
Database seeding: creates default roles, admin user, and settings on first run.
"""

from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import hash_password
from ..config import CONFIG_FILE, app_settings
from ..database import AsyncSessionLocal
from ..models import GlobalSettings, Role, User


async def seed_initial_data() -> None:
    async with AsyncSessionLocal() as db:
        await _seed_roles(db)
        await _seed_admin(db)
        await _seed_settings(db)
        await db.commit()


async def _seed_roles(db: AsyncSession) -> None:
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
    exists = await db.exec(select(GlobalSettings))
    if not exists.one_or_none():
        db.add(
            GlobalSettings.model_validate(
                {
                    "dns_servers": ["1.1.1.1", "8.8.8.8"],
                    "config_file_path": CONFIG_FILE,
                    "maintenance_mode": False,
                    "oidc_enabled": False,
                    "oidc_only": False,
                    "oidc_response_type": "code",
                    "oidc_scope": "openid profile email",
                }
            )
        )
