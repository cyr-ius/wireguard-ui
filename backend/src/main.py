"""
WireGuard UI - FastAPI Backend
Entry point: run with `uvicorn main:app --reload` from the backend/ directory.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlmodel import SQLModel

from .config import app_settings
from .database import engine
from .routers import auth, clients, oidc, server, settings, status, users
from .services.seed import seed_initial_data

logger = logging.getLogger(__name__)


def _ensure_global_settings_oidc_columns(sync_conn) -> None:
    """Best-effort schema patch for existing databases without migrations."""
    inspector = inspect(sync_conn)
    if not inspector.has_table("global_settings"):
        return

    existing = {col["name"] for col in inspector.get_columns("global_settings")}
    column_sql: dict[str, str] = {
        "oidc_enabled": "BOOLEAN NOT NULL DEFAULT 0",
        "oidc_issuer": "VARCHAR(512) DEFAULT ''",
        "oidc_client_id": "VARCHAR(255) DEFAULT ''",
        "oidc_client_secret": "VARCHAR(512) DEFAULT ''",
        "oidc_redirect_uri": "VARCHAR(512) DEFAULT ''",
        "oidc_post_logout_redirect_uri": "VARCHAR(512) DEFAULT ''",
        "oidc_response_type": "VARCHAR(50) DEFAULT 'code'",
        "oidc_scope": "VARCHAR(255) DEFAULT 'openid profile email'",
    }

    for column, definition in column_sql.items():
        if column in existing:
            continue
        sync_conn.execute(
            text(f"ALTER TABLE global_settings ADD COLUMN {column} {definition}")
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create all tables and seed initial data, then yield."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.run_sync(_ensure_global_settings_oidc_columns)
    await seed_initial_data()
    yield
    await engine.dispose()


app = FastAPI(
    title="WireGuard UI API",
    description="REST API for WireGuard management",
    version=app_settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(server.router, prefix="/api/server", tags=["Server"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(oidc.router, prefix="/api/oidc", tags=["OIDC"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": "WireGuardUI"}


# ── Serve Angular SPA (must be last) ─────────────────────────────────────────
frontend_dist = Path(__file__).resolve().parent.parent / "frontend"

if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
