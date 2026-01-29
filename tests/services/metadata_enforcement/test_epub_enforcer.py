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

"""Tests for EPUB enforcer to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.epub_fixer.core.epub import EPUBContents
from bookcard.services.metadata_enforcement.epub_enforcer import (
    EpubMetadataEnforcer,
)
from bookcard.services.opf_service import OpfMetadataResult, OpfService


@pytest.fixture
def book() -> Book:
    """Create a test book."""
    from datetime import UTC, datetime

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
    """Create a test book with relations."""
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


@pytest.fixture
def opf_service() -> MagicMock:
    """Create a mock OPF service."""
    mock_service = MagicMock(spec=OpfService)
    mock_service.generate_opf.return_value = OpfMetadataResult(
        xml_content='<?xml version="1.0"?><package version="3.0"><metadata></metadata></package>',
        filename="metadata.opf",
    )
    return mock_service


def test_init_default_opf_service() -> None:
    """Test initialization with default OPF service."""
    enforcer = EpubMetadataEnforcer()
    assert enforcer._opf_service is not None
    assert enforcer._reader is not None
    assert enforcer._writer is not None
    assert enforcer._opf_locator is not None
    assert enforcer._cover_embedder is not None


def test_init_custom_opf_service(opf_service: MagicMock) -> None:
    """Test initialization with custom OPF service."""
    enforcer = EpubMetadataEnforcer(opf_service=opf_service)
    assert enforcer._opf_service == opf_service


def test_enforce_metadata_no_book_id(book_with_rels: BookWithFullRelations) -> None:
    """Test enforce_metadata when book ID is None."""
    book_with_rels.book.id = None
    enforcer = EpubMetadataEnforcer()
    result = enforcer.enforce_metadata(book_with_rels, Path("/test/book.epub"))
    assert result is False


def test_enforce_metadata_success(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata with successful update."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    existing_opf = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:title>Old Title</dc:title>
        </metadata>
        <manifest></manifest>
        <spine></spine>
    </package>"""

    new_opf = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:title>New Title</dc:title>
        </metadata>
    </package>"""

    opf_service.generate_opf.return_value = OpfMetadataResult(
        xml_content=new_opf, filename="metadata.opf"
    )

    mock_contents = EPUBContents()
    mock_contents.files = {"OEBPS/content.opf": existing_opf}

    enforcer = EpubMetadataEnforcer(opf_service=opf_service)
    with (
        patch.object(enforcer, "_reader") as mock_reader,
        patch.object(enforcer, "_writer") as mock_writer,
        patch.object(enforcer, "_opf_locator") as mock_locator,
        patch.object(enforcer, "_cover_embedder") as mock_embedder,
    ):
        mock_reader.read.return_value = mock_contents
        mock_locator.find_opf_path.return_value = "OEBPS/content.opf"

        result = enforcer.enforce_metadata(book_with_rels, epub_file)

        assert result is True
        mock_writer.write.assert_called_once()
        # Verify update_opf_content logic worked
        assert "New Title" in mock_contents.files["OEBPS/content.opf"]
        # Cover embedder should NOT be called as no cover exists in tmp_path
        mock_embedder.embed_cover.assert_not_called()


def test_enforce_metadata_with_cover(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata with cover embedding."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    # Create cover file in book directory
    cover_file = tmp_path / "cover.jpg"
    cover_file.write_bytes(b"image data")

    existing_opf = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata></metadata>
        <manifest></manifest>
    </package>"""

    new_opf = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <metadata></metadata>
    </package>"""

    opf_service.generate_opf.return_value = OpfMetadataResult(
        xml_content=new_opf, filename="metadata.opf"
    )

    mock_contents = EPUBContents()
    mock_contents.files = {"OEBPS/content.opf": existing_opf}

    enforcer = EpubMetadataEnforcer(opf_service=opf_service)
    with (
        patch.object(enforcer, "_reader") as mock_reader,
        patch.object(enforcer, "_writer") as mock_writer,
        patch.object(enforcer, "_opf_locator") as mock_locator,
        patch.object(enforcer, "_cover_embedder") as mock_embedder,
    ):
        mock_reader.read.return_value = mock_contents
        mock_locator.find_opf_path.return_value = "OEBPS/content.opf"

        result = enforcer.enforce_metadata(book_with_rels, epub_file)

        assert result is True
        mock_writer.write.assert_called_once()
        mock_embedder.embed_cover.assert_called_once_with(
            mock_contents, cover_file, opf_path="OEBPS/content.opf"
        )


def test_enforce_metadata_no_opf_found(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata when OPF file not found."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    mock_contents = EPUBContents()
    mock_contents.files = {}

    enforcer = EpubMetadataEnforcer(opf_service=opf_service)
    with (
        patch.object(enforcer, "_reader") as mock_reader,
        patch.object(enforcer, "_opf_locator") as mock_locator,
    ):
        mock_reader.read.return_value = mock_contents
        mock_locator.find_opf_path.return_value = None

        result = enforcer.enforce_metadata(book_with_rels, epub_file)
        assert result is False


def test_enforce_metadata_update_opf_failure(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata when OPF update fails."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    mock_contents = EPUBContents()
    # Missing OPF content in files
    mock_contents.files = {}

    enforcer = EpubMetadataEnforcer(opf_service=opf_service)
    with (
        patch.object(enforcer, "_reader") as mock_reader,
        patch.object(enforcer, "_opf_locator") as mock_locator,
    ):
        mock_reader.read.return_value = mock_contents
        mock_locator.find_opf_path.return_value = "OEBPS/content.opf"

        result = enforcer.enforce_metadata(book_with_rels, epub_file)
        assert result is False


def test_enforce_metadata_exception(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata with exception."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    enforcer = EpubMetadataEnforcer(opf_service=opf_service)
    with patch.object(enforcer, "_reader", side_effect=Exception("Read error")):
        result = enforcer.enforce_metadata(book_with_rels, epub_file)
        assert result is False
