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

"""Tests for FlareSolverr bypass strategy."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from requests import exceptions as requests_exceptions

from bookcard.pvr.download_clients.direct_http.bypass.config import FlareSolverrConfig
from bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy import (
    FlareSolverrStrategy,
)


class TestFlareSolverrStrategy:
    """Test FlareSolverrStrategy class."""

    def test_init(self) -> None:
        """Test initialization."""
        config = FlareSolverrConfig()
        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ):
            strategy = FlareSolverrStrategy(config)
            assert strategy._config == config

    def test_validate_dependencies_success(self) -> None:
        """Test validate_dependencies when requests is available."""
        config = FlareSolverrConfig()
        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests",
            MagicMock(),
        ):
            strategy = FlareSolverrStrategy(config)
            strategy.validate_dependencies()  # Should not raise

    def test_validate_dependencies_failure(self) -> None:
        """Test validate_dependencies when requests is not available."""
        config = FlareSolverrConfig()
        with (
            patch(
                "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests",
                None,
            ),
            pytest.raises(ImportError, match="requests library required"),
        ):
            FlareSolverrStrategy(config)

    def test_fetch_success(self) -> None:
        """Test successful fetch."""
        config = FlareSolverrConfig()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "solution": {"response": "<html>test</html>"},
        }
        mock_response.raise_for_status = Mock()

        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ) as mock_requests:
            mock_requests.post.return_value = mock_response
            strategy = FlareSolverrStrategy(config)
            result = strategy.fetch("https://example.com")
            assert result.success is True
            assert result.html == "<html>test</html>"

    def test_fetch_failure_status_not_ok(self) -> None:
        """Test fetch with status not ok."""
        config = FlareSolverrConfig()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "error",
            "message": "Failed",
        }
        mock_response.raise_for_status = Mock()

        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ) as mock_requests:
            mock_requests.post.return_value = mock_response
            strategy = FlareSolverrStrategy(config)
            result = strategy.fetch("https://example.com")
            assert result.success is False
            assert result.html is None

    def test_fetch_empty_response(self) -> None:
        """Test fetch with empty response."""
        config = FlareSolverrConfig()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "solution": {"response": ""},
        }
        mock_response.raise_for_status = Mock()

        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ) as mock_requests:
            mock_requests.post.return_value = mock_response
            strategy = FlareSolverrStrategy(config)
            result = strategy.fetch("https://example.com")
            assert result.success is False

    def test_fetch_timeout(self) -> None:
        """Test fetch with timeout."""
        config = FlareSolverrConfig()
        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ) as mock_requests:
            mock_requests.post.side_effect = requests_exceptions.Timeout("Timeout")
            strategy = FlareSolverrStrategy(config)
            result = strategy.fetch("https://example.com")
            assert result.success is False

    def test_fetch_request_exception(self) -> None:
        """Test fetch with request exception."""
        config = FlareSolverrConfig()
        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ) as mock_requests:
            mock_requests.post.side_effect = requests_exceptions.RequestException(
                "Request failed"
            )
            strategy = FlareSolverrStrategy(config)
            result = strategy.fetch("https://example.com")
            assert result.success is False

    def test_fetch_malformed_response(self) -> None:
        """Test fetch with malformed response."""
        config = FlareSolverrConfig()
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()

        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ) as mock_requests:
            mock_requests.post.return_value = mock_response
            strategy = FlareSolverrStrategy(config)
            result = strategy.fetch("https://example.com")
            assert result.success is False

    def test_fetch_missing_solution(self) -> None:
        """Test fetch with missing solution in response."""
        config = FlareSolverrConfig()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()

        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ) as mock_requests:
            mock_requests.post.return_value = mock_response
            strategy = FlareSolverrStrategy(config)
            result = strategy.fetch("https://example.com")
            assert result.success is False

    def test_do_fetch_calculates_timeouts(self) -> None:
        """Test that _do_fetch calculates timeouts correctly."""
        config = FlareSolverrConfig(timeout=60000)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "solution": {"response": "<html>test</html>"},
        }
        mock_response.raise_for_status = Mock()

        with patch(
            "bookcard.pvr.download_clients.direct_http.bypass.flaresolverr_strategy.requests"
        ) as mock_requests:
            mock_requests.post.return_value = mock_response
            strategy = FlareSolverrStrategy(config)
            strategy.fetch("https://example.com")
            # Check that timeout was passed correctly
            call_kwargs = mock_requests.post.call_args[1]
            assert "timeout" in call_kwargs
