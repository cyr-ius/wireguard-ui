"""
WireGuard UI - FastAPI Backend
Copyright (C) 2021-2024  Cyr-ius (github.com/cyr-ius)
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from sqlmodel import SQLModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import app_settings
from .database import engine
from .exceptions import http_exception_handler, validation_exception_handler
from .helpers import (
    resolve_safe_path,
)
from .routers import auth, clients, oidc, server, settings, smtp, status, users
from .security import SecurityHeadersMiddleware
from .services.seed import seed_initial_data

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=app_settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create all tables and seed initial data, then yield."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await seed_initial_data()
    yield
    await engine.dispose()


app = FastAPI(
    title="WireGuard UI API",
    description="REST API for WireGuard management",
    version=app_settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

# ── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── Exception handlers ───────────────────────────────────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # pyright: ignore[reportArgumentType]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # pyright: ignore[reportArgumentType]

# ── API routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(server.router, prefix="/api/server", tags=["Server"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(oidc.router, prefix="/api/oidc", tags=["OIDC"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(smtp.router, prefix="/api/smtp", tags=["SMTP"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": "WireGuardUI"}


# ── Serve Angular SPA (must be last) ─────────────────────────────────────────
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str) -> FileResponse:
    """
    Serve Angular static files with path traversal protection.

    Requests for existing static assets (JS, CSS, images) are served directly.
    All other paths fall back to index.html to support client-side SPA routing.
    Unknown or unsafe paths also fall back to index.html rather than 404-ing,
    letting the Angular router handle the error page.
    """

    # Resolve once at module load — avoids repeated filesystem calls per request.
    project_root = Path(__file__).resolve().parents[2]
    frontend_dist = (project_root / "frontend").resolve()
    frontend_index = frontend_dist / "index.html"

    if not frontend_index.is_file():
        logger.error("SPA index.html not found at %s", frontend_index)
        raise HTTPException(status_code=503, detail="Frontend not available.")

    safe = resolve_safe_path(full_path, frontend_dist)
    if safe is not None:
        return FileResponse(safe)

    # SPA fallback: Angular router handles unknown client-side routes.
    return FileResponse(frontend_index)
