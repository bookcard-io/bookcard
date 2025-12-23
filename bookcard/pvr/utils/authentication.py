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

"""Authentication management utilities for PVR download clients.

This module provides reusable authentication management following DRY principles
by centralizing authentication logic used across multiple download clients.
"""

from collections.abc import Callable

from bookcard.pvr.exceptions import PVRProviderAuthenticationError


class AuthenticationManager:
    """Reusable authentication manager with caching.

    This class consolidates authentication logic following DRY principles,
    providing a consistent interface for authentication across download clients.

    Parameters
    ----------
    authenticator : Callable[[], str | dict[str, str]]
        Function that performs authentication and returns a token (str) or
        cookies (dict[str, str]). Should raise PVRProviderAuthenticationError
        on failure.

    Examples
    --------
    >>> def perform_auth():
    ...     # Perform authentication
    ...     return "session_token_123"
    >>> auth_manager = AuthenticationManager(
    ...     perform_auth
    ... )
    >>> token = auth_manager.get_token()
    >>> token
    'session_token_123'
    >>> # Subsequent calls use cached token
    >>> auth_manager.get_token()  # No authentication call
    'session_token_123'
    >>> # Force re-authentication
    >>> auth_manager.get_token(
    ...     force=True
    ... )  # Calls authenticator again
    'session_token_123'
    """

    def __init__(self, authenticator: Callable[[], str | dict[str, str]]) -> None:
        """Initialize authentication manager.

        Parameters
        ----------
        authenticator : Callable[[], str | dict[str, str]]
            Function that performs authentication.
        """
        self._authenticator = authenticator
        self._token: str | None = None
        self._cookies: dict[str, str] | None = None

    def get_token(self, force: bool = False) -> str:
        """Get authentication token.

        Parameters
        ----------
        force : bool
            Force re-authentication even if token is cached.

        Returns
        -------
        str
            Authentication token.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails or returns cookies instead of token.
        """
        if not force and self._token is not None:
            return self._token

        auth_result = self._authenticator()

        if isinstance(auth_result, dict):
            msg = "Authenticator returned cookies, but get_token() was called"
            raise PVRProviderAuthenticationError(msg)

        self._token = auth_result
        return self._token

    def get_cookies(self, force: bool = False) -> dict[str, str]:
        """Get authentication cookies.

        Parameters
        ----------
        force : bool
            Force re-authentication even if cookies are cached.

        Returns
        -------
        dict[str, str]
            Authentication cookies.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails or returns token instead of cookies.
        """
        if not force and self._cookies is not None:
            return self._cookies

        auth_result = self._authenticator()

        if isinstance(auth_result, str):
            msg = "Authenticator returned token, but get_cookies() was called"
            raise PVRProviderAuthenticationError(msg)

        self._cookies = auth_result
        return self._cookies

    def invalidate(self) -> None:
        """Invalidate cached authentication.

        Forces next authentication call to perform fresh authentication.
        """
        self._token = None
        self._cookies = None

    def is_authenticated(self) -> bool:
        """Check if authentication is cached.

        Returns
        -------
        bool
            True if authentication is cached, False otherwise.
        """
        return self._token is not None or self._cookies is not None
