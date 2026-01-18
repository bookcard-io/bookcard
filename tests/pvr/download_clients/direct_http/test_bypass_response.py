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

"""Tests for bypass response module."""

import httpx
import pytest

from bookcard.pvr.download_clients.direct_http.bypass.constants import BypassConstants
from bookcard.pvr.download_clients.direct_http.bypass.response import (
    BypassResponse,
    BypassResponseFactory,
)


class TestBypassResponse:
    """Test BypassResponse class."""

    def test_init_with_dict_headers(self) -> None:
        """Test initialization with dict headers."""
        response = BypassResponse(
            status_code=200,
            text="<html>test</html>",
            headers={"Content-Type": "text/html"},
            url="https://example.com",
        )
        assert response.status_code == 200
        assert response.text == "<html>test</html>"
        assert response.headers["Content-Type"] == "text/html"
        assert response._url == "https://example.com"

    def test_init_with_httpx_headers(self) -> None:
        """Test initialization with httpx.Headers."""
        headers = httpx.Headers({"Content-Type": "text/html"})
        response = BypassResponse(
            status_code=200, text="<html>test</html>", headers=headers
        )
        assert response.headers["Content-Type"] == "text/html"

    def test_init_without_headers(self) -> None:
        """Test initialization without headers."""
        response = BypassResponse(status_code=200, text="<html>test</html>")
        assert isinstance(response.headers, httpx.Headers)
        assert len(response.headers) == 0

    def test_init_without_url(self) -> None:
        """Test initialization without URL."""
        response = BypassResponse(status_code=200, text="<html>test</html>")
        assert response._url == ""

    def test_headers_property(self) -> None:
        """Test headers property."""
        response = BypassResponse(
            status_code=200,
            text="<html>test</html>",
            headers={"Content-Type": "text/html"},
        )
        assert isinstance(response.headers, httpx.Headers)

    def test_status_code_property(self) -> None:
        """Test status_code property."""
        response = BypassResponse(status_code=404, text="Not found")
        assert response.status_code == 404

    def test_text_property(self) -> None:
        """Test text property."""
        response = BypassResponse(status_code=200, text="<html>test</html>")
        assert response.text == "<html>test</html>"

    def test_raise_for_status_success(self) -> None:
        """Test raise_for_status with success status."""
        response = BypassResponse(status_code=200, text="OK")
        response.raise_for_status()  # Should not raise

    @pytest.mark.parametrize(
        "status_code",
        [400, 401, 403, 404, 500, 503],
    )
    def test_raise_for_status_error(self, status_code: int) -> None:
        """Test raise_for_status with error status."""
        response = BypassResponse(
            status_code=status_code,
            text="Error",
            url="https://example.com",
        )
        with pytest.raises(httpx.HTTPStatusError):
            response.raise_for_status()

    def test_iter_bytes_default_chunk_size(self) -> None:
        """Test iter_bytes with default chunk size."""
        text = "a" * 20000  # Large text
        response = BypassResponse(status_code=200, text=text)
        chunks = list(response.iter_bytes())
        assert len(chunks) > 0
        assert b"".join(chunks) == text.encode("utf-8")

    def test_iter_bytes_custom_chunk_size(self) -> None:
        """Test iter_bytes with custom chunk size."""
        text = "test" * 10
        response = BypassResponse(status_code=200, text=text)
        chunks = list(response.iter_bytes(chunk_size=10))
        assert len(chunks) > 0
        assert b"".join(chunks) == text.encode("utf-8")

    def test_iter_bytes_empty_text(self) -> None:
        """Test iter_bytes with empty text."""
        response = BypassResponse(status_code=200, text="")
        chunks = list(response.iter_bytes())
        assert len(chunks) == 0


class TestBypassResponseFactory:
    """Test BypassResponseFactory class."""

    def test_create_error_default(self) -> None:
        """Test create_error with default status code."""
        response = BypassResponseFactory.create_error("https://example.com")
        assert response.status_code == BypassConstants.HTTP_STATUS_SERVICE_UNAVAILABLE
        assert response.text == ""
        assert response._url == "https://example.com"

    def test_create_error_custom_status(self) -> None:
        """Test create_error with custom status code."""
        response = BypassResponseFactory.create_error(
            "https://example.com", status_code=404
        )
        assert response.status_code == 404

    def test_create_success(self) -> None:
        """Test create_success."""
        html = "<html><body>Test</body></html>"
        response = BypassResponseFactory.create_success("https://example.com", html)
        assert response.status_code == BypassConstants.HTTP_STATUS_OK
        assert response.text == html
        assert response.headers["Content-Type"] == BypassConstants.CONTENT_TYPE_HTML
        assert response.headers["Host"] == "example.com"

    def test_create_success_with_port(self) -> None:
        """Test create_success with URL containing port."""
        html = "<html><body>Test</body></html>"
        response = BypassResponseFactory.create_success(
            "https://example.com:8080", html
        )
        assert response.headers["Host"] == "example.com:8080"

    def test_create_success_with_path(self) -> None:
        """Test create_success with URL containing path."""
        html = "<html><body>Test</body></html>"
        response = BypassResponseFactory.create_success(
            "https://example.com/path/to/page", html
        )
        assert response.headers["Host"] == "example.com"
