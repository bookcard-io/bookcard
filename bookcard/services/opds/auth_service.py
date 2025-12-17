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

"""Authentication service for OPDS feeds.

Supports HTTP Basic Auth (for e-reader compatibility) and JWT Bearer tokens.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from bookcard.services.opds.interfaces import IOpdsAuthProvider
from bookcard.services.security import (
    JWTManager,
    PasswordHasher,
    SecurityTokenError,
)

if TYPE_CHECKING:
    from fastapi import Request
    from sqlmodel import Session

    from bookcard.models.auth import User
    from bookcard.repositories.user_repository import UserRepository


class OpdsAuthService(IOpdsAuthProvider):
    """Authentication service for OPDS feeds.

    Supports both HTTP Basic Auth (for e-reader apps) and JWT Bearer tokens.
    Follows SRP by focusing solely on authentication concerns.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        user_repo: UserRepository,  # type: ignore[type-arg]
        hasher: PasswordHasher,  # type: ignore[type-arg]
        jwt_manager: JWTManager,  # type: ignore[type-arg]
    ) -> None:
        """Initialize OPDS auth service.

        Parameters
        ----------
        session : Session
            Database session.
        user_repo : UserRepository
            User repository.
        hasher : PasswordHasher
            Password hasher for verifying credentials.
        jwt_manager : JWTManager
            JWT manager for verifying Bearer tokens.
        """
        self._session = session
        self._user_repo = user_repo
        self._hasher = hasher
        self._jwt_manager = jwt_manager

    def authenticate_request(self, request: Request) -> User | None:
        """Authenticate request via HTTP Basic Auth or JWT.

        Tries HTTP Basic Auth first (for e-reader compatibility), then falls
        back to JWT Bearer token (for web clients).

        Parameters
        ----------
        request : Request
            FastAPI request object.

        Returns
        -------
        User | None
            Authenticated user or None if authentication fails.
        """
        # Try HTTP Basic Auth first (for e-readers)
        user = self._authenticate_basic_auth(request)
        if user is not None:
            return user

        # Fall back to JWT Bearer token (for web clients)
        return self._authenticate_jwt(request)

    def _authenticate_basic_auth(self, request: Request) -> User | None:
        """Authenticate via HTTP Basic Auth.

        Parameters
        ----------
        request : Request
            FastAPI request object.

        Returns
        -------
        User | None
            Authenticated user or None if authentication fails.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return None

        try:
            # Decode Basic Auth credentials
            encoded = auth_header.removeprefix("Basic ").strip()
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return None

        # Find user by username or email
        user = self._user_repo.find_by_username(
            username
        ) or self._user_repo.find_by_email(username)
        if user is None:
            return None

        # Verify password
        if not self._hasher.verify(password, user.password_hash):
            return None

        return user

    def _authenticate_jwt(self, request: Request) -> User | None:
        """Authenticate via JWT Bearer token.

        Parameters
        ----------
        request : Request
            FastAPI request object.

        Returns
        -------
        User | None
            Authenticated user or None if authentication fails.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.removeprefix("Bearer ")

        try:
            # Get JWT manager from app state (requires config)
            if not hasattr(request.app.state, "config"):
                return None

            jwt_mgr = JWTManager(request.app.state.config)

            # Decode token (without blacklist check for OPDS - simpler)
            claims = jwt_mgr.decode_token(token)
            user_id = int(claims.get("sub", 0))

            if user_id == 0:
                return None

            return self._user_repo.get(user_id)
        except (SecurityTokenError, ValueError, KeyError):
            return None
