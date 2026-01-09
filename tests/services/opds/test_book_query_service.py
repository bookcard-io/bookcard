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

from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.repositories.models import BookWithRelations
from bookcard.services.book_permission_helper import BookPermissionHelper
from bookcard.services.book_service import BookService
from bookcard.services.opds.book_query_service import OpdsBookQueryService
from bookcard.services.permission_service import PermissionService


@pytest.fixture
def mock_session() -> Mock:
    return Mock(spec=Session)


@pytest.fixture
def mock_library() -> Mock:
    return Mock(spec=Library)


@pytest.fixture
def mock_book_service() -> Mock:
    return Mock(spec=BookService)


@pytest.fixture
def mock_permission_service() -> Mock:
    return Mock(spec=PermissionService)


@pytest.fixture
def mock_permission_helper() -> Mock:
    return Mock(spec=BookPermissionHelper)


@pytest.fixture
def book_query_service(
    mock_session: Mock,
    mock_library: Mock,
    mock_book_service: Mock,
    mock_permission_service: Mock,
    mock_permission_helper: Mock,
) -> OpdsBookQueryService:
    return OpdsBookQueryService(
        session=mock_session,
        library=mock_library,
        book_service=mock_book_service,
        permission_service=mock_permission_service,
        permission_helper=mock_permission_helper,
    )


