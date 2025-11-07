# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Optional middleware that attaches current user to request.state.

Routes should still use dependencies for enforcement; this is for convenience.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from fundamental.services.security import JWTManager, SecurityTokenError

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
