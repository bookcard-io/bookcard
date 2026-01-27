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

"""Tests for metadata builder to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.metadata_builder import MetadataBuilder


@pytest.fixture
def book() -> Book:
    """Create a test book."""
    return Book(
        id=1,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
        uuid="test-uuid-123",
        has_cover=False,
        path="Author Name/Test Book (1)",
    )


@pytest.fixture
def book_with_rels(book: Book) -> BookWithFullRelations:
    """Create test book with relations."""
    book.series_index = 1.5
    return BookWithFullRelations(
        book=book,
        authors=["Author One", "Author Two"],
        series="Test Series",
        series_id=1,
        tags=["Fiction", "Science Fiction"],
        identifiers=[
            {"type": "isbn", "val": "978-1234567890"},
            {"type": "asin", "val": "B01234567"},
        ],
        description="A test book description",
        publisher="Test Publisher",
        publisher_id=1,
        languages=["en", "fr"],
        language_ids=[1, 2],
        rating=4,
        rating_id=1,
        formats=[{"format": "EPUB", "name": "test.epub", "size": 1000}],
    )


def test_build_full_metadata(book_with_rels: BookWithFullRelations) -> None:
    """Test build with full metadata."""
    result = MetadataBuilder.build(book_with_rels)

    assert result.id == 1
    assert result.title == "Test Book"
    assert result.authors == ["Author One", "Author Two"]
    assert result.uuid == "test-uuid-123"
    assert result.publisher == "Test Publisher"
    assert result.description == "A test book description"
    assert result.languages == ["en", "fr"]
    assert result.identifiers is not None
    assert len(result.identifiers) == 2
    assert result.series == "Test Series"
    assert result.series_index == 1.5
    assert result.tags == ["Fiction", "Science Fiction"]
    assert result.rating == 4
    assert result.isbn == "" or result.isbn is None  # Not set in book fixture
    assert result.formats is not None
    assert len(result.formats) == 1


def test_build_minimal_metadata(book: Book) -> None:
    """Test build with minimal metadata."""
    # Create a new book without series_index set
    minimal_book = Book(
        id=1,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=None,
        uuid="test-uuid-123",
        has_cover=False,
        path="Test Book (1)",
    )
    minimal_book.series_index = (  # ty:ignore[invalid-assignment]
        None  # Explicitly set to None
    )
    book_with_rels = BookWithFullRelations(
        book=minimal_book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )

    result = MetadataBuilder.build(book_with_rels)

    assert result.id == 1
    assert result.title == "Test Book"
    assert result.authors == []
    assert result.uuid == "test-uuid-123"
    assert result.publisher is None
    assert result.description is None
    assert result.languages == []
    assert result.identifiers == []
    assert result.series is None
    assert result.series_index is None
    assert result.tags == []
    assert result.rating is None


def test_build_without_id() -> None:
    """Test build raises ValueError when book has no ID."""
    book = Book(
        id=None,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=None,
        uuid="test-uuid",
        has_cover=False,
        path="Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )

    with pytest.raises(ValueError, match="Book must have an ID"):
        MetadataBuilder.build(book_with_rels)


def test_build_without_uuid(book: Book) -> None:
    """Test build generates UUID when book has no UUID."""
    book.uuid = None
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )

    result = MetadataBuilder.build(book_with_rels)

    assert result.uuid == "calibre-book-1"


def test_format_date_with_datetime() -> None:
    """Test _format_date with datetime object."""
    dt = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    result = MetadataBuilder._format_date(dt)
    assert result == "2020-01-01T12:00:00+00:00"


def test_format_date_with_none() -> None:
    """Test _format_date with None."""
    result = MetadataBuilder._format_date(None)
    assert result is None


def test_format_date_with_string() -> None:
    """Test _format_date with string."""
    result = MetadataBuilder._format_date("2020-01-01")  # type: ignore[arg-type]
    assert result == "2020-01-01"


def test_format_timestamp_with_datetime() -> None:
    """Test _format_timestamp with datetime object."""
    dt = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    result = MetadataBuilder._format_timestamp(dt)
    assert result is not None
    assert "2020-01-01" in result
    assert "T" in result or result.endswith("Z")


def test_format_timestamp_with_none() -> None:
    """Test _format_timestamp with None."""
    result = MetadataBuilder._format_timestamp(None)
    assert result is None


def test_format_timestamp_with_string() -> None:
    """Test _format_timestamp with string."""
    result = MetadataBuilder._format_timestamp("2020-01-01T12:00:00")  # type: ignore[arg-type]
    assert result == "2020-01-01T12:00:00"


def test_format_timestamp_timezone_conversion() -> None:
    """Test _format_timestamp converts to UTC."""
    # Create datetime with different timezone
    from datetime import timedelta, timezone

    tz = timezone(timedelta(hours=5))
    dt = datetime(2020, 1, 1, 12, 0, 0, tzinfo=tz)
    result = MetadataBuilder._format_timestamp(dt)

    assert result is not None
    # Should be converted to UTC
    assert "+00:00" in result or result.endswith("Z")
