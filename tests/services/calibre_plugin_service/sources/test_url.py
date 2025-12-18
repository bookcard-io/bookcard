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

"""Tests for URL plugin source to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from bookcard.services.calibre_plugin_service.exceptions import PluginSourceError
from bookcard.services.calibre_plugin_service.sources.base import (
    DefaultTempDirectoryFactory,
)
from bookcard.services.calibre_plugin_service.sources.url import UrlZipSource


@pytest.fixture
def tempdirs() -> DefaultTempDirectoryFactory:
    """Create temp directory factory.

    Returns
    -------
    DefaultTempDirectoryFactory
        Temp directory factory instance.
    """
    return DefaultTempDirectoryFactory()


class TestUrlZipSource:
    """Test UrlZipSource class."""

    def test_open_success(self, tempdirs: DefaultTempDirectoryFactory) -> None:
        """Test open with successful download.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(
            url="https://example.com/plugin.zip",
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PK\x03\x04fake zip content"

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            with source.open() as zip_path:
                assert zip_path.suffix == ".zip"
                assert zip_path.exists()

    def test_validate_url_empty(self, tempdirs: DefaultTempDirectoryFactory) -> None:
        """Test validation rejects empty URL.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(url="", tempdirs=tempdirs, timeout_s=1.0)

        with (
            pytest.raises(PluginSourceError, match="URL cannot be empty"),
            source.open(),
        ):
            pass

    def test_validate_url_whitespace(
        self, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test validation rejects whitespace-only URL.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(url="   ", tempdirs=tempdirs, timeout_s=1.0)

        with (
            pytest.raises(PluginSourceError, match="URL cannot be empty"),
            source.open(),
        ):
            pass

    def test_validate_url_no_scheme(
        self, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test validation rejects URL without scheme.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(
            url="example.com/plugin.zip", tempdirs=tempdirs, timeout_s=1.0
        )

        with (
            pytest.raises(
                PluginSourceError,
                match=r"URL must include a scheme \(e\.g\., http:// or https://\)",
            ),
            source.open(),
        ):
            pass

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com/plugin.zip",
            "file:///path/to/plugin.zip",
            "ssh://example.com/plugin.zip",
        ],
    )
    def test_validate_url_unsupported_scheme(
        self, url: str, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test validation rejects unsupported schemes.

        Parameters
        ----------
        url : str
            URL with unsupported scheme.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(url=url, tempdirs=tempdirs, timeout_s=1.0)

        with (
            pytest.raises(
                PluginSourceError,
                match=r"Unsupported URL scheme.*Only http:// and https:// are supported",
            ),
            source.open(),
        ):
            pass

    def test_open_http_status_error(
        self, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test open when HTTP request returns error status.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(
            url="https://example.com/plugin.zip",
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_response.raise_for_status.side_effect = error

            with (
                pytest.raises(
                    PluginSourceError, match="Failed to download plugin: HTTP 404"
                ),
                source.open(),
            ):
                pass

    def test_open_request_error(self, tempdirs: DefaultTempDirectoryFactory) -> None:
        """Test open when HTTP request fails.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(
            url="https://example.com/plugin.zip",
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        error = httpx.RequestError("Connection failed", request=MagicMock())

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.side_effect = error

            with (
                pytest.raises(PluginSourceError, match="Failed to download plugin:"),
                source.open(),
            ):
                pass

    def test_open_oserror_saving(self, tempdirs: DefaultTempDirectoryFactory) -> None:
        """Test open when saving file fails.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(
            url="https://example.com/plugin.zip",
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PK\x03\x04fake zip content"

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            with (
                patch(
                    "pathlib.Path.write_bytes", side_effect=OSError("Permission denied")
                ),
                pytest.raises(
                    PluginSourceError, match="Failed to save downloaded plugin"
                ),
                source.open(),
            ):
                pass

    def test_open_file_not_found(self, tempdirs: DefaultTempDirectoryFactory) -> None:
        """Test open when downloaded file doesn't exist.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(
            url="https://example.com/plugin.zip",
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PK\x03\x04fake zip content"

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            with (
                patch("pathlib.Path.exists", return_value=False),
                pytest.raises(FileNotFoundError, match="Downloaded file not found"),
                source.open(),
            ):
                pass

    def test_open_not_zip_file(self, tempdirs: DefaultTempDirectoryFactory) -> None:
        """Test open when downloaded file is not a ZIP.

        Parameters
        ----------
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = UrlZipSource(
            url="https://example.com/plugin.txt",
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"not a zip file"

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            # Create a mock Path that exists but has .txt suffix
            mock_path_instance = MagicMock(spec=Path)
            mock_path_instance.exists.return_value = True
            type(mock_path_instance).suffix = property(lambda self: ".txt")

            # Patch Path operations to return our mock
            with (
                patch("pathlib.Path.write_bytes"),
                patch("pathlib.Path.__truediv__", return_value=mock_path_instance),
                pytest.raises(ValueError, match=r"Only \.zip plugins are supported"),
                source.open(),
            ):
                pass