class TestOpdsBookQueryService:
    def test_init_defaults(self, mock_session: Mock, mock_library: Mock) -> None:
        """Test initialization with defaults."""
        with (
            patch("bookcard.services.opds.book_query_service.BookService"),
            patch("bookcard.services.opds.book_query_service.PermissionService"),
            patch("bookcard.services.opds.book_query_service.BookPermissionHelper"),
        ):
            service = OpdsBookQueryService(mock_session, mock_library)
            assert service._book_service is not None
            assert service._permission_service is not None
            assert service._permission_helper is not None

    def test_get_books_success(
        self,
        book_query_service: OpdsBookQueryService,
        mock_book_service: Mock,
        mock_permission_service: Mock,
    ) -> None:
        """Test get_books with permission filtering."""
        # Arrange
        user = User(id=1)
        book1 = Mock(spec=BookWithRelations)
        book1.is_virtual = False
        book1.formats = [{"format": "EPUB"}]
        book2 = Mock(spec=BookWithRelations)
        book2.is_virtual = False
        book2.formats = [{"format": "EPUB"}]
        mock_book_service.list_books.return_value = ([book1, book2], 2)

        # Allow book1, deny book2
        mock_permission_service.has_permission.side_effect = [True, False]

        with patch.object(BookPermissionHelper, "build_permission_context") as mock_ctx:
            mock_ctx.return_value = {}

            # Act
            result, count = book_query_service.get_books(user)

            # Assert
            assert result == [book1]
            assert count == 1
            mock_book_service.list_books.assert_called_with(
                page=1, page_size=20, sort_by="timestamp", sort_order="desc", full=False
            )

    def test_get_books_no_user(
        self, book_query_service: OpdsBookQueryService, mock_book_service: Mock
    ) -> None:
        """Test get_books returns empty when no user."""
        mock_book_service.list_books.return_value = ([Mock()], 1)

        result, count = book_query_service.get_books(None)

        assert result == []
        assert count == 0

    def test_get_recent_books(
        self,
        book_query_service: OpdsBookQueryService,
        mock_book_service: Mock,
        mock_permission_service: Mock,
    ) -> None:
        """Test get_recent_books delegates to get_books."""
        # Arrange
        user = User(id=1)
        book = Mock(spec=BookWithRelations)
        book.is_virtual = False
        book.formats = [{"format": "EPUB"}]
        mock_book_service.list_books.return_value = ([book], 1)
        mock_permission_service.has_permission.return_value = True

        with patch.object(BookPermissionHelper, "build_permission_context"):
            result, _count = book_query_service.get_recent_books(user)

            assert result == [book]
            mock_book_service.list_books.assert_called_with(
                page=1, page_size=20, sort_by="timestamp", sort_order="desc", full=False
            )

    def test_get_random_books(
        self,
        book_query_service: OpdsBookQueryService,
        mock_book_service: Mock,
        mock_permission_service: Mock,
    ) -> None:
        """Test get_random_books with filtering."""
        user = User(id=1)
        books = [Mock(spec=BookWithRelations) for _ in range(5)]
        for b in books:
            b.is_virtual = False
            b.formats = [{"format": "EPUB"}]
        mock_book_service.list_books.return_value = (books, 5)
        mock_permission_service.has_permission.return_value = True

        with patch.object(BookPermissionHelper, "build_permission_context"):
            result = book_query_service.get_random_books(user, limit=2)

            assert len(result) == 2
            # Should request larger sample size (limit * 3)
            mock_book_service.list_books.assert_called()
            call_args = mock_book_service.list_books.call_args[1]
            assert call_args["page_size"] == 6  # 2 * 3

    def test_search_books(
        self,
        book_query_service: OpdsBookQueryService,
        mock_book_service: Mock,
        mock_permission_service: Mock,
    ) -> None:
        """Test search_books."""
        user = User(id=1)
        book = Mock(spec=BookWithRelations)
        book.is_virtual = False
        book.formats = [{"format": "EPUB"}]
        mock_book_service.list_books.return_value = ([book], 1)
        mock_permission_service.has_permission.return_value = True

        with patch.object(BookPermissionHelper, "build_permission_context"):
            result, _count = book_query_service.search_books(user, "query")

            assert result == [book]
            mock_book_service.list_books.assert_called_with(
                page=1, page_size=20, search_query="query", full=False
            )

    def test_get_books_by_filter(
        self,
        book_query_service: OpdsBookQueryService,
        mock_book_service: Mock,
        mock_permission_service: Mock,
    ) -> None:
        """Test get_books_by_filter."""
        user = User(id=1)
        book = Mock(spec=BookWithRelations)
        book.is_virtual = False
        book.formats = [{"format": "EPUB"}]
        mock_book_service.list_books_with_filters.return_value = ([book], 1)
        mock_permission_service.has_permission.return_value = True

        with patch.object(BookPermissionHelper, "build_permission_context"):
            result, _count = book_query_service.get_books_by_filter(
                user, author_ids=[1]
            )

            assert result == [book]
            mock_book_service.list_books_with_filters.assert_called_with(
                page=1,
                page_size=20,
                author_ids=[1],
                publisher_ids=None,
                genre_ids=None,
                series_ids=None,
                rating_ids=None,
                formats=None,
                language_ids=None,
                sort_by="timestamp",
                sort_order="desc",
                full=False,
            )

    def test_get_best_rated_books(
        self,
        book_query_service: OpdsBookQueryService,
        mock_book_service: Mock,
        mock_permission_service: Mock,
    ) -> None:
        """Test get_best_rated_books."""
        user = User(id=1)

        # Book 1: High rating
        book1 = Mock(spec=BookWithRelations)
        book1.is_virtual = False
        book1.formats = [{"format": "EPUB"}]
        book1.book = Mock()
        book1.book.rating_id = 9

        # Book 2: Low rating
        book2 = Mock(spec=BookWithRelations)
        book2.is_virtual = False
        book2.formats = [{"format": "EPUB"}]
        book2.book = Mock()
        # Mocking empty rating_id or 0
        book2.book.rating_id = 0

        # Book 3: No rating attr
        book3 = Mock(spec=BookWithRelations)
        book3.is_virtual = False
        book3.formats = [{"format": "EPUB"}]
        # Mock book3.book to NOT have rating_id set correctly or None
        book3.book = Mock()
        book3.book.rating_id = None

        mock_book_service.list_books_with_filters.return_value = (
            [book1, book2, book3],
            3,
        )
        mock_permission_service.has_permission.return_value = True

        with patch.object(BookPermissionHelper, "build_permission_context"):
            result, _count = book_query_service.get_best_rated_books(user)

            assert len(result) == 1
            assert result[0] == book1

    def test_filters_out_virtual_without_formats(
        self,
        book_query_service: OpdsBookQueryService,
        mock_book_service: Mock,
        mock_permission_service: Mock,
    ) -> None:
        """Virtual items without formats are excluded from OPDS feeds."""
        user = User(id=1)
        virtual_no_formats = Mock(spec=BookWithRelations)
        virtual_no_formats.is_virtual = True
        virtual_no_formats.formats = []

        mock_book_service.list_books.return_value = ([virtual_no_formats], 1)
        mock_permission_service.has_permission.return_value = True

        with patch.object(BookPermissionHelper, "build_permission_context"):
            result, count = book_query_service.get_books(user)

        assert result == []
        assert count == 0
