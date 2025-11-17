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

"""Tests for metadata export service to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from fundamental.models.core import Book
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.metadata_export_service import MetadataExportService


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


def test_init_default_services() -> None:
    """Test __init__ with default services."""
    service = MetadataExportService()
    assert len(service._exporters) == 3
    from fundamental.services.metadata_exporters.opf_exporter import OpfExporter

    assert isinstance(service._exporters[0], OpfExporter)
    assert service._exporters[0]._opf_service is not None


def test_init_custom_opf_service() -> None:
    """Test __init__ with custom OPF service."""
    mock_opf_service = MagicMock()
    service = MetadataExportService(opf_service=mock_opf_service)
    from fundamental.services.metadata_exporters.opf_exporter import OpfExporter

    assert isinstance(service._exporters[0], OpfExporter)
    assert service._exporters[0]._opf_service == mock_opf_service


def test_init_custom_exporters() -> None:
    """Test __init__ with custom exporters."""
    mock_exporter1 = MagicMock()
    mock_exporter2 = MagicMock()
    service = MetadataExportService(exporters=[mock_exporter1, mock_exporter2])

    assert len(service._exporters) == 2
    assert service._exporters[0] == mock_exporter1
    assert service._exporters[1] == mock_exporter2


def test_export_metadata_opf(book_with_rels: BookWithFullRelations) -> None:
    """Test export_metadata with OPF format."""
    service = MetadataExportService()
    result = service.export_metadata(book_with_rels, "opf")

    assert result.media_type == "application/oebps-package+xml"
    assert result.filename.endswith(".opf")
    assert "Test Book" in result.content


def test_export_metadata_json(book_with_rels: BookWithFullRelations) -> None:
    """Test export_metadata with JSON format."""
    service = MetadataExportService()
    result = service.export_metadata(book_with_rels, "json")

    assert result.media_type == "application/json"
    assert result.filename.endswith(".json")
    assert "Test Book" in result.content


def test_export_metadata_yaml(book_with_rels: BookWithFullRelations) -> None:
    """Test export_metadata with YAML format."""
    service = MetadataExportService()
    result = service.export_metadata(book_with_rels, "yaml")

    assert result.media_type == "text/yaml"
    assert result.filename.endswith(".yaml")
    assert "Test Book" in result.content


def test_export_metadata_default_format(book_with_rels: BookWithFullRelations) -> None:
    """Test export_metadata defaults to OPF format."""
    service = MetadataExportService()
    result = service.export_metadata(book_with_rels)

    assert result.media_type == "application/oebps-package+xml"
    assert result.filename.endswith(".opf")


def test_export_metadata_case_insensitive(
    book_with_rels: BookWithFullRelations,
) -> None:
    """Test export_metadata is case insensitive."""
    service = MetadataExportService()
    result = service.export_metadata(book_with_rels, "OPF")

    assert result.media_type == "application/oebps-package+xml"


def test_export_metadata_unsupported_format(
    book_with_rels: BookWithFullRelations,
) -> None:
    """Test export_metadata with unsupported format."""
    service = MetadataExportService()
    with pytest.raises(ValueError, match="Unsupported format"):
        service.export_metadata(book_with_rels, "xml")


def test_export_metadata_unsupported_format_dynamic_supported(
    book_with_rels: BookWithFullRelations,
) -> None:
    """Test export_metadata shows dynamically determined supported formats."""
    mock_exporter = MagicMock()
    mock_exporter.can_handle.return_value = False
    service = MetadataExportService(exporters=[mock_exporter])

    with pytest.raises(ValueError, match="Unsupported format: xml"):
        service.export_metadata(book_with_rels, "xml")


def test_export_metadata_uses_custom_exporter(
    book_with_rels: BookWithFullRelations,
) -> None:
    """Test export_metadata uses custom exporter."""
    mock_exporter = MagicMock()
    mock_exporter.can_handle.return_value = True
    mock_result = MagicMock()
    mock_exporter.export.return_value = mock_result

    service = MetadataExportService(exporters=[mock_exporter])
    result = service.export_metadata(book_with_rels, "custom")

    mock_exporter.can_handle.assert_called_once_with("custom")
    mock_exporter.export.assert_called_once_with(book_with_rels)
    assert result == mock_result
