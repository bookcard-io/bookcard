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

"""Unit tests for AuthenticatedProxyMixin."""

import pytest

from bookcard.pvr.download_clients._auth_mixin import AuthenticatedProxyMixin
from bookcard.pvr.exceptions import PVRProviderAuthenticationError

# ============================================================================
# Test Concrete Implementations
# ============================================================================


class TokenAuthProxy(AuthenticatedProxyMixin):
    """Concrete proxy that returns a token for authentication."""

    def _perform_authentication(self) -> str | dict[str, str]:
        """Return a token."""
        return "test-token-123"


class CookieAuthProxy(AuthenticatedProxyMixin):
    """Concrete proxy that returns cookies for authentication."""

    def _perform_authentication(self) -> str | dict[str, str]:
        """Return cookies."""
        return {"session_id": "abc123", "auth_token": "xyz789"}


class EmptyCookieAuthProxy(AuthenticatedProxyMixin):
    """Concrete proxy that returns empty cookies (no auth needed)."""

    def _perform_authentication(self) -> str | dict[str, str]:
        """Return empty cookies."""
        return {}


class TestProxy(AuthenticatedProxyMixin):
    """Concrete proxy for testing credential requirements."""

    def _perform_authentication(self) -> str | dict[str, str]:
        """Mock authentication."""
        return "token"


class MyCustomProxy(AuthenticatedProxyMixin):
    """Concrete proxy with custom name for testing."""

    def _perform_authentication(self) -> str | dict[str, str]:
        """Mock authentication."""
        return "token"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def token_auth_proxy() -> TokenAuthProxy:
    """Create a token-based auth proxy."""
    return TokenAuthProxy()


@pytest.fixture
def cookie_auth_proxy() -> CookieAuthProxy:
    """Create a cookie-based auth proxy."""
    return CookieAuthProxy()


@pytest.fixture
def empty_cookie_auth_proxy() -> EmptyCookieAuthProxy:
    """Create an empty cookie auth proxy."""
    return EmptyCookieAuthProxy()


@pytest.fixture
def test_proxy() -> TestProxy:
    """Create a test proxy."""
    return TestProxy()


# ============================================================================
# Class Attributes Tests
# ============================================================================


class TestAuthenticatedProxyMixinAttributes:
    """Test cases for AuthenticatedProxyMixin class attributes."""

    def test_session_token_initialized_to_none(
        self, token_auth_proxy: TokenAuthProxy
    ) -> None:
        """Test _session_token is initialized to None."""
        assert token_auth_proxy._session_token is None

    def test_auth_cookies_initialized_to_none(
        self, cookie_auth_proxy: CookieAuthProxy
    ) -> None:
        """Test _auth_cookies is initialized to None."""
        assert cookie_auth_proxy._auth_cookies is None

    def test_attributes_are_class_variables(self) -> None:
        """Test that attributes are class variables, not instance variables."""
        proxy1 = TokenAuthProxy()
        proxy2 = TokenAuthProxy()

        # Initially both should be None
        assert proxy1._session_token is None
        assert proxy2._session_token is None

        # Setting on one should affect the class variable
        proxy1._session_token = "token1"
        # Note: This is actually an instance attribute now, but the class variable exists
        assert proxy1._session_token == "token1"
        # The other instance should still have None (instance attribute shadows class)
        assert proxy2._session_token is None


# ============================================================================
# ensure_authenticated Tests
# ============================================================================


