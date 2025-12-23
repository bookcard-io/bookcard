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

"""Tests for authentication management utilities."""

from unittest.mock import MagicMock

import pytest

from bookcard.pvr.exceptions import PVRProviderAuthenticationError
from bookcard.pvr.utils.authentication import AuthenticationManager

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def token_authenticator() -> MagicMock:
    """Create a mock authenticator that returns a token."""
    return MagicMock(return_value="token123")


@pytest.fixture
def cookies_authenticator() -> MagicMock:
    """Create a mock authenticator that returns cookies."""
    return MagicMock(return_value={"session": "abc123", "csrf": "xyz789"})


@pytest.fixture
def failing_authenticator() -> MagicMock:
    """Create a mock authenticator that raises an error."""
    return MagicMock(side_effect=PVRProviderAuthenticationError("Auth failed"))


# ============================================================================
# AuthenticationManager Tests
# ============================================================================


class TestAuthenticationManagerInit:
    """Test AuthenticationManager initialization."""

    def test_init_with_token_authenticator(
        self, token_authenticator: MagicMock
    ) -> None:
        """Test initialization with token authenticator."""
        manager = AuthenticationManager(token_authenticator)
        assert manager._authenticator == token_authenticator
        assert manager._token is None
        assert manager._cookies is None

    def test_init_with_cookies_authenticator(
        self, cookies_authenticator: MagicMock
    ) -> None:
        """Test initialization with cookies authenticator."""
        manager = AuthenticationManager(cookies_authenticator)
        assert manager._authenticator == cookies_authenticator
        assert manager._token is None
        assert manager._cookies is None


class TestAuthenticationManagerGetToken:
    """Test AuthenticationManager.get_token method."""

    def test_get_token_first_call(self, token_authenticator: MagicMock) -> None:
        """Test get_token on first call (no cache)."""
        manager = AuthenticationManager(token_authenticator)
        result = manager.get_token()
        assert result == "token123"
        assert manager._token == "token123"
        token_authenticator.assert_called_once()

    def test_get_token_cached(self, token_authenticator: MagicMock) -> None:
        """Test get_token uses cached token."""
        manager = AuthenticationManager(token_authenticator)
        # First call
        result1 = manager.get_token()
        assert result1 == "token123"
        # Second call should use cache
        result2 = manager.get_token()
        assert result2 == "token123"
        # Authenticator should only be called once
        assert token_authenticator.call_count == 1

    def test_get_token_force_reauthentication(
        self, token_authenticator: MagicMock
    ) -> None:
        """Test get_token with force=True re-authenticates."""
        manager = AuthenticationManager(token_authenticator)
        # First call
        manager.get_token()
        # Force re-authentication
        token_authenticator.return_value = "new_token456"
        result = manager.get_token(force=True)
        assert result == "new_token456"
        assert manager._token == "new_token456"
        assert token_authenticator.call_count == 2

    def test_get_token_with_cookies_authenticator_raises(
        self, cookies_authenticator: MagicMock
    ) -> None:
        """Test get_token raises error when authenticator returns cookies."""
        manager = AuthenticationManager(cookies_authenticator)
        with pytest.raises(
            PVRProviderAuthenticationError,
            match="Authenticator returned cookies, but get_token\\(\\) was called",
        ):
            manager.get_token()

    def test_get_token_authenticator_fails(
        self, failing_authenticator: MagicMock
    ) -> None:
        """Test get_token when authenticator raises error."""
        manager = AuthenticationManager(failing_authenticator)
        with pytest.raises(PVRProviderAuthenticationError, match="Auth failed"):
            manager.get_token()


