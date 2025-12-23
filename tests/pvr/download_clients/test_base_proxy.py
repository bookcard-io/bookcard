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

"""Unit tests for BaseClientProxy."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.base_proxy import BaseClientProxy

# ============================================================================
# Test Concrete Implementation
# ============================================================================


class ConcreteProxy(BaseClientProxy):
    """Concrete implementation of BaseClientProxy for testing."""

    def authenticate(self, force: bool = False) -> None:
        """Mock authenticate implementation."""

    def test_connection(self) -> bool:
        """Mock test_connection implementation."""
        return True


class ConcreteProxyNoSSL(ConcreteProxy):
    """Concrete proxy that disables SSL verification."""

    @property
    def _verify_ssl(self) -> bool:
        """Disable SSL verification."""
        return False


class ConcreteProxyNoRedirects(ConcreteProxy):
    """Concrete proxy that disables redirect following."""

    @property
    def _follow_redirects(self) -> bool:
        """Disable redirect following."""
        return False


class ConcreteProxyCustomBoth(ConcreteProxy):
    """Concrete proxy that customizes both SSL and redirects."""

    @property
    def _verify_ssl(self) -> bool:
        """Disable SSL verification."""
        return False

    @property
    def _follow_redirects(self) -> bool:
        """Disable redirect following."""
        return False


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def base_download_client_settings() -> DownloadClientSettings:
    """Create base download client settings."""
    return DownloadClientSettings(
        host="localhost",
        port=8080,
        username="testuser",
        password="testpass",
        use_ssl=False,
        timeout_seconds=30,
        category="test",
        download_path="/downloads",
    )


@pytest.fixture
def base_url() -> str:
    """Create base URL for testing."""
    return "http://localhost:8080/api"


@pytest.fixture
def concrete_proxy(
    base_download_client_settings: DownloadClientSettings, base_url: str
) -> ConcreteProxy:
    """Create a concrete proxy instance."""
    return ConcreteProxy(settings=base_download_client_settings, base_url=base_url)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestBaseClientProxyInit:
    """Test cases for BaseClientProxy initialization."""

    def test_init(
        self,
        base_download_client_settings: DownloadClientSettings,
        base_url: str,
    ) -> None:
        """Test BaseClientProxy initialization."""
        proxy = ConcreteProxy(settings=base_download_client_settings, base_url=base_url)

        assert proxy.settings is base_download_client_settings
        assert proxy.base_url == base_url

    @pytest.mark.parametrize(
        ("host", "port", "use_ssl", "expected_base"),
        [
            ("localhost", 8080, False, "http://localhost:8080/api"),
            ("192.168.1.1", 9090, True, "https://192.168.1.1:9090/api"),
            ("example.com", 443, True, "https://example.com:443/api"),
        ],
    )
    def test_init_with_various_settings(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        expected_base: str,
    ) -> None:
        """Test initialization with various settings."""
        settings = DownloadClientSettings(
            host=host,
            port=port,
            username="user",
            password="pass",
            use_ssl=use_ssl,
            timeout_seconds=30,
        )
        proxy = ConcreteProxy(settings=settings, base_url=expected_base)

        assert proxy.settings.host == host
        assert proxy.settings.port == port
        assert proxy.settings.use_ssl == use_ssl
        assert proxy.base_url == expected_base


# ============================================================================
# Property Tests
# ============================================================================


class TestBaseClientProxyProperties:
    """Test cases for BaseClientProxy properties."""

    def test_verify_ssl_default(self, concrete_proxy: ConcreteProxy) -> None:
        """Test _verify_ssl property returns True by default."""
        assert concrete_proxy._verify_ssl is True

    def test_follow_redirects_default(self, concrete_proxy: ConcreteProxy) -> None:
        """Test _follow_redirects property returns True by default."""
        assert concrete_proxy._follow_redirects is True

    def test_verify_ssl_custom(
        self,
        base_download_client_settings: DownloadClientSettings,
        base_url: str,
    ) -> None:
        """Test _verify_ssl property can be overridden."""
        proxy = ConcreteProxyNoSSL(
            settings=base_download_client_settings, base_url=base_url
        )
        assert proxy._verify_ssl is False

    def test_follow_redirects_custom(
        self,
        base_download_client_settings: DownloadClientSettings,
        base_url: str,
    ) -> None:
        """Test _follow_redirects property can be overridden."""
        proxy = ConcreteProxyNoRedirects(
            settings=base_download_client_settings, base_url=base_url
        )
        assert proxy._follow_redirects is False

    def test_both_properties_custom(
        self,
        base_download_client_settings: DownloadClientSettings,
        base_url: str,
    ) -> None:
        """Test both properties can be overridden together."""
        proxy = ConcreteProxyCustomBoth(
            settings=base_download_client_settings, base_url=base_url
        )
        assert proxy._verify_ssl is False
        assert proxy._follow_redirects is False


# ============================================================================
# _get_client Tests
# ============================================================================


class TestBaseClientProxyGetClient:
    """Test cases for BaseClientProxy._get_client method."""

    @patch("bookcard.pvr.download_clients.base_proxy.create_httpx_client")
    def test_get_client_default(
        self,
        mock_create_client: MagicMock,
        concrete_proxy: ConcreteProxy,
    ) -> None:
        """Test _get_client with default SSL and redirect settings."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_create_client.return_value = mock_client

        result = concrete_proxy._get_client()

        assert result is mock_client
        mock_create_client.assert_called_once_with(
            timeout=30,
            verify=True,
            follow_redirects=True,
        )

    @patch("bookcard.pvr.download_clients.base_proxy.create_httpx_client")
    @pytest.mark.parametrize(
        ("timeout", "verify", "follow_redirects"),
        [
            (10, True, True),
            (60, False, True),
            (30, True, False),
            (45, False, False),
        ],
    )
    def test_get_client_with_custom_properties(
        self,
        mock_create_client: MagicMock,
        base_download_client_settings: DownloadClientSettings,
        base_url: str,
        timeout: int,
        verify: bool,
        follow_redirects: bool,
    ) -> None:
        """Test _get_client with custom property overrides."""
        base_download_client_settings.timeout_seconds = timeout

        if not verify and not follow_redirects:
            proxy = ConcreteProxyCustomBoth(
                settings=base_download_client_settings, base_url=base_url
            )
        elif not verify:
            proxy = ConcreteProxyNoSSL(
                settings=base_download_client_settings, base_url=base_url
            )
        elif not follow_redirects:
            proxy = ConcreteProxyNoRedirects(
                settings=base_download_client_settings, base_url=base_url
            )
        else:
            proxy = ConcreteProxy(
                settings=base_download_client_settings, base_url=base_url
            )

        mock_client = MagicMock(spec=httpx.Client)
        mock_create_client.return_value = mock_client

        result = proxy._get_client()

        assert result is mock_client
        mock_create_client.assert_called_once_with(
            timeout=timeout,
            verify=verify,
            follow_redirects=follow_redirects,
        )

    @patch("bookcard.pvr.download_clients.base_proxy.create_httpx_client")
    def test_get_client_uses_settings_timeout(
        self,
        mock_create_client: MagicMock,
        base_download_client_settings: DownloadClientSettings,
        base_url: str,
    ) -> None:
        """Test _get_client uses timeout from settings."""
        base_download_client_settings.timeout_seconds = 120
        proxy = ConcreteProxy(settings=base_download_client_settings, base_url=base_url)

        mock_client = MagicMock(spec=httpx.Client)
        mock_create_client.return_value = mock_client

        proxy._get_client()

        mock_create_client.assert_called_once_with(
            timeout=120,
            verify=True,
            follow_redirects=True,
        )


