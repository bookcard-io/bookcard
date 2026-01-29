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

"""Middleware configuration for the FastAPI application."""

from fastapi import FastAPI

from bookcard.api.middleware.auth_middleware import AuthMiddleware
from bookcard.api.middleware.demo_mode_middleware import DemoModeWriteLockMiddleware


def register_middleware(app: FastAPI) -> None:
    """Register middleware with the FastAPI application.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """
    # NOTE: Starlette runs middleware in reverse order of addition.
    # Auth must run first to populate `request.state.user_claims` for downstream checks.
    app.add_middleware(DemoModeWriteLockMiddleware)  # type: ignore[invalid-argument-type]
    # Middleware (best-effort attachment of user claims)
    app.add_middleware(AuthMiddleware)  # type: ignore[invalid-argument-type]
