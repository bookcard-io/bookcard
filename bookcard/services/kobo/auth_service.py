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

"""Kobo authentication service.

Handles generation, validation, and management of Kobo authentication tokens.
Follows SRP by focusing solely on Kobo authentication concerns.
"""

from __future__ import annotations

from binascii import hexlify
from os import urandom
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.auth import User
    from bookcard.repositories.kobo_repository import KoboAuthTokenRepository
    from bookcard.repositories.user_repository import UserRepository


class KoboAuthService:
    """Service for managing Kobo authentication tokens.

    Handles token generation, validation, and revocation for Kobo device
    authentication. Tokens are unique per user and used to authenticate
    requests from Kobo devices.

    Parameters
    ----------
    session : Session
        Database session.
    auth_token_repo : KoboAuthTokenRepository
        Repository for Kobo auth tokens.
    user_repo : UserRepository
        Repository for users.
    """

    def __init__(
        self,
        session: Session,
        auth_token_repo: KoboAuthTokenRepository,
        user_repo: UserRepository,
    ) -> None:
        self._session = session
        self._auth_token_repo = auth_token_repo
        self._user_repo = user_repo

    def generate_auth_token(self, user_id: int) -> str:
        """Generate or retrieve existing authentication token for a user.

        If a token already exists for the user, it is returned.
        Otherwise, a new token is generated and stored.

        Parameters
        ----------
        user_id : int
            User ID to generate token for.

        Returns
        -------
        str
            Authentication token (hex-encoded random bytes).

        Raises
        ------
        ValueError
            If user does not exist.
        """
        user = self._user_repo.get(user_id)
        if user is None:
            msg = f"User {user_id} not found"
            raise ValueError(msg)

        existing_token = self._auth_token_repo.find_by_user_id(user_id)
        if existing_token:
            return existing_token.auth_token

        # Generate new token (32 bytes = 64 hex characters)
        token_bytes = urandom(32)
        token = hexlify(token_bytes).decode("utf-8")

        from bookcard.models.kobo import KoboAuthToken

        auth_token = KoboAuthToken(
            user_id=user_id,
            auth_token=token,
        )
        self._auth_token_repo.add(auth_token)
        self._session.flush()

        return token

    def validate_auth_token(self, token: str) -> User | None:
        """Validate an authentication token and return the associated user.

        Parameters
        ----------
        token : str
            Authentication token to validate.

        Returns
        -------
        User | None
            User associated with the token if valid, None otherwise.
        """
        auth_token = self._auth_token_repo.find_by_token(token)
        if auth_token is None:
            return None

        return self._user_repo.get(auth_token.user_id)

    def revoke_auth_token(self, user_id: int) -> None:
        """Revoke (delete) the authentication token for a user.

        Parameters
        ----------
        user_id : int
            User ID whose token should be revoked.
        """
        self._auth_token_repo.delete_by_user_id(user_id)
        self._session.flush()
