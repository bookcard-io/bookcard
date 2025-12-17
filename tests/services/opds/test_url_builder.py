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

from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi import Request

from bookcard.services.opds.url_builder import OpdsUrlBuilder


@pytest.fixture
def mock_request() -> Mock:
    request = Mock(spec=Request)
    request.base_url = "http://testserver/"
    return request


@pytest.fixture
def url_builder(mock_request: Mock) -> OpdsUrlBuilder:
    return OpdsUrlBuilder(mock_request)


class TestOpdsUrlBuilder:
    def test_init(self, url_builder: OpdsUrlBuilder) -> None:
        assert url_builder is not None

    def test_build_opds_url_simple(self, url_builder: OpdsUrlBuilder) -> None:
        """Test building simple URL."""
        url = url_builder.build_opds_url("/opds/books")
        assert url == "http://testserver/opds/books"

    def test_build_opds_url_with_params(self, url_builder: OpdsUrlBuilder) -> None:
        """Test building URL with query params."""
        params: dict[str, str | int] = {"page": 1, "sort": "asc"}
        url = url_builder.build_opds_url("/opds/books", params)
        # Should filter out None and encode
        assert url == "http://testserver/opds/books?page=1&sort=asc"

        # Test with None values (should be filtered out)
        params_with_none: dict[str, str | int | None] = {
            "page": 1,
            "sort": "asc",
            "empty": None,
        }
        url2 = url_builder.build_opds_url("/opds/books", params_with_none)  # type: ignore[arg-type]
        assert url2 == "http://testserver/opds/books?page=1&sort=asc"

    def test_build_download_url(self, url_builder: OpdsUrlBuilder) -> None:
        """Test building download URL."""
        url = url_builder.build_download_url(123, "EPUB")
        assert url == "http://testserver/api/books/123/download/EPUB"

    def test_build_cover_url(self, url_builder: OpdsUrlBuilder) -> None:
        """Test building cover URL."""
        url = url_builder.build_cover_url(123)
        assert url == "http://testserver/api/books/123/cover"

    def test_build_pagination_url(self, url_builder: OpdsUrlBuilder) -> None:
        """Test building pagination URL."""
        url = url_builder.build_pagination_url("/opds/books", offset=20, page_size=10)
        assert url == "http://testserver/opds/books?offset=20&page_size=10"

    def test_build_pagination_url_no_page_size(
        self, url_builder: OpdsUrlBuilder
    ) -> None:
        """Test building pagination URL without page size."""
        url = url_builder.build_pagination_url("/opds/books", offset=20)
        assert url == "http://testserver/opds/books?offset=20"
