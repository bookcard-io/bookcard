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

"""Tests for JSON exporter to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from fundamental.models.core import Book
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.metadata_exporters.json_exporter import JsonExporter


@pytest.fixture
def json_exporter() -> JsonExporter:
    """Create JSON exporter instance."""
    return JsonExporter()


@pytest.fixture
def book_with_rels() -> BookWithFullRelations:
    """Create test book with relations."""
    book = Book(
        id=1,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
        uuid="test-uuid-123",
        has_cover=False,
        path="Author Name/Test Book (1)",
    )
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


def test_can_handle_json(json_exporter: JsonExporter) -> None:
    """Test can_handle returns True for json format."""
    assert json_exporter.can_handle("json") is True
    assert json_exporter.can_handle("JSON") is True
    assert json_exporter.can_handle("Json") is True


def test_can_handle_other_formats(json_exporter: JsonExporter) -> None:
    """Test can_handle returns False for other formats."""
    assert json_exporter.can_handle("yaml") is False
    assert json_exporter.can_handle("opf") is False
    assert json_exporter.can_handle("xml") is False


def test_export_full_metadata(
    json_exporter: JsonExporter, book_with_rels: BookWithFullRelations
) -> None:
    """Test export with full metadata."""
    result = json_exporter.export(book_with_rels)

    assert result.media_type == "application/json"
    assert result.filename.endswith(".json")
    assert "Test Book" in result.content
    assert "Author One" in result.content
    assert "Test Series" in result.content
    assert "978-1234567890" in result.content


def test_export_minimal_metadata(json_exporter: JsonExporter) -> None:
    """Test export with minimal metadata."""
    book = Book(
        id=1,
        title="Minimal Book",
        timestamp=datetime.now(UTC),
        pubdate=None,
        uuid="test-uuid",
        has_cover=False,
        path="Minimal Book (1)",
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

    result = json_exporter.export(book_with_rels)

    assert result.media_type == "application/json"
    assert result.filename.endswith(".json")
    assert "Minimal Book" in result.content
