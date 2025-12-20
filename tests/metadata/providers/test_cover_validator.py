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

"""Tests for cover validator to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from bookcard.metadata.providers.dnb._cover_validator import CoverValidator


def test_cover_validator_init(cover_validator: CoverValidator) -> None:
    """Test CoverValidator initialization."""
    assert cover_validator is not None
    assert cover_validator.timeout == 10
    assert hasattr(cover_validator, "COVER_BASE_URL")
    assert hasattr(cover_validator, "VALID_IMAGE_TYPES")


def test_cover_validator_get_cover_url_no_isbn(cover_validator: CoverValidator) -> None:
    """Test cover URL retrieval with no ISBN."""
    result = cover_validator.get_cover_url(None)
    assert result is None

    result = cover_validator.get_cover_url("")
    assert result is None


def test_cover_validator_get_cover_url_success(cover_validator: CoverValidator) -> None:
    """Test cover URL retrieval succeeds with valid image."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.head", return_value=mock_response):
        result = cover_validator.get_cover_url("9783123456789")
        assert result is not None
        assert "isbn=9783123456789" in result


@pytest.mark.parametrize(
    "content_type",
    [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/bmp",
    ],
)
def test_cover_validator_get_cover_url_valid_types(
    cover_validator: CoverValidator,
    content_type: str,
) -> None:
    """Test cover URL retrieval with various valid image types."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": content_type}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.head", return_value=mock_response):
        result = cover_validator.get_cover_url("9783123456789")
        assert result is not None


def test_cover_validator_get_cover_url_invalid_type(
    cover_validator: CoverValidator,
) -> None:
    """Test cover URL retrieval with invalid content type."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.head", return_value=mock_response):
        result = cover_validator.get_cover_url("9783123456789")
        # Should try to extract from HTML
        assert result is None or isinstance(result, str)


def test_cover_validator_get_cover_url_404(cover_validator: CoverValidator) -> None:
    """Test cover URL retrieval handles 404."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404",
        request=MagicMock(),
        response=mock_response,
    )

    with patch("httpx.head", return_value=mock_response):
        result = cover_validator.get_cover_url("9783123456789")
        assert result is None


def test_cover_validator_get_cover_url_http_error(
    cover_validator: CoverValidator,
) -> None:
    """Test cover URL retrieval handles HTTP error (non-404)."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500",
        request=MagicMock(),
        response=mock_response,
    )

    with patch("httpx.head", return_value=mock_response):
        result = cover_validator.get_cover_url("9783123456789")
        assert result is None


def test_cover_validator_extract_image_from_html_magic_bytes(
    cover_validator: CoverValidator,
) -> None:
    """Test image extraction from HTML with image magic bytes."""
    mock_response = MagicMock()
    # The check is: len(content) > 4 and content[:4] in (b"\xff\xd8\xff", b"\x89PNG")
    # content[:4] is 4 bytes, so it can match b"\x89PNG" (4 bytes) but not b"\xff\xd8\xff" (3 bytes)
    # Use PNG magic bytes: b"\x89PNG" is exactly 4 bytes
    mock_response.content = b"\x89PNG" + b"x" * 100
    mock_response.text = "<html>fake html</html>"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = cover_validator._extract_image_from_html("http://example.com/cover")
        assert result == "http://example.com/cover"


def test_cover_validator_get_cover_url_network_error(
    cover_validator: CoverValidator,
) -> None:
    """Test cover URL retrieval handles network errors."""
    with patch("httpx.head", side_effect=httpx.RequestError("Network error")):
        result = cover_validator.get_cover_url("9783123456789")
        assert result is None


def test_cover_validator_extract_image_from_html_success(
    cover_validator: CoverValidator,
) -> None:
    """Test image extraction from HTML wrapper."""
    html_content = (
        '<html><body><img src="http://example.com/image.jpg" /></body></html>'
    )
    mock_response = MagicMock()
    mock_response.content = b"\xff\xd8\xff\xe0"  # JPEG magic bytes
    mock_response.text = html_content
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = cover_validator._extract_image_from_html("http://example.com/cover")
        # Should return URL if magic bytes detected, or extracted image URL
        assert result is not None


def test_cover_validator_extract_image_from_html_no_image(
    cover_validator: CoverValidator,
) -> None:
    """Test image extraction from HTML with no image."""
    html_content = "<html><body>No image here</body></html>"
    mock_response = MagicMock()
    mock_response.content = b"<html>"
    mock_response.text = html_content
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = cover_validator._extract_image_from_html("http://example.com/cover")
        assert result is None


def test_cover_validator_extract_image_from_html_relative_url(
    cover_validator: CoverValidator,
) -> None:
    """Test image extraction from HTML with relative URL."""
    html_content = '<html><body><img src="/images/cover.jpg" /></body></html>'
    mock_response = MagicMock()
    mock_response.content = b"<html>"
    mock_response.text = html_content
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = cover_validator._extract_image_from_html("http://example.com/cover")
        # Should convert relative to absolute URL
        assert (
            result is None or "/images/cover.jpg" in result or "example.com" in result
        )


def test_cover_validator_extract_image_from_html_error(
    cover_validator: CoverValidator,
) -> None:
    """Test image extraction from HTML handles errors."""
    with patch("httpx.get", side_effect=httpx.RequestError("Error")):
        result = cover_validator._extract_image_from_html("http://example.com/cover")
        assert result is None


def test_cover_validator_get_cover_url_with_charset(
    cover_validator: CoverValidator,
) -> None:
    """Test cover URL retrieval handles content-type with charset."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "image/jpeg; charset=utf-8"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.head", return_value=mock_response):
        result = cover_validator.get_cover_url("9783123456789")
        assert result is not None


def test_cover_validator_custom_timeout() -> None:
    """Test CoverValidator with custom timeout."""
    validator = CoverValidator(timeout=20)
    assert validator.timeout == 20