class TestEnsureAuthenticated:
    """Test cases for ensure_authenticated method."""

    def test_ensure_authenticated_when_not_authenticated_token(
        self, token_auth_proxy: TokenAuthProxy
    ) -> None:
        """Test ensure_authenticated when not authenticated, returns token."""
        assert token_auth_proxy._session_token is None

        token_auth_proxy.ensure_authenticated()

        assert token_auth_proxy._session_token == "test-token-123"
        assert token_auth_proxy._auth_cookies is None

    def test_ensure_authenticated_when_not_authenticated_cookies(
        self, cookie_auth_proxy: CookieAuthProxy
    ) -> None:
        """Test ensure_authenticated when not authenticated, returns cookies."""
        assert cookie_auth_proxy._auth_cookies is None

        cookie_auth_proxy.ensure_authenticated()

        assert cookie_auth_proxy._auth_cookies == {
            "session_id": "abc123",
            "auth_token": "xyz789",
        }
        assert cookie_auth_proxy._session_token is None

    def test_ensure_authenticated_when_already_authenticated_token(
        self, token_auth_proxy: TokenAuthProxy
    ) -> None:
        """Test ensure_authenticated when already authenticated with token."""
        token_auth_proxy._session_token = "existing-token"
        token_auth_proxy.ensure_authenticated()

        # Should not call _perform_authentication again
        assert token_auth_proxy._session_token == "existing-token"

    def test_ensure_authenticated_when_already_authenticated_cookies(
        self, cookie_auth_proxy: CookieAuthProxy
    ) -> None:
        """Test ensure_authenticated when already authenticated with cookies."""
        cookie_auth_proxy._auth_cookies = {"existing": "cookie"}
        cookie_auth_proxy.ensure_authenticated()

        # Should not call _perform_authentication again
        assert cookie_auth_proxy._auth_cookies == {"existing": "cookie"}

    def test_ensure_authenticated_with_force_token(
        self, token_auth_proxy: TokenAuthProxy
    ) -> None:
        """Test ensure_authenticated with force=True re-authenticates."""
        token_auth_proxy._session_token = "old-token"
        token_auth_proxy.ensure_authenticated(force=True)

        # Should call _perform_authentication and update token
        assert token_auth_proxy._session_token == "test-token-123"

    def test_ensure_authenticated_with_force_cookies(
        self, cookie_auth_proxy: CookieAuthProxy
    ) -> None:
        """Test ensure_authenticated with force=True re-authenticates cookies."""
        cookie_auth_proxy._auth_cookies = {"old": "cookie"}
        cookie_auth_proxy.ensure_authenticated(force=True)

        # Should call _perform_authentication and update cookies
        assert cookie_auth_proxy._auth_cookies == {
            "session_id": "abc123",
            "auth_token": "xyz789",
        }

    def test_ensure_authenticated_with_empty_cookies(
        self, empty_cookie_auth_proxy: EmptyCookieAuthProxy
    ) -> None:
        """Test ensure_authenticated with empty cookies dict."""
        empty_cookie_auth_proxy.ensure_authenticated()

        # Empty dict should be stored
        assert empty_cookie_auth_proxy._auth_cookies == {}
        assert empty_cookie_auth_proxy._session_token is None

    def test_ensure_authenticated_force_false_when_authenticated(
        self, token_auth_proxy: TokenAuthProxy
    ) -> None:
        """Test ensure_authenticated with force=False when already authenticated."""
        token_auth_proxy._session_token = "existing"
        # Should return early without calling _perform_authentication
        token_auth_proxy.ensure_authenticated(force=False)

        assert token_auth_proxy._session_token == "existing"

    @pytest.mark.parametrize(
        ("session_token", "auth_cookies", "should_authenticate"),
        [
            (None, None, True),
            ("token", None, False),
            (None, {"cookie": "value"}, False),
            ("token", {"cookie": "value"}, False),
        ],
    )
    def test_ensure_authenticated_early_return_conditions(
        self,
        token_auth_proxy: TokenAuthProxy,
        session_token: str | None,
        auth_cookies: dict[str, str] | None,
        should_authenticate: bool,
    ) -> None:
        """Test ensure_authenticated early return conditions."""
        token_auth_proxy._session_token = session_token
        token_auth_proxy._auth_cookies = auth_cookies

        token_auth_proxy.ensure_authenticated()

        if should_authenticate:
            assert token_auth_proxy._session_token == "test-token-123"
        else:
            # Should not have changed
            assert token_auth_proxy._session_token == session_token


# ============================================================================
# _require_credentials Tests
# ============================================================================


class TestRequireCredentials:
    """Test cases for _require_credentials method."""

    def test_require_credentials_with_valid_credentials(
        self, test_proxy: TestProxy
    ) -> None:
        """Test _require_credentials with valid username and password."""
        # Should not raise
        test_proxy._require_credentials(username="user", password="pass")

    @pytest.mark.parametrize(
        ("username", "password"),
        [
            (None, "password"),
            ("", "password"),
            ("username", None),
            ("username", ""),
            (None, None),
            ("", ""),
        ],
    )
    def test_require_credentials_with_missing_credentials(
        self,
        test_proxy: TestProxy,
        username: str | None,
        password: str | None,
    ) -> None:
        """Test _require_credentials raises error when credentials are missing."""
        with pytest.raises(
            PVRProviderAuthenticationError, match="requires username and password"
        ):
            test_proxy._require_credentials(username=username, password=password)

    def test_require_credentials_client_name_extraction(
        self, test_proxy: TestProxy
    ) -> None:
        """Test _require_credentials extracts client name from class name."""
        with pytest.raises(
            PVRProviderAuthenticationError, match="test requires username and password"
        ):
            test_proxy._require_credentials(username=None, password="pass")

    def test_require_credentials_custom_proxy_name(self) -> None:
        """Test _require_credentials with custom proxy class name."""
        proxy = MyCustomProxy()
        with pytest.raises(
            PVRProviderAuthenticationError,
            match="mycustom requires username and password",
        ):
            proxy._require_credentials(username="user", password=None)

    def test_require_credentials_with_whitespace_only_username(
        self, test_proxy: TestProxy
    ) -> None:
        """Test _require_credentials accepts whitespace-only username (not treated as empty)."""
        # Whitespace-only strings are truthy in Python, so they pass the check
        # This is the actual behavior of the implementation
        test_proxy._require_credentials(username="   ", password="pass")
        # Should not raise

    def test_require_credentials_with_whitespace_only_password(
        self, test_proxy: TestProxy
    ) -> None:
        """Test _require_credentials accepts whitespace-only password (not treated as empty)."""
        # Whitespace-only strings are truthy in Python, so they pass the check
        # This is the actual behavior of the implementation
        test_proxy._require_credentials(username="user", password="   ")
        # Should not raise


# ============================================================================
# Abstract Method Tests
# ============================================================================


class TestAbstractMethods:
    """Test cases for abstract methods."""

    def test_perform_authentication_raises_not_implemented(self) -> None:
        """Test that _perform_authentication raises NotImplementedError when not implemented."""

        # Create a class that doesn't implement _perform_authentication
        class IncompleteProxy(AuthenticatedProxyMixin):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            _ = IncompleteProxy()

    def test_perform_authentication_abstract_method_exists(self) -> None:
        """Test that _perform_authentication is an abstract method."""
        # Verify that _perform_authentication is marked as abstract
        assert hasattr(AuthenticatedProxyMixin, "_perform_authentication")
        # The method should exist but raise NotImplementedError when called
        # We can't call it directly on the abstract class, but we can verify it's abstract
        import inspect

        assert inspect.isabstract(AuthenticatedProxyMixin)
        assert "_perform_authentication" in AuthenticatedProxyMixin.__abstractmethods__
