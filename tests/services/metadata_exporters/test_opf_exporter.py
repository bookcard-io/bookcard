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

"""Tests for OPF exporter to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from fundamental.models.core import Book
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.metadata_exporters.opf_exporter import OpfExporter
from fundamental.services.opf_service import OpfService


@pytest.fixture
def opf_exporter() -> OpfExporter:
    """Create OPF exporter instance."""
    return OpfExporter()


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


def test_init_default_opf_service() -> None:
    """Test __init__ with default OPF service."""
    exporter = OpfExporter()
    assert exporter._opf_service is not None
    assert isinstance(exporter._opf_service, OpfService)


def test_init_custom_opf_service() -> None:
    """Test __init__ with custom OPF service."""
    mock_opf_service = MagicMock()
    exporter = OpfExporter(opf_service=mock_opf_service)
    assert exporter._opf_service == mock_opf_service


def test_can_handle_opf(opf_exporter: OpfExporter) -> None:
    """Test can_handle returns True for opf format."""
    assert opf_exporter.can_handle("opf") is True
    assert opf_exporter.can_handle("OPF") is True
    assert opf_exporter.can_handle("Opf") is True


def test_can_handle_other_formats(opf_exporter: OpfExporter) -> None:
    """Test can_handle returns False for other formats."""
    assert opf_exporter.can_handle("json") is False
    assert opf_exporter.can_handle("yaml") is False
    assert opf_exporter.can_handle("xml") is False


def test_export(
    opf_exporter: OpfExporter, book_with_rels: BookWithFullRelations
) -> None:
    """Test export."""
    result = opf_exporter.export(book_with_rels)

    assert result.media_type == "application/oebps-package+xml"
    assert result.filename.endswith(".opf")
    assert "Test Book" in result.content
    assert "test-uuid-123" in result.content
