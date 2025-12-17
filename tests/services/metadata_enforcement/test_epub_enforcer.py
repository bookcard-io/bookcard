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

import subprocess  # noqa: S404
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

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


def test_enforce_metadata_no_polish(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata when ebook-polish not found."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    with (
        patch.object(EpubMetadataEnforcer, "_get_ebook_polish_path", return_value=None),
        patch.object(
            EpubMetadataEnforcer, "_enforce_metadata_manual", return_value=True
        ) as mock_manual,
    ):
        enforcer = EpubMetadataEnforcer(opf_service=opf_service)
        result = enforcer.enforce_metadata(book_with_rels, epub_file)
        assert result is True
        mock_manual.assert_called_once()


def test_enforce_metadata_polish_success(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata with successful ebook-polish."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")
    book_dir = epub_file.parent
    opf_file = book_dir / "metadata.opf"
    opf_file.write_text("test opf")

    with (
        patch.object(
            EpubMetadataEnforcer,
            "_get_ebook_polish_path",
            return_value="/usr/bin/ebook-polish",
        ),
        patch.object(
            EpubMetadataEnforcer, "_run_ebook_polish_metadata", return_value=True
        ),
    ):
        enforcer = EpubMetadataEnforcer(opf_service=opf_service)
        result = enforcer.enforce_metadata(book_with_rels, epub_file)
        assert result is True


def test_enforce_metadata_polish_failure_fallback(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata with ebook-polish failure falling back to manual."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    with (
        patch.object(
            EpubMetadataEnforcer,
            "_get_ebook_polish_path",
            return_value="/usr/bin/ebook-polish",
        ),
        patch.object(
            EpubMetadataEnforcer,
            "_run_ebook_polish_metadata",
            side_effect=Exception("Error"),
        ),
        patch.object(
            EpubMetadataEnforcer, "_enforce_metadata_manual", return_value=True
        ) as mock_manual,
    ):
        enforcer = EpubMetadataEnforcer(opf_service=opf_service)
        result = enforcer.enforce_metadata(book_with_rels, epub_file)
        assert result is True
        mock_manual.assert_called_once()


def test_enforce_metadata_polish_failure_no_fallback(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test enforce_metadata with ebook-polish failure and no fallback."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    with (
        patch.object(
            EpubMetadataEnforcer,
            "_get_ebook_polish_path",
            return_value="/usr/bin/ebook-polish",
        ),
        patch.object(
            EpubMetadataEnforcer, "_run_ebook_polish_metadata", return_value=False
        ),
    ):
        enforcer = EpubMetadataEnforcer(opf_service=opf_service)
        result = enforcer.enforce_metadata(book_with_rels, epub_file)
        assert result is False


def test_get_ebook_polish_path_docker() -> None:
    """Test _get_ebook_polish_path with Docker path."""
    with patch("pathlib.Path.exists", return_value=True):
        enforcer = EpubMetadataEnforcer()
        result = enforcer._get_ebook_polish_path()
        assert result == "/app/calibre/ebook-polish"


def test_get_ebook_polish_path_system() -> None:
    """Test _get_ebook_polish_path with system path."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        patch("shutil.which", return_value="/usr/bin/ebook-polish"),
    ):
        enforcer = EpubMetadataEnforcer()
        result = enforcer._get_ebook_polish_path()
        assert result == "/usr/bin/ebook-polish"


def test_get_ebook_polish_path_not_found() -> None:
    """Test _get_ebook_polish_path when not found."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        patch("shutil.which", return_value=None),
    ):
        enforcer = EpubMetadataEnforcer()
        result = enforcer._get_ebook_polish_path()
        assert result is None


def test_run_ebook_polish_metadata_success() -> None:
    """Test _run_ebook_polish_metadata with successful execution."""
    polish_path = "/usr/bin/ebook-polish"
    opf_path = Path("/test/metadata.opf")
    ebook_path = Path("/test/book.epub")

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        enforcer = EpubMetadataEnforcer()
        result = enforcer._run_ebook_polish_metadata(polish_path, opf_path, ebook_path)
        assert result is True


