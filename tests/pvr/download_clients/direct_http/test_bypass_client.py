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

"""Tests for bypass client module."""

from unittest.mock import MagicMock, patch

from bookcard.pvr.download_clients.direct_http.bypass.client import BypassClient
from bookcard.pvr.download_clients.direct_http.bypass.result import BypassResult


class TestBypassClient:
    """Test BypassClient class."""

    def test_init_flaresolverr(self) -> None:
        """Test initialization with FlareSolverr."""
        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.client.FlareSolverrStrategy"
        ) as mock_strategy_class:
            mock_strategy = MagicMock()
            mock_strategy_class.return_value = mock_strategy
            client = BypassClient(
                flaresolverr_url="http://custom:8191",
                flaresolverr_path="/v2",
                flaresolverr_timeout=120000,
                use_seleniumbase=False,
            )
            assert client._strategy == mock_strategy

    def test_init_seleniumbase(self) -> None:
        """Test initialization with SeleniumBase."""
        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.client.SeleniumBaseStrategy"
        ) as mock_strategy_class:
            mock_strategy = MagicMock()
            mock_strategy_class.return_value = mock_strategy
            client = BypassClient(use_seleniumbase=True)
            assert client._strategy == mock_strategy

    def test_get_success(self) -> None:
        """Test successful get request."""
        mock_strategy = MagicMock()
        mock_result = BypassResult(html="<html>test</html>")
        mock_strategy.fetch.return_value = mock_result

        client = BypassClient(use_seleniumbase=False)
        client._strategy = mock_strategy

        response = client.get("https://example.com")
        assert response.status_code == 200
        assert response.text == "<html>test</html>"

    def test_get_failure(self) -> None:
        """Test failed get request."""
        mock_strategy = MagicMock()
        mock_result = BypassResult(html=None, error="Failed")
        mock_strategy.fetch.return_value = mock_result

        client = BypassClient(use_seleniumbase=False)
        client._strategy = mock_strategy

        response = client.get("https://example.com")
        assert response.status_code == 503
        assert response.text == ""

    def test_get_removes_unsupported_kwargs(self) -> None:
        """Test that unsupported kwargs are removed."""
        mock_strategy = MagicMock()
        mock_result = BypassResult(html="<html>test</html>")
        mock_strategy.fetch.return_value = mock_result

        client = BypassClient(use_seleniumbase=False)
        client._strategy = mock_strategy

        client.get(
            "https://example.com",
            follow_redirects=True,
            extensions={},
        )
        # Should not raise and should call strategy.fetch
        mock_strategy.fetch.assert_called_once_with("https://example.com")

    def test_context_manager(self) -> None:
        """Test context manager protocol."""
        client = BypassClient(use_seleniumbase=False)
        with client as ctx_client:
            assert ctx_client == client

    def test_exit_context_manager(self) -> None:
        """Test exiting context manager."""
        client = BypassClient(use_seleniumbase=False)
        # Should not raise
        client.__exit__(None, None, None)
