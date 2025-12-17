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

"""Tests for BookResponseBuilder to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from bookcard.api.schemas import BookRead
from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations, BookWithRelations
from bookcard.services.book_response_builder import BookResponseBuilder
from bookcard.services.book_service import BookService

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_book_service() -> MagicMock:
    """Create a mock book service."""
    return MagicMock(spec=BookService)


@pytest.fixture
def response_builder(mock_book_service: MagicMock) -> BookResponseBuilder:
    """Create BookResponseBuilder instance."""
    return BookResponseBuilder(mock_book_service)


@pytest.fixture
def book() -> Book:
    """Create sample book."""
    return Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
        timestamp=datetime(2020, 1, 1, tzinfo=UTC),
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
    )


@pytest.fixture
def book_with_relations(book: Book) -> BookWithRelations:
    """Create BookWithRelations."""
    return BookWithRelations(
        book=book,
        authors=["Author One", "Author Two"],
        series="Test Series",
        formats=[],
    )


@pytest.fixture
def book_with_full_relations(book: Book) -> BookWithFullRelations:
    """Create BookWithFullRelations."""
    return BookWithFullRelations(
        book=book,
        authors=["Author One", "Author Two"],
        series="Test Series",
        series_id=1,
        tags=["Fiction", "Sci-Fi"],
        identifiers=[{"type": "isbn", "val": "1234567890"}],
        description="Test description",
        publisher="Test Publisher",
        publisher_id=1,
        languages=["en"],
        language_ids=[1],
        rating=5,
        rating_id=1,
        formats=[{"format": "EPUB", "name": "test.epub", "size": 1000}],
    )


@pytest.fixture
def book_no_id() -> Book:
    """Create book without ID."""
    return Book(
        id=None,
        title="Test Book",
        author_sort="Author, Test",
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
        timestamp=datetime(2020, 1, 1, tzinfo=UTC),
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
    )


# ============================================================================
# Initialization Tests
# ============================================================================


class TestBookResponseBuilderInit:
    """Test BookResponseBuilder initialization."""

    def test_init(
        self,
        mock_book_service: MagicMock,
    ) -> None:
        """Test __init__ stores book service."""
        builder = BookResponseBuilder(mock_book_service)

        assert builder._book_service == mock_book_service


# ============================================================================
# build_book_read Tests
# ============================================================================


class TestBuildBookRead:
    """Test build_book_read method."""

    def test_build_book_read_with_relations(
        self,
        response_builder: BookResponseBuilder,
        mock_book_service: MagicMock,
        book_with_relations: BookWithRelations,
    ) -> None:
        """Test build_book_read with BookWithRelations."""
        mock_book_service.get_thumbnail_url.return_value = "/api/books/1/cover"

        result = response_builder.build_book_read(book_with_relations, full=False)

        assert isinstance(result, BookRead)
        assert result.id == 1
        assert result.title == "Test Book"
        assert result.authors == ["Author One", "Author Two"]
        assert result.series == "Test Series"
        assert result.thumbnail_url == "/api/books/1/cover"
        # Tags should be empty list by default, not None
        assert result.tags == []

    def test_build_book_read_with_full_relations(
        self,
        response_builder: BookResponseBuilder,
        mock_book_service: MagicMock,
        book_with_full_relations: BookWithFullRelations,
    ) -> None:
        """Test build_book_read with BookWithFullRelations and full=True."""
        mock_book_service.get_thumbnail_url.return_value = "/api/books/1/cover"

        result = response_builder.build_book_read(book_with_full_relations, full=True)

        assert isinstance(result, BookRead)
        assert result.id == 1
        assert result.title == "Test Book"
        assert result.tags == ["Fiction", "Sci-Fi"]
        assert result.identifiers == [{"type": "isbn", "val": "1234567890"}]
        assert result.description == "Test description"
        assert result.publisher == "Test Publisher"
        assert result.publisher_id == 1
        assert result.languages == ["en"]
        assert result.language_ids == [1]
        assert result.rating == 5
        assert result.rating_id == 1
        assert result.series_id == 1
        assert result.formats == [{"format": "EPUB", "name": "test.epub", "size": 1000}]

    def test_build_book_read_with_full_relations_full_false(
        self,
        response_builder: BookResponseBuilder,
        mock_book_service: MagicMock,
        book_with_full_relations: BookWithFullRelations,
    ) -> None:
        """Test build_book_read with BookWithFullRelations and full=False."""
        mock_book_service.get_thumbnail_url.return_value = "/api/books/1/cover"

        result = response_builder.build_book_read(book_with_full_relations, full=False)

        assert isinstance(result, BookRead)
        assert result.id == 1
        # Full details should not be included (tags should be empty list)
        assert result.tags == []

    def test_build_book_read_with_relations_full_true(
        self,
        response_builder: BookResponseBuilder,
        mock_book_service: MagicMock,
        book_with_relations: BookWithRelations,
    ) -> None:
        """Test build_book_read with BookWithRelations and full=True (should not add full details)."""
        mock_book_service.get_thumbnail_url.return_value = "/api/books/1/cover"

        result = response_builder.build_book_read(book_with_relations, full=True)

        assert isinstance(result, BookRead)
        assert result.id == 1
        # BookWithRelations doesn't have full details, so tags should be empty list
        assert result.tags == []

    def test_build_book_read_no_id(
        self,
        response_builder: BookResponseBuilder,
        mock_book_service: MagicMock,
        book_no_id: Book,
    ) -> None:
        """Test build_book_read raises error when book has no ID."""
        book_with_rels = BookWithRelations(
            book=book_no_id,
            authors=["Author One"],
            series=None,
            formats=[],
        )

        with pytest.raises(ValueError, match="book_missing_id"):
            response_builder.build_book_read(book_with_rels)


# ============================================================================
# build_book_read_list Tests
# ============================================================================


class TestBuildBookReadList:
    """Test build_book_read_list method."""

    def test_build_book_read_list_success(
        self,
        response_builder: BookResponseBuilder,
        mock_book_service: MagicMock,
        book_with_relations: BookWithRelations,
    ) -> None:
        """Test build_book_read_list with valid books."""
        mock_book_service.get_thumbnail_url.return_value = "/api/books/1/cover"
        books = [book_with_relations]

        result = response_builder.build_book_read_list(books, full=False)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], BookRead)
        assert result[0].id == 1

    def test_build_book_read_list_with_full(
        self,
        response_builder: BookResponseBuilder,
        mock_book_service: MagicMock,
        book_with_full_relations: BookWithFullRelations,
    ) -> None:
        """Test build_book_read_list with full=True."""
        mock_book_service.get_thumbnail_url.return_value = "/api/books/1/cover"
        books = [book_with_full_relations]

        result = response_builder.build_book_read_list(books, full=True)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].tags == ["Fiction", "Sci-Fi"]

    def test_build_book_read_list_skips_no_id(
        self,
        response_builder: BookResponseBuilder,
        mock_book_service: MagicMock,
        book_with_relations: BookWithRelations,
        book_no_id: Book,
    ) -> None:
        """Test build_book_read_list skips books without IDs."""
        mock_book_service.get_thumbnail_url.return_value = "/api/books/1/cover"
        book_with_no_id = BookWithRelations(
            book=book_no_id,
            authors=["Author One"],
            series=None,
            formats=[],
        )
        books = [book_with_relations, book_with_no_id]

        result = response_builder.build_book_read_list(books, full=False)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == 1

    def test_build_book_read_list_empty(
        self,
        response_builder: BookResponseBuilder,
    ) -> None:
        """Test build_book_read_list with empty list."""
        books: list[BookWithRelations | BookWithFullRelations] = []

        result = response_builder.build_book_read_list(books, full=False)

        assert isinstance(result, list)
        assert len(result) == 0
