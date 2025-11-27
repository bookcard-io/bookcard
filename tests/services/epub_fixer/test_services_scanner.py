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

"""Tests for EPUB scanner service."""

from pathlib import Path

from fundamental.models.config import Library
from fundamental.repositories.calibre_book_repository import CalibreBookRepository
from fundamental.services.epub_fixer.services.scanner import EPUBFileInfo, EPUBScanner


def test_epub_scanner_init() -> None:
    """Test EPUBScanner initialization."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/metadata.db",
    )
    calibre_repo = CalibreBookRepository("/path/to/metadata.db", "metadata.db")

    scanner = EPUBScanner(library, calibre_repo)

    assert scanner._library == library
    assert scanner._calibre_repo == calibre_repo


# Note: Scanner tests require actual database setup with SQLAlchemy queries
# These are better suited for integration tests with a real Calibre database
# The scanner logic is tested indirectly through the EPUBFixerService integration tests


def test_epub_file_info() -> None:
    """Test EPUBFileInfo dataclass."""
    info = EPUBFileInfo(
        book_id=1,
        book_title="Test Book",
        file_path=Path("/path/to/book.epub"),
    )

    assert info.book_id == 1
    assert info.book_title == "Test Book"
    assert info.file_path == Path("/path/to/book.epub")