class TestAuthenticationManagerGetCookies:
    """Test AuthenticationManager.get_cookies method."""

    def test_get_cookies_first_call(self, cookies_authenticator: MagicMock) -> None:
        """Test get_cookies on first call (no cache)."""
        manager = AuthenticationManager(cookies_authenticator)
        result = manager.get_cookies()
        assert result == {"session": "abc123", "csrf": "xyz789"}
        assert manager._cookies == {"session": "abc123", "csrf": "xyz789"}
        cookies_authenticator.assert_called_once()

    def test_get_cookies_cached(self, cookies_authenticator: MagicMock) -> None:
        """Test get_cookies uses cached cookies."""
        manager = AuthenticationManager(cookies_authenticator)
        # First call
        result1 = manager.get_cookies()
        assert result1 == {"session": "abc123", "csrf": "xyz789"}
        # Second call should use cache
        result2 = manager.get_cookies()
        assert result2 == {"session": "abc123", "csrf": "xyz789"}
        # Authenticator should only be called once
        assert cookies_authenticator.call_count == 1

    def test_get_cookies_force_reauthentication(
        self, cookies_authenticator: MagicMock
    ) -> None:
        """Test get_cookies with force=True re-authenticates."""
        manager = AuthenticationManager(cookies_authenticator)
        # First call
        manager.get_cookies()
        # Force re-authentication
        cookies_authenticator.return_value = {
            "session": "new_session",
            "csrf": "new_csrf",
        }
        result = manager.get_cookies(force=True)
        assert result == {"session": "new_session", "csrf": "new_csrf"}
        assert manager._cookies == {"session": "new_session", "csrf": "new_csrf"}
        assert cookies_authenticator.call_count == 2

    def test_get_cookies_with_token_authenticator_raises(
        self, token_authenticator: MagicMock
    ) -> None:
        """Test get_cookies raises error when authenticator returns token."""
        manager = AuthenticationManager(token_authenticator)
        with pytest.raises(
            PVRProviderAuthenticationError,
            match="Authenticator returned token, but get_cookies\\(\\) was called",
        ):
            manager.get_cookies()

    def test_get_cookies_authenticator_fails(
        self, failing_authenticator: MagicMock
    ) -> None:
        """Test get_cookies when authenticator raises error."""
        manager = AuthenticationManager(failing_authenticator)
        with pytest.raises(PVRProviderAuthenticationError, match="Auth failed"):
            manager.get_cookies()


class TestAuthenticationManagerInvalidate:
    """Test AuthenticationManager.invalidate method."""

    def test_invalidate_clears_token(self, token_authenticator: MagicMock) -> None:
        """Test invalidate clears cached token."""
        manager = AuthenticationManager(token_authenticator)
        manager.get_token()
        assert manager._token == "token123"
        manager.invalidate()
        assert manager._token is None

    def test_invalidate_clears_cookies(self, cookies_authenticator: MagicMock) -> None:
        """Test invalidate clears cached cookies."""
        manager = AuthenticationManager(cookies_authenticator)
        manager.get_cookies()
        assert manager._cookies == {"session": "abc123", "csrf": "xyz789"}
        manager.invalidate()
        assert manager._cookies is None

    def test_invalidate_clears_both(self, token_authenticator: MagicMock) -> None:
        """Test invalidate clears both token and cookies."""
        manager = AuthenticationManager(token_authenticator)
        manager.get_token()
        manager._cookies = {"test": "cookie"}  # Manually set cookies
        manager.invalidate()
        assert manager._token is None
        assert manager._cookies is None

    def test_invalidate_requires_reauthentication(
        self, token_authenticator: MagicMock
    ) -> None:
        """Test that after invalidate, next call re-authenticates."""
        manager = AuthenticationManager(token_authenticator)
        manager.get_token()
        assert token_authenticator.call_count == 1
        manager.invalidate()
        manager.get_token()
        assert token_authenticator.call_count == 2


class TestAuthenticationManagerIsAuthenticated:
    """Test AuthenticationManager.is_authenticated method."""

    def test_is_authenticated_false_initially(
        self, token_authenticator: MagicMock
    ) -> None:
        """Test is_authenticated returns False initially."""
        manager = AuthenticationManager(token_authenticator)
        assert manager.is_authenticated() is False

    def test_is_authenticated_true_after_get_token(
        self, token_authenticator: MagicMock
    ) -> None:
        """Test is_authenticated returns True after get_token."""
        manager = AuthenticationManager(token_authenticator)
        manager.get_token()
        assert manager.is_authenticated() is True

    def test_is_authenticated_true_after_get_cookies(
        self, cookies_authenticator: MagicMock
    ) -> None:
        """Test is_authenticated returns True after get_cookies."""
        manager = AuthenticationManager(cookies_authenticator)
        manager.get_cookies()
        assert manager.is_authenticated() is True

    def test_is_authenticated_false_after_invalidate(
        self, token_authenticator: MagicMock
    ) -> None:
        """Test is_authenticated returns False after invalidate."""
        manager = AuthenticationManager(token_authenticator)
        manager.get_token()
        assert manager.is_authenticated() is True
        manager.invalidate()
        assert manager.is_authenticated() is False

    def test_is_authenticated_true_with_token_only(
        self, token_authenticator: MagicMock
    ) -> None:
        """Test is_authenticated returns True with only token."""
        manager = AuthenticationManager(token_authenticator)
        manager.get_token()
        manager._cookies = None  # Ensure cookies is None
        assert manager.is_authenticated() is True

    def test_is_authenticated_true_with_cookies_only(
        self, cookies_authenticator: MagicMock
    ) -> None:
        """Test is_authenticated returns True with only cookies."""
        manager = AuthenticationManager(cookies_authenticator)
        manager.get_cookies()
        manager._token = None  # Ensure token is None
        assert manager.is_authenticated() is True
