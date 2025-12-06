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

"""Tests for AuthorExceptionMapper to achieve 100% coverage."""

from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from fundamental.services.author_exception_mapper import AuthorExceptionMapper
from fundamental.services.author_exceptions import (
    AuthorMetadataFetchError,
    AuthorNotFoundError,
    AuthorServiceError,
    InvalidPhotoFormatError,
    NoActiveLibraryError,
    PhotoNotFoundError,
    PhotoStorageError,
)


class TestMapValueErrorToHttpException:
    """Test map_value_error_to_http_exception method."""

    @pytest.mark.parametrize(
        ("error", "expected_status", "expected_detail"),
        [
            (
                AuthorNotFoundError("Author not found"),
                status.HTTP_404_NOT_FOUND,
                "Author not found",
            ),
            (
                NoActiveLibraryError("No active library"),
                status.HTTP_404_NOT_FOUND,
                "No active library found",
            ),
            (
                InvalidPhotoFormatError("Invalid format"),
                status.HTTP_400_BAD_REQUEST,
                "Invalid format",
            ),
            (
                AuthorMetadataFetchError("Fetch failed"),
                status.HTTP_400_BAD_REQUEST,
                "Fetch failed",
            ),
            (
                PhotoNotFoundError("Photo not found"),
                status.HTTP_404_NOT_FOUND,
                "Photo not found",
            ),
            (
                PhotoStorageError("Storage failed"),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Storage failed",
            ),
        ],
    )
    def test_map_domain_exceptions(
        self,
        error: AuthorServiceError,
        expected_status: int,
        expected_detail: str,
    ) -> None:
        """Test mapping domain-specific exceptions (covers lines 59-87)."""
        result = AuthorExceptionMapper.map_value_error_to_http_exception(error)

        assert isinstance(result, HTTPException)
        assert result.status_code == expected_status
        assert result.detail == expected_detail

    @pytest.mark.parametrize(
        ("error_msg", "expected_status", "expected_detail"),
        [
            ("Author not found", status.HTTP_404_NOT_FOUND, "Author not found"),
            ("author not found", status.HTTP_404_NOT_FOUND, "author not found"),
            ("NOT FOUND", status.HTTP_404_NOT_FOUND, "NOT FOUND"),
            (
                "No active library found",
                status.HTTP_404_NOT_FOUND,
                "No active library found",
            ),
            (
                "does not have an OpenLibrary key",
                status.HTTP_400_BAD_REQUEST,
                "does not have an OpenLibrary key",
            ),
            (
                "Invalid author ID format",
                status.HTTP_400_BAD_REQUEST,
                "Invalid author ID format",
            ),
            (
                "Author mapping not found",
                status.HTTP_404_NOT_FOUND,
                "Author mapping not found",
            ),
            (
                "Author metadata ID not found",
                status.HTTP_404_NOT_FOUND,
                "Author metadata ID not found",
            ),
            (
                "Could not determine library ID",
                status.HTTP_400_BAD_REQUEST,
                "Could not determine library ID",
            ),
            (
                "Message broker not available",
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Message broker not available",
            ),
            ("Unknown error", status.HTTP_500_INTERNAL_SERVER_ERROR, "Unknown error"),
        ],
    )
    def test_map_value_error_fallback(
        self,
        error_msg: str,
        expected_status: int,
        expected_detail: str,
    ) -> None:
        """Test mapping ValueError fallback cases (covers lines 89-129)."""
        error = ValueError(error_msg)

        result = AuthorExceptionMapper.map_value_error_to_http_exception(error)

        assert isinstance(result, HTTPException)
        assert result.status_code == expected_status
        assert result.detail == expected_detail


class TestMapPhotoErrorToHttpException:
    """Test map_photo_error_to_http_exception method."""

    @pytest.mark.parametrize(
        ("error", "expected_status", "expected_detail"),
        [
            (
                PhotoNotFoundError("Photo not found"),
                status.HTTP_404_NOT_FOUND,
                "Photo not found",
            ),
            (
                InvalidPhotoFormatError("Invalid format"),
                status.HTTP_400_BAD_REQUEST,
                "Invalid format",
            ),
            (
                PhotoStorageError("Storage failed"),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Storage failed",
            ),
        ],
    )
    def test_map_domain_exceptions(
        self,
        error: AuthorServiceError,
        expected_status: int,
        expected_detail: str,
    ) -> None:
        """Test mapping domain-specific photo exceptions (covers lines 148-164)."""
        result = AuthorExceptionMapper.map_photo_error_to_http_exception(error)

        assert isinstance(result, HTTPException)
        assert result.status_code == expected_status
        assert result.detail == expected_detail

    @pytest.mark.parametrize(
        ("error_msg", "expected_status", "expected_detail"),
        [
            ("Photo not found", 404, "Photo not found"),
            ("photo not found", 404, "photo not found"),
            ("NOT FOUND", 404, "NOT FOUND"),
            ("invalid_file_type", 400, "invalid_file_type"),
            ("url_not_an_image", 400, "url_not_an_image"),
            ("invalid_image_format", 400, "invalid_image_format"),
            ("failed_to_download_image: error", 500, "failed_to_download_image: error"),
            ("failed_to_save_file: error", 500, "failed_to_save_file: error"),
            ("Unknown error", status.HTTP_500_INTERNAL_SERVER_ERROR, "Unknown error"),
        ],
    )
    def test_map_value_error_fallback(
        self,
        error_msg: str,
        expected_status: int,
        expected_detail: str,
    ) -> None:
        """Test mapping ValueError fallback cases (covers lines 166-185)."""
        error = ValueError(error_msg)

        result = AuthorExceptionMapper.map_photo_error_to_http_exception(error)

        assert isinstance(result, HTTPException)
        assert result.status_code == expected_status
        assert result.detail == expected_detail
