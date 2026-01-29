# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Demo-mode middleware that prevents write operations for non-admin users."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Final, cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import Request
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.responses import Response


_SAFE_METHODS: Final[set[str]] = {"GET", "HEAD", "OPTIONS"}
_DENIED_SAFE_PATHS: Final[set[str]] = {
    # These endpoints are implemented as GET but still mutate server state.
    "/auth/oidc/callback",
    "/kobo/v1/library/sync",
}

# Write endpoints that are allowed for non-admin users in demo mode.
# The intent is to keep demo UX interactive while still preventing filesystem-
# touching operations (uploads, cover changes, conversions, etc.).
_ALLOWED_WRITE_EXACT: Final[dict[str, set[str]]] = {
    # Auth: allow users to obtain/revoke tokens
    "/auth/login": {"POST"},
    "/auth/logout": {"POST"},
    "/auth/oidc/callback": {"POST"},
    # Auth: allow "DB-only" preference/profile tweaks
    "/auth/settings": {"PUT"},  # allow changing settings
    # Reading: allow persisting reading state (DB-only)
    "/reading/progress": {"PUT"},
    "/reading/sessions": {"POST"},
}

_ALLOWED_WRITE_PREFIX: Final[dict[str, set[str]]] = {
    # Auth settings are stored per-key.
    "/auth/settings/": {"PUT"},
    # Reading endpoints with path params.
    "/reading/sessions/": {"PUT"},
    "/reading/status/": {"PUT"},
}


def _is_admin_from_claims(claims: object) -> bool:
    """Return True when decoded JWT claims indicate an admin user.

    Parameters
    ----------
    claims : object
        Decoded JWT claims object. Expected to be a mapping containing an
        ``is_admin`` boolean.

    Returns
    -------
    bool
        True if claims contain an admin marker, otherwise False.
    """
    if not isinstance(claims, Mapping):
        return False
    claims_map = cast("Mapping[str, object]", claims)
    value = claims_map.get("is_admin")
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


def _is_allowed_write_request(method: str, path: str) -> bool:
    """Return True when a write request is allowed for demo-mode non-admins.

    Parameters
    ----------
    method : str
        HTTP method (e.g., "POST", "PUT").
    path : str
        Request path (e.g., "/auth/settings/theme").

    Returns
    -------
    bool
        True if the request should be permitted in demo mode.
    """
    if method in _ALLOWED_WRITE_EXACT.get(path, set()):
        return True
    for prefix, methods in _ALLOWED_WRITE_PREFIX.items():
        if path.startswith(prefix) and method in methods:
            return True
    return False


class DemoModeWriteLockMiddleware(BaseHTTPMiddleware):
    """Block non-safe HTTP methods for non-admins when demo mode is enabled.

    This middleware is intended for demo deployments where the UI should be
    "read-only" for regular users. Admin users are exempt.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and enforce demo-mode write lock.

        Parameters
        ----------
        request : Request
            Incoming FastAPI request.
        call_next : RequestResponseEndpoint
            Next middleware in chain.

        Returns
        -------
        Response
            Response from downstream middleware/handler, or a 403 when blocked.
        """
        cfg = request.app.state.config
        if not getattr(cfg, "demo_mode", False):
            return await call_next(request)

        path = request.url.path

        # Block the few known stateful GET endpoints in demo mode.
        if request.method in _SAFE_METHODS and path in _DENIED_SAFE_PATHS:
            if _is_admin_from_claims(getattr(request.state, "user_claims", None)):
                return await call_next(request)
            return JSONResponse(
                status_code=403, content={"detail": "demo_mode_read_only"}
            )

        if request.method in _SAFE_METHODS:
            return await call_next(request)

        if _is_allowed_write_request(request.method, path):
            return await call_next(request)

        if _is_admin_from_claims(getattr(request.state, "user_claims", None)):
            return await call_next(request)

        return JSONResponse(
            status_code=403,
            content={"detail": "demo_mode_read_only"},
        )
