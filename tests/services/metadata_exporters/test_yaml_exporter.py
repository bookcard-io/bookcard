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

"""Tests for YAML exporter to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from fundamental.models.core import Book
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.metadata_exporters.yaml_exporter import YamlExporter


@pytest.fixture
def yaml_exporter() -> YamlExporter:
    """Create YAML exporter instance."""
    return YamlExporter()


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


def test_can_handle_yaml(yaml_exporter: YamlExporter) -> None:
    """Test can_handle returns True for yaml format."""
    assert yaml_exporter.can_handle("yaml") is True
    assert yaml_exporter.can_handle("YAML") is True
    assert yaml_exporter.can_handle("Yaml") is True


def test_can_handle_other_formats(yaml_exporter: YamlExporter) -> None:
    """Test can_handle returns False for other formats."""
    assert yaml_exporter.can_handle("json") is False
    assert yaml_exporter.can_handle("opf") is False
    assert yaml_exporter.can_handle("yml") is False


def test_export_full_metadata(
    yaml_exporter: YamlExporter, book_with_rels: BookWithFullRelations
) -> None:
    """Test export with full metadata."""
    result = yaml_exporter.export(book_with_rels)

    assert result.media_type == "text/yaml"
    assert result.filename.endswith(".yaml")
    assert "Test Book" in result.content
    assert "Author One" in result.content
    assert "Test Series" in result.content
    assert "978-1234567890" in result.content


def test_export_minimal_metadata(yaml_exporter: YamlExporter) -> None:
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

    result = yaml_exporter.export(book_with_rels)

    assert result.media_type == "text/yaml"
    assert result.filename.endswith(".yaml")
    assert "Minimal Book" in result.content


def test_export_pyyaml_not_installed(
    yaml_exporter: YamlExporter, book_with_rels: BookWithFullRelations
) -> None:
    """Test export raises error when PyYAML is not installed."""
    with (
        patch("fundamental.services.metadata_exporters.yaml_exporter.yaml", None),
        pytest.raises(ValueError, match="YAML export requires PyYAML"),
    ):
        yaml_exporter.export(book_with_rels)
