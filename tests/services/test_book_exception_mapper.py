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

"""Tests for BookExceptionMapper to achieve 100% coverage."""

from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from bookcard.services.book_exception_mapper import BookExceptionMapper

# ============================================================================
# map_value_error_to_http_exception Tests
# ============================================================================


class TestMapValueErrorToHttpException:
    """Test map_value_error_to_http_exception method."""

    @pytest.mark.parametrize(
        ("error_msg", "expected_status", "expected_detail"),
        [
            ("book_not_found", status.HTTP_404_NOT_FOUND, "book_not_found"),
            ("Book not found", status.HTTP_404_NOT_FOUND, "Book not found"),
            ("NOT FOUND", status.HTTP_404_NOT_FOUND, "NOT FOUND"),
            ("no_active_library", status.HTTP_404_NOT_FOUND, "no_active_library"),
            (
                "No active library",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "No active library",
            ),
            (
                "No active library found",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "No active library found",
            ),
            (
                "no active library",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "no active library",
            ),
            ("format_not_found", status.HTTP_400_BAD_REQUEST, "format_not_found"),
            ("file_not_found", status.HTTP_400_BAD_REQUEST, "file_not_found"),
            ("Unsupported format", status.HTTP_400_BAD_REQUEST, "Unsupported format"),
            (
                "file_extension_required",
                status.HTTP_400_BAD_REQUEST,
                "file_extension_required",
            ),
            ("url_required", status.HTTP_400_BAD_REQUEST, "url_required"),
            ("invalid_url_format", status.HTTP_400_BAD_REQUEST, "invalid_url_format"),
            (
                "email_server_not_configured",
                status.HTTP_400_BAD_REQUEST,
                "email_server_not_configured",
            ),
            (
                "Task runner not available",
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Task runner not available",
            ),
            ("Unknown error", status.HTTP_500_INTERNAL_SERVER_ERROR, "Unknown error"),
        ],
    )
    def test_map_value_error_to_http_exception(
        self,
        error_msg: str,
        expected_status: int,
        expected_detail: str,
    ) -> None:
        """Test map_value_error_to_http_exception with various error messages."""
        error = ValueError(error_msg)

        result = BookExceptionMapper.map_value_error_to_http_exception(error)

        assert isinstance(result, HTTPException)
        assert result.status_code == expected_status
        assert result.detail == expected_detail


# ============================================================================
# map_cover_error_to_http_exception Tests
# ============================================================================


class TestMapCoverErrorToHttpException:
    """Test map_cover_error_to_http_exception method."""

    @pytest.mark.parametrize(
        ("error_msg", "expected_status", "expected_detail"),
        [
            ("book_not_found", status.HTTP_500_INTERNAL_SERVER_ERROR, "book_not_found"),
            ("Book not found", 404, "Book not found"),
            ("not found", 404, "not found"),
            ("NOT FOUND", 404, "NOT FOUND"),
            ("url_not_an_image", 400, "url_not_an_image"),
            ("invalid_image_format", 400, "invalid_image_format"),
            ("url_required", 400, "url_required"),
            ("invalid_url_format", 400, "invalid_url_format"),
            (
                "failed_to_download_image: Connection error",
                500,
                "failed_to_download_image: Connection error",
            ),
            (
                "failed_to_save_file: Permission denied",
                500,
                "failed_to_save_file: Permission denied",
            ),
            ("Unknown error", status.HTTP_500_INTERNAL_SERVER_ERROR, "Unknown error"),
        ],
    )
    def test_map_cover_error_to_http_exception_value_error(
        self,
        error_msg: str,
        expected_status: int,
        expected_detail: str,
    ) -> None:
        """Test map_cover_error_to_http_exception with ValueError."""
        error = ValueError(error_msg)

        result = BookExceptionMapper.map_cover_error_to_http_exception(error)

        assert isinstance(result, HTTPException)
        assert result.status_code == expected_status
        assert result.detail == expected_detail

    def test_map_cover_error_to_http_exception_generic_exception(
        self,
    ) -> None:
        """Test map_cover_error_to_http_exception with generic Exception."""
        error = Exception("Generic error")

        result = BookExceptionMapper.map_cover_error_to_http_exception(error)

        assert isinstance(result, HTTPException)
        assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert result.detail == "Generic error"
