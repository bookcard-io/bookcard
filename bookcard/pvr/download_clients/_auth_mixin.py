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

"""Authentication mixin for download client proxies.

This module provides a reusable authentication mixin following DRY principles
by centralizing common authentication patterns used across download clients.
"""

from abc import ABC, abstractmethod

from bookcard.pvr.exceptions import PVRProviderAuthenticationError


class AuthenticatedProxyMixin(ABC):
    """Mixin for proxy classes that require authentication.

    This mixin provides a common authentication pattern that can be reused
    across different download client proxies. Subclasses must implement
    `_perform_authentication()` to provide client-specific authentication logic.

    Attributes
    ----------
    _session_token : str | None
        Cached authentication token/session ID.
    _auth_cookies : dict[str, str] | None
        Cached authentication cookies.
    """

    _session_token: str | None = None
    _auth_cookies: dict[str, str] | None = None

    @abstractmethod
    def _perform_authentication(self) -> str | dict[str, str]:
        """Perform client-specific authentication.

        This method should be implemented by subclasses to provide
        client-specific authentication logic.

        Returns
        -------
        str | dict[str, str]
            Authentication token (str) or cookies (dict[str, str]).
            Return empty dict for cookies if no auth needed.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails.
        """
        raise NotImplementedError

    def ensure_authenticated(self, force: bool = False) -> None:
        """Ensure proxy is authenticated.

        This method checks if authentication is needed and performs it
        if necessary. It caches the authentication result to avoid
        repeated authentication calls.

        Parameters
        ----------
        force : bool
            Force re-authentication even if already authenticated.

        Raises
        ------
        PVRProviderAuthenticationError
            If authentication fails or credentials are missing.
        """
        if not force and (
            self._session_token is not None or self._auth_cookies is not None
        ):
            return

        auth_result = self._perform_authentication()

        if isinstance(auth_result, dict):
            self._auth_cookies = auth_result
        else:
            self._session_token = auth_result

    def _require_credentials(self, username: str | None, password: str | None) -> None:
        """Check that credentials are provided.

        Parameters
        ----------
        username : str | None
            Username.
        password : str | None
            Password.

        Raises
        ------
        PVRProviderAuthenticationError
            If credentials are missing.
        """
        if not username or not password:
            client_name = self.__class__.__name__.replace("Proxy", "").lower()
            msg = f"{client_name} requires username and password"
            raise PVRProviderAuthenticationError(msg)