# ============================================================================
# Abstract Method Tests
# ============================================================================


class TestBaseClientProxyAbstractMethods:
    """Test cases for BaseClientProxy abstract methods."""

    def test_authenticate_raises_not_implemented(
        self,
        base_download_client_settings: DownloadClientSettings,
        base_url: str,
    ) -> None:
        """Test that authenticate raises NotImplementedError when not implemented."""

        # Create a class that doesn't implement authenticate
        # Python's ABC will prevent instantiation
        class IncompleteProxy(BaseClientProxy):
            def test_connection(self) -> bool:
                return True

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            _ = IncompleteProxy(
                settings=base_download_client_settings, base_url=base_url
            )

    def test_authenticate_abstract_method_exists(self) -> None:
        """Test that authenticate is an abstract method."""
        # Verify that authenticate is marked as abstract
        assert hasattr(BaseClientProxy, "authenticate")
        # The method should exist but raise NotImplementedError when called
        # We can't call it directly on the abstract class, but we can verify it's abstract
        import inspect

        assert inspect.isabstract(BaseClientProxy)
        assert "authenticate" in BaseClientProxy.__abstractmethods__

    def test_test_connection_raises_not_implemented(
        self,
        base_download_client_settings: DownloadClientSettings,
        base_url: str,
    ) -> None:
        """Test that test_connection raises NotImplementedError when not implemented."""

        # Create a class that doesn't implement test_connection
        # Python's ABC will prevent instantiation
        class IncompleteProxy(BaseClientProxy):
            def authenticate(self, force: bool = False) -> None:
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            _ = IncompleteProxy(
                settings=base_download_client_settings, base_url=base_url
            )

    def test_test_connection_abstract_method_exists(self) -> None:
        """Test that test_connection is an abstract method."""
        # Verify that test_connection is marked as abstract
        assert hasattr(BaseClientProxy, "test_connection")
        # The method should exist but raise NotImplementedError when called
        # We can't call it directly on the abstract class, but we can verify it's abstract
        import inspect

        assert inspect.isabstract(BaseClientProxy)
        assert "test_connection" in BaseClientProxy.__abstractmethods__

    def test_authenticate_with_force_parameter(
        self, concrete_proxy: ConcreteProxy
    ) -> None:
        """Test authenticate can be called with force parameter."""
        # Should not raise - concrete implementation exists
        concrete_proxy.authenticate(force=False)
        concrete_proxy.authenticate(force=True)

    def test_test_connection_returns_bool(self, concrete_proxy: ConcreteProxy) -> None:
        """Test test_connection returns bool in concrete implementation."""
        result = concrete_proxy.test_connection()
        assert isinstance(result, bool)
        assert result is True
