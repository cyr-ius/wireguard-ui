"""
WireGuard UI - FastAPI Backend
Copyright (C) 2021-2024  Cyr-ius (github.com/cyr-ius)
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import app_settings
from .database import engine
from .exceptions import http_exception_handler, validation_exception_handler
from .helpers import resolve_safe_path
from .routers import auth, clients, oidc, server, settings, smtp, status, users
from .security import CsrfMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from .services.seed import seed_initial_data
from .services.wireguard import WireGuardError, start_service, write_server_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=app_settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def auto_start_wireguard(retry: int = 0) -> None:
    """Autostart WireGuard if configured to do so and not already running."""
    try:
        await write_server_config()
        await start_service()
        logger.info("WireGuard autostart successful")
    except WireGuardError as e:
        logger.warning("WireGuard autostart failed: %s", e)
        retry += 1
        if retry < 3:
            await asyncio.sleep(5)  # Wait before retrying
            logger.info("Retrying WireGuard autostart (attempt %d)", retry)
            await auto_start_wireguard(retry)
        else:
            logger.error("WireGuard autostart failed after 3 attempts: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: seed initial data then optionally start WireGuard."""
    await seed_initial_data()
    if app_settings.wg_autostart:
        await auto_start_wireguard()

    yield
    await engine.dispose()


app = FastAPI(
    title="WireGuard UI",
    description="API for WireGuard management",
    version=app_settings.app_version,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if app_settings.swagger_enabled else None,
)

# ── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CsrfMiddleware)
app.add_middleware(RateLimitMiddleware)

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

# ── Self-hosted static assets (Swagger UI, no Internet dependency) ─────────────
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/api/static", StaticFiles(directory=static_dir), name="static")


# ── Self-hosted Swagger UI ────────────────────────────────────────────────────
@app.get("/api/docs", include_in_schema=False)
async def swagger_ui() -> HTMLResponse:
    if not app_settings.swagger_enabled:
        raise HTTPException(status_code=404, detail="Not Found")
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - Swagger UI",
        swagger_js_url="/api/static/swagger/swagger-ui-bundle.js",
        swagger_css_url="/api/static/swagger/swagger-ui.css",
        swagger_favicon_url="/api/static/favicon.ico",
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": app.title, "version": app.version}


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
