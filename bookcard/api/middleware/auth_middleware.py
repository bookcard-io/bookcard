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

"""Optional middleware that attaches current user to request.state.

Routes should still use dependencies for enforcement; this is for convenience.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from bookcard.services.security import JWTManager, SecurityTokenError

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp


class AuthMiddleware(BaseHTTPMiddleware):
    """Attach `request.state.user` when a valid Bearer token is present."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], ASGIApp]
    ) -> Response:
        """Process request and attach user claims if valid token present.

        Parameters
        ----------
        request : Request
            Incoming FastAPI request.
        call_next : Callable[[Request], ASGIApp]
            Next middleware in chain.

        Returns
        -------
        Response
            Response from next middleware or handler.
        """
        request.state.user = None
        request.state.user_claims = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            try:
                jwt_mgr = JWTManager(request.app.state.config)
                claims = jwt_mgr.decode_token(token)
                request.state.user_claims = claims
            except SecurityTokenError:
                # Best-effort: ignore errors; dependencies will enforce auth.
                return await call_next(request)
        return await call_next(request)