def test_run_ebook_polish_metadata_failure() -> None:
    """Test _run_ebook_polish_metadata with failed execution."""
    polish_path = "/usr/bin/ebook-polish"
    opf_path = Path("/test/metadata.opf")
    ebook_path = Path("/test/book.epub")

    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stderr = "Error message"

    with patch("subprocess.run", return_value=mock_result):
        enforcer = EpubMetadataEnforcer()
        result = enforcer._run_ebook_polish_metadata(polish_path, opf_path, ebook_path)
        assert result is False


def test_run_ebook_polish_metadata_timeout() -> None:
    """Test _run_ebook_polish_metadata with timeout."""
    polish_path = "/usr/bin/ebook-polish"
    opf_path = Path("/test/metadata.opf")
    ebook_path = Path("/test/book.epub")

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 300)):
        enforcer = EpubMetadataEnforcer()
        result = enforcer._run_ebook_polish_metadata(polish_path, opf_path, ebook_path)
        assert result is False


def test_run_ebook_polish_metadata_exception() -> None:
    """Test _run_ebook_polish_metadata with exception."""
    polish_path = "/usr/bin/ebook-polish"
    opf_path = Path("/test/metadata.opf")
    ebook_path = Path("/test/book.epub")

    with patch("subprocess.run", side_effect=Exception("Unexpected error")):
        enforcer = EpubMetadataEnforcer()
        result = enforcer._run_ebook_polish_metadata(polish_path, opf_path, ebook_path)
        assert result is False


def test_enforce_metadata_manual_no_opf(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test _enforce_metadata_manual when OPF not found."""
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

        result = enforcer._enforce_metadata_manual(book_with_rels, epub_file)
        assert result is False


def test_enforce_metadata_manual_opf_not_in_contents(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test _enforce_metadata_manual when OPF not in contents."""
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
        mock_locator.find_opf_path.return_value = "OEBPS/content.opf"

        result = enforcer._enforce_metadata_manual(book_with_rels, epub_file)
        assert result is False


def test_enforce_metadata_manual_success(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test _enforce_metadata_manual with successful update."""
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
    ):
        mock_reader.read.return_value = mock_contents
        mock_locator.find_opf_path.return_value = "OEBPS/content.opf"

        result = enforcer._enforce_metadata_manual(book_with_rels, epub_file)
        assert result is True
        mock_writer.write.assert_called_once()


def test_enforce_metadata_manual_no_metadata_elements(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test _enforce_metadata_manual when metadata elements not found."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    existing_opf = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
        <manifest></manifest>
        <spine></spine>
    </package>"""

    new_opf = """<?xml version="1.0"?>
    <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
    </package>"""

    opf_service.generate_opf.return_value = OpfMetadataResult(
        xml_content=new_opf, filename="metadata.opf"
    )

    mock_contents = EPUBContents()
    mock_contents.files = {"OEBPS/content.opf": existing_opf}

    enforcer = EpubMetadataEnforcer(opf_service=opf_service)
    with (
        patch.object(enforcer, "_reader") as mock_reader,
        patch.object(enforcer, "_opf_locator") as mock_locator,
    ):
        mock_reader.read.return_value = mock_contents
        mock_locator.find_opf_path.return_value = "OEBPS/content.opf"

        result = enforcer._enforce_metadata_manual(book_with_rels, epub_file)
        assert result is False


def test_enforce_metadata_manual_exception(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test _enforce_metadata_manual with exception."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")

    enforcer = EpubMetadataEnforcer(opf_service=opf_service)
    with patch.object(enforcer, "_reader", side_effect=Exception("Read error")):
        result = enforcer._enforce_metadata_manual(book_with_rels, epub_file)
        assert result is False


def test_enforce_metadata_creates_opf_file(
    book_with_rels: BookWithFullRelations, opf_service: MagicMock, tmp_path: Path
) -> None:
    """Test that enforce_metadata creates OPF file if it doesn't exist."""
    epub_file = tmp_path / "book.epub"
    epub_file.write_text("test")
    book_dir = epub_file.parent

    with (
        patch.object(
            EpubMetadataEnforcer,
            "_get_ebook_polish_path",
            return_value="/usr/bin/ebook-polish",
        ),
        patch.object(
            EpubMetadataEnforcer, "_run_ebook_polish_metadata", return_value=True
        ),
    ):
        enforcer = EpubMetadataEnforcer(opf_service=opf_service)
        result = enforcer.enforce_metadata(book_with_rels, epub_file)
        assert result is True
        opf_file = book_dir / "metadata.opf"
        assert opf_file.exists()
