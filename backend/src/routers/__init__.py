"""Routers package exports for static analyzers and explicit imports."""

from . import auth, clients, oidc, server, settings, smtp, status, users

__all__ = ["auth", "clients", "oidc", "server", "settings", "status", "users", "smtp"]
