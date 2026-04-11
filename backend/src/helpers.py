"""Helper functions for the WireGuard UI backend."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def resolve_safe_path(full_path: str, frontend_dist: Path) -> Path | None:
    """
    Resolve a URL path to a filesystem path safely.

    Returns the resolved Path if it is a file strictly inside frontend_dist,
    or None if the path is unsafe, empty, or points outside the allowed root.

    This prevents path traversal attacks (e.g. '../../etc/passwd',
    '%2e%2e%2fetc', null-byte injection) by using Path.is_relative_to()
    which operates on the fully resolved absolute path.

    Args:
        full_path: Raw URL path segment from the request.

    Returns:
        Path | None: Safe resolved path, or None if rejected.
    """
    # Reject empty paths and dot-only segments immediately.
    stripped = full_path.strip()
    if not stripped or stripped in (".", ".."):
        return None

    # Resolve to absolute path — collapses all '..' and symlinks.
    candidate = (frontend_dist / stripped).resolve()

    # The candidate must be strictly inside frontend_dist (not equal to it).
    # is_relative_to() returns True even when candidate == frontend_dist,
    # so we add an explicit equality check to block directory root access.
    if candidate == frontend_dist:
        return None

    if not candidate.is_relative_to(frontend_dist):
        logger.warning(
            "Path traversal attempt blocked: raw=%r resolved=%s",
            full_path,
            candidate,
        )
        return None

    # Only serve regular files, never directories or special files.
    if not candidate.is_file():
        return None

    return candidate
