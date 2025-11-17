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

"""Tests for metadata export utils to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from fundamental.models.core import Book
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.metadata_builder import StructuredMetadata
from fundamental.services.metadata_export_utils import (
    FilenameGenerator,
    MetadataExportResult,
    MetadataSerializer,
)


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
    return BookWithFullRelations(
        book=book,
        authors=["Author One", "Author Two"],
        series="Test Series",
        series_id=1,
        tags=["Fiction"],
        identifiers=[],
        description="Description",
        publisher="Publisher",
        publisher_id=1,
        languages=["en"],
        language_ids=[1],
        rating=4,
        rating_id=1,
        formats=[],
    )


@pytest.fixture
def structured_metadata() -> StructuredMetadata:
    """Create structured metadata."""
    return StructuredMetadata(
        id=1,
        title="Test Book",
        authors=["Author One"],
        uuid="test-uuid",
        author_sort="One, Author",
        publisher="Test Publisher",
        pubdate="2020-01-01",
        timestamp="2020-01-01T12:00:00+00:00",
        description="Test description",
        languages=["en"],
        identifiers=[{"type": "isbn", "val": "978-1234567890"}],
        series="Test Series",
        series_index=1.5,
        tags=["Fiction"],
        rating=4,
        isbn="978-1234567890",
        formats=[{"format": "EPUB", "name": "test.epub"}],
    )


def test_metadata_export_result() -> None:
    """Test MetadataExportResult dataclass."""
    result = MetadataExportResult(
        content="test content",
        filename="test.opf",
        media_type="application/xml",
    )

    assert result.content == "test content"
    assert result.filename == "test.opf"
    assert result.media_type == "application/xml"


def test_filename_generator_with_authors(
    book_with_rels: BookWithFullRelations, book: Book
) -> None:
    """Test FilenameGenerator.generate with authors."""
    filename = FilenameGenerator.generate(book_with_rels, book, "opf")

    assert filename.endswith(".opf")
    assert "Author One" in filename or "Author Two" in filename
    assert "Test Book" in filename


def test_filename_generator_without_authors(book: Book) -> None:
    """Test FilenameGenerator.generate without authors."""
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

    filename = FilenameGenerator.generate(book_with_rels, book, "json")

    assert filename.endswith(".json")
    assert "Unknown" in filename
    assert "Test Book" in filename


def test_filename_generator_without_title(book: Book) -> None:
    """Test FilenameGenerator.generate without title."""
    book.title = ""
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Author One"],
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

    filename = FilenameGenerator.generate(book_with_rels, book, "yaml")

    assert filename.endswith(".yaml")
    assert "book_1" in filename


def test_filename_generator_sanitizes_special_chars(book: Book) -> None:
    """Test FilenameGenerator.generate sanitizes special characters."""
    book.title = "Test/Book: With*Special?Chars"
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Author/Name"],
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

    filename = FilenameGenerator.generate(book_with_rels, book, "opf")

    assert "/" not in filename or filename.count("/") == 1  # Only separator
    assert ":" not in filename
    assert "*" not in filename
    assert "?" not in filename


def test_metadata_serializer_to_dict_full(
    structured_metadata: StructuredMetadata,
) -> None:
    """Test MetadataSerializer.to_dict with full metadata."""
    result = MetadataSerializer.to_dict(structured_metadata)

    assert result["id"] == 1
    assert result["title"] == "Test Book"
    assert result["authors"] == ["Author One"]
    assert result["uuid"] == "test-uuid"
    assert result["author_sort"] == "One, Author"
    assert result["publisher"] == "Test Publisher"
    assert result["pubdate"] == "2020-01-01"
    assert result["timestamp"] == "2020-01-01T12:00:00+00:00"
    assert result["description"] == "Test description"
    assert result["languages"] == ["en"]
    assert len(result["identifiers"]) == 1
    assert result["series"] == "Test Series"
    assert result["series_index"] == 1.5
    assert result["tags"] == ["Fiction"]
    assert result["rating"] == 4
    assert result["isbn"] == "978-1234567890"
    assert len(result["formats"]) == 1


def test_metadata_serializer_to_dict_minimal() -> None:
    """Test MetadataSerializer.to_dict with minimal metadata."""
    structured = StructuredMetadata(
        id=1,
        title="Test Book",
        authors=[],
        uuid="test-uuid",
    )

    result = MetadataSerializer.to_dict(structured)

    assert result["id"] == 1
    assert result["title"] == "Test Book"
    assert result["authors"] == []
    assert result["uuid"] == "test-uuid"
    assert "author_sort" not in result
    assert "publisher" not in result
    assert "description" not in result


def test_metadata_serializer_to_dict_series_without_index() -> None:
    """Test MetadataSerializer.to_dict with series but no index."""
    structured = StructuredMetadata(
        id=1,
        title="Test Book",
        authors=[],
        uuid="test-uuid",
        series="Test Series",
        series_index=None,
    )

    result = MetadataSerializer.to_dict(structured)

    assert result["series"] == "Test Series"
    assert "series_index" not in result


def test_metadata_serializer_to_dict_series_index_without_series() -> None:
    """Test MetadataSerializer.to_dict with series_index but no series."""
    structured = StructuredMetadata(
        id=1,
        title="Test Book",
        authors=[],
        uuid="test-uuid",
        series=None,
        series_index=1.5,
    )

    result = MetadataSerializer.to_dict(structured)

    assert "series" not in result
    assert "series_index" not in result


def test_metadata_serializer_to_dict_rating_zero() -> None:
    """Test MetadataSerializer.to_dict with rating of 0."""
    structured = StructuredMetadata(
        id=1,
        title="Test Book",
        authors=[],
        uuid="test-uuid",
        rating=0,
    )

    result = MetadataSerializer.to_dict(structured)

    assert result["rating"] == 0


def test_metadata_serializer_add_optional_string_fields() -> None:
    """Test _add_optional_string_fields."""
    metadata = {}
    structured = StructuredMetadata(
        id=1,
        title="Test",
        authors=[],
        uuid="test",
        author_sort="Sort",
        publisher="Publisher",
        pubdate="2020-01-01",
        timestamp="2020-01-01T12:00:00",
        description="Description",
        isbn="978-1234567890",
    )

    MetadataSerializer._add_optional_string_fields(metadata, structured)

    assert metadata["author_sort"] == "Sort"
    assert metadata["publisher"] == "Publisher"
    assert metadata["pubdate"] == "2020-01-01"
    assert metadata["timestamp"] == "2020-01-01T12:00:00"
    assert metadata["description"] == "Description"
    assert metadata["isbn"] == "978-1234567890"


def test_metadata_serializer_add_optional_string_fields_none() -> None:
    """Test _add_optional_string_fields with None values."""
    metadata = {}
    structured = StructuredMetadata(
        id=1,
        title="Test",
        authors=[],
        uuid="test",
    )

    MetadataSerializer._add_optional_string_fields(metadata, structured)

    assert "author_sort" not in metadata
    assert "publisher" not in metadata
    assert "description" not in metadata


def test_metadata_serializer_add_optional_list_fields() -> None:
    """Test _add_optional_list_fields."""
    metadata = {}
    structured = StructuredMetadata(
        id=1,
        title="Test",
        authors=[],
        uuid="test",
        languages=["en"],
        identifiers=[{"type": "isbn", "val": "978-1234567890"}],
        tags=["Fiction"],
        formats=[{"format": "EPUB"}],
    )

    MetadataSerializer._add_optional_list_fields(metadata, structured)

    assert metadata["languages"] == ["en"]
    assert len(metadata["identifiers"]) == 1
    assert metadata["tags"] == ["Fiction"]
    assert len(metadata["formats"]) == 1


def test_metadata_serializer_add_optional_list_fields_empty() -> None:
    """Test _add_optional_list_fields with empty lists."""
    metadata = {}
    structured = StructuredMetadata(
        id=1,
        title="Test",
        authors=[],
        uuid="test",
        languages=[],
        identifiers=[],
        tags=[],
        formats=[],
    )

    MetadataSerializer._add_optional_list_fields(metadata, structured)

    assert "languages" not in metadata
    assert "identifiers" not in metadata
    assert "tags" not in metadata
    assert "formats" not in metadata


def test_metadata_serializer_add_series_fields() -> None:
    """Test _add_series_fields."""
    metadata = {}
    structured = StructuredMetadata(
        id=1,
        title="Test",
        authors=[],
        uuid="test",
        series="Test Series",
        series_index=1.5,
    )

    MetadataSerializer._add_series_fields(metadata, structured)

    assert metadata["series"] == "Test Series"
    assert metadata["series_index"] == 1.5


def test_metadata_serializer_add_series_fields_no_series() -> None:
    """Test _add_series_fields without series."""
    metadata = {}
    structured = StructuredMetadata(
        id=1,
        title="Test",
        authors=[],
        uuid="test",
        series=None,
        series_index=1.5,
    )

    MetadataSerializer._add_series_fields(metadata, structured)

    assert "series" not in metadata
    assert "series_index" not in metadata


def test_metadata_serializer_add_optional_numeric_fields() -> None:
    """Test _add_optional_numeric_fields."""
    metadata = {}
    structured = StructuredMetadata(
        id=1,
        title="Test",
        authors=[],
        uuid="test",
        rating=4,
    )

    MetadataSerializer._add_optional_numeric_fields(metadata, structured)

    assert metadata["rating"] == 4


def test_metadata_serializer_add_optional_numeric_fields_none() -> None:
    """Test _add_optional_numeric_fields with None rating."""
    metadata = {}
    structured = StructuredMetadata(
        id=1,
        title="Test",
        authors=[],
        uuid="test",
        rating=None,
    )

    MetadataSerializer._add_optional_numeric_fields(metadata, structured)

    assert "rating" not in metadata
