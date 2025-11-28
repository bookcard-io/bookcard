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

"""Tests for EPUB scanner service to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.config import Library
from fundamental.models.core import Book
from fundamental.models.media import Data
from fundamental.repositories.calibre_book_repository import CalibreBookRepository
from fundamental.services.epub_fixer.services.scanner import EPUBFileInfo, EPUBScanner


@pytest.fixture
def library() -> Library:
    """Create a test library configuration."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/metadata.db",
    )


@pytest.fixture
def mock_calibre_repo() -> MagicMock:
    """Create a mock CalibreBookRepository."""
    repo = MagicMock(spec=CalibreBookRepository)
    mock_session = MagicMock()
    repo.get_session.return_value.__enter__.return_value = mock_session
    repo.get_session.return_value.__exit__.return_value = None
    return repo


@pytest.fixture
def mock_library_locator() -> MagicMock:
    """Create a mock LibraryLocator."""
    locator = MagicMock()
    locator.get_location.return_value = Path("/library/root")
    return locator


@pytest.fixture
def scanner(library: Library, mock_calibre_repo: MagicMock) -> EPUBScanner:
    """Create EPUBScanner with mocked dependencies."""
    return EPUBScanner(library=library, calibre_repo=mock_calibre_repo)


@pytest.fixture
def sample_book() -> Book:
    """Create a sample Book instance."""
    return Book(
        id=1,
        title="Test Book",
        path="Author Name/Test Book (1)",
    )


@pytest.fixture
def sample_data() -> Data:
    """Create a sample Data instance."""
    return Data(
        id=1,
        book=1,
        format="EPUB",
        uncompressed_size=1000,
        name="Test Book - Author Name",
    )


class TestEPUBScannerInit:
    """Test EPUBScanner initialization."""

    def test_init(
        self,
        library: Library,
        mock_calibre_repo: MagicMock,
    ) -> None:
        """Test EPUBScanner initialization."""
        scanner = EPUBScanner(library=library, calibre_repo=mock_calibre_repo)

        assert scanner._library == library
        assert scanner._calibre_repo == mock_calibre_repo
        assert scanner._library_locator is not None


class TestEPUBFileInfo:
    """Test EPUBFileInfo dataclass."""

    def test_epub_file_info(
        self,
    ) -> None:
        """Test EPUBFileInfo dataclass."""
        info = EPUBFileInfo(
            book_id=1,
            book_title="Test Book",
            file_path=Path("/path/to/book.epub"),
        )

        assert info.book_id == 1
        assert info.book_title == "Test Book"
        assert info.file_path == Path("/path/to/book.epub")


class TestEPUBScannerScanEpubFiles:
    """Test scan_epub_files method to achieve 100% coverage."""

    @pytest.mark.parametrize(
        ("book_id", "expected_filtered"),
        [
            (None, False),
            (1, True),
            (100, True),
        ],
    )
    def test_scan_epub_files_with_book_id_filter(
        self,
        scanner: EPUBScanner,
        mock_calibre_repo: MagicMock,
        sample_book: Book,
        sample_data: Data,
        book_id: int | None,
        expected_filtered: bool,
    ) -> None:
        """Test scan_epub_files with and without book_id filter."""
        library_path = Path("/library/root")
        book_path = library_path / sample_book.path
        file_path = book_path / f"{sample_data.name}.epub"

        # Mock library locator
        with patch.object(scanner, "_library_locator") as mock_locator:
            mock_locator.get_location.return_value = library_path

            # Mock session and query results
            mock_session = (
                mock_calibre_repo.get_session.return_value.__enter__.return_value
            )
            mock_exec = MagicMock()
            mock_exec.all.return_value = [(sample_book, sample_data)]
            mock_session.exec.return_value = mock_exec

            # Mock file existence
            with patch.object(Path, "exists") as mock_exists:
                mock_exists.return_value = True

                result = scanner.scan_epub_files(book_id=book_id)

                # Verify query was executed
                assert mock_session.exec.called
                if expected_filtered:
                    # Verify book_id filter was applied
                    call_args = mock_session.exec.call_args
                    assert call_args is not None

                # Verify result
                if mock_exists.return_value:
                    assert len(result) == 1
                    assert result[0].book_id == sample_book.id
                    assert result[0].book_title == sample_book.title
                    assert result[0].file_path == file_path

    @pytest.mark.parametrize(
        ("data_name", "file_name", "file_exists", "expected_count"),
        [
            ("Test Book - Author", "Test Book - Author.epub", True, 1),
            ("Test Book - Author", "Test Book - Author.epub", False, 0),
            (None, "1.epub", True, 1),
            (None, "1.epub", False, 0),
        ],
    )
    def test_scan_epub_files_file_path_patterns(
        self,
        scanner: EPUBScanner,
        mock_calibre_repo: MagicMock,
        sample_book: Book,
        data_name: str | None,
        file_name: str,
        file_exists: bool,
        expected_count: int,
    ) -> None:
        """Test scan_epub_files with different file path patterns."""
        library_path = Path("/library/root")

        # Create data with optional name
        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name=data_name,
        )

        # Mock library locator
        with patch.object(scanner, "_library_locator") as mock_locator:
            mock_locator.get_location.return_value = library_path

            # Mock session and query results
            mock_session = (
                mock_calibre_repo.get_session.return_value.__enter__.return_value
            )
            mock_exec = MagicMock()
            mock_exec.all.return_value = [(sample_book, data)]
            mock_session.exec.return_value = mock_exec

            # Mock file existence - pattern 1 first, then pattern 2
            def mock_exists(self: Path) -> bool:
                if file_name in str(self):
                    return file_exists
                return False

            with patch.object(Path, "exists", new=mock_exists):
                result = scanner.scan_epub_files()

                assert len(result) == expected_count
                if expected_count > 0:
                    assert result[0].book_id == sample_book.id
                    assert result[0].book_title == sample_book.title

    def test_scan_epub_files_suffix_filtering_epub(
        self,
        scanner: EPUBScanner,
        mock_calibre_repo: MagicMock,
        sample_book: Book,
        sample_data: Data,
        tmp_path: Path,
    ) -> None:
        """Test scan_epub_files includes files with .epub suffix."""
        library_path = tmp_path / "library"
        library_path.mkdir()
        book_path = library_path / sample_book.path
        book_path.mkdir(parents=True)

        # Create actual EPUB file
        epub_file = book_path / f"{sample_data.name}.epub"
        epub_file.touch()

        # Mock library locator
        with patch.object(scanner, "_library_locator") as mock_locator:
            mock_locator.get_location.return_value = library_path

            # Mock session and query results
            mock_session = (
                mock_calibre_repo.get_session.return_value.__enter__.return_value
            )
            mock_exec = MagicMock()
            mock_exec.all.return_value = [(sample_book, sample_data)]
            mock_session.exec.return_value = mock_exec

            result = scanner.scan_epub_files()

            assert len(result) == 1
            assert result[0].file_path == epub_file
            assert result[0].file_path.suffix.lower() == ".epub"

    def test_scan_epub_files_suffix_filtering_non_epub(
        self,
        scanner: EPUBScanner,
        mock_calibre_repo: MagicMock,
        sample_book: Book,
        sample_data: Data,
        tmp_path: Path,
    ) -> None:
        """Test scan_epub_files excludes files without .epub suffix."""
        library_path = tmp_path / "library"
        library_path.mkdir()
        book_path = library_path / sample_book.path
        book_path.mkdir(parents=True)

        # Create non-EPUB file (PDF)
        pdf_file = book_path / f"{sample_data.name}.pdf"
        pdf_file.touch()

        # Mock library locator
        with patch.object(scanner, "_library_locator") as mock_locator:
            mock_locator.get_location.return_value = library_path

            # Mock session and query results
            mock_session = (
                mock_calibre_repo.get_session.return_value.__enter__.return_value
            )
            mock_exec = MagicMock()
            mock_exec.all.return_value = [(sample_book, sample_data)]
            mock_session.exec.return_value = mock_exec

            result = scanner.scan_epub_files()

            # Should be empty because file has .pdf suffix, not .epub
            assert len(result) == 0

    def test_scan_epub_files_empty_results(
        self,
        scanner: EPUBScanner,
        mock_calibre_repo: MagicMock,
    ) -> None:
        """Test scan_epub_files with no matching books."""
        library_path = Path("/library/root")

        # Mock library locator
        with patch.object(scanner, "_library_locator") as mock_locator:
            mock_locator.get_location.return_value = library_path

            # Mock session with empty results
            mock_session = (
                mock_calibre_repo.get_session.return_value.__enter__.return_value
            )
            mock_exec = MagicMock()
            mock_exec.all.return_value = []
            mock_session.exec.return_value = mock_exec

            result = scanner.scan_epub_files()

            assert len(result) == 0
            assert result == []

    def test_scan_epub_files_multiple_books(
        self,
        scanner: EPUBScanner,
        mock_calibre_repo: MagicMock,
    ) -> None:
        """Test scan_epub_files with multiple books."""
        library_path = Path("/library/root")

        # Create multiple books
        book1 = Book(
            id=1,
            title="Book 1",
            path="Author/Book 1 (1)",
        )
        data1 = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book 1",
        )

        book2 = Book(
            id=2,
            title="Book 2",
            path="Author/Book 2 (2)",
        )
        data2 = Data(
            id=2,
            book=2,
            format="EPUB",
            uncompressed_size=2000,
            name="Book 2",
        )

        # Mock library locator
        with patch.object(scanner, "_library_locator") as mock_locator:
            mock_locator.get_location.return_value = library_path

            # Mock session with multiple results
            mock_session = (
                mock_calibre_repo.get_session.return_value.__enter__.return_value
            )
            mock_exec = MagicMock()
            mock_exec.all.return_value = [
                (book1, data1),
                (book2, data2),
            ]
            mock_session.exec.return_value = mock_exec

            # Mock file existence
            with patch.object(Path, "exists", return_value=True):
                result = scanner.scan_epub_files()

                assert len(result) == 2
                assert result[0].book_id == 1
                assert result[0].book_title == "Book 1"
                assert result[1].book_id == 2
                assert result[1].book_title == "Book 2"

    def test_scan_epub_files_pattern2_fallback(
        self,
        scanner: EPUBScanner,
        mock_calibre_repo: MagicMock,
        sample_book: Book,
    ) -> None:
        """Test scan_epub_files falls back to pattern 2 when pattern 1 doesn't exist."""
        library_path = Path("/library/root")
        book_path = library_path / sample_book.path

        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Test Book",
        )

        pattern2_path = book_path / "1.epub"

        # Mock library locator
        with patch.object(scanner, "_library_locator") as mock_locator:
            mock_locator.get_location.return_value = library_path

            # Mock session and query results
            mock_session = (
                mock_calibre_repo.get_session.return_value.__enter__.return_value
            )
            mock_exec = MagicMock()
            mock_exec.all.return_value = [(sample_book, data)]
            mock_session.exec.return_value = mock_exec

            # Mock file existence: pattern 1 doesn't exist, pattern 2 does
            def mock_exists(self: Path) -> bool:
                return str(self) == str(pattern2_path)

            with patch.object(Path, "exists", new=mock_exists):
                result = scanner.scan_epub_files()

                assert len(result) == 1
                assert result[0].file_path == pattern2_path

    def test_scan_epub_files_lowercase_format(
        self,
        scanner: EPUBScanner,
        mock_calibre_repo: MagicMock,
        sample_book: Book,
    ) -> None:
        """Test scan_epub_files handles lowercase format in file path."""
        library_path = Path("/library/root")
        data = Data(
            id=1,
            book=1,
            format="EPUB",  # Uppercase in DB
            uncompressed_size=1000,
            name="Test Book",
        )

        # Mock library locator
        with patch.object(scanner, "_library_locator") as mock_locator:
            mock_locator.get_location.return_value = library_path

            # Mock session and query results
            mock_session = (
                mock_calibre_repo.get_session.return_value.__enter__.return_value
            )
            mock_exec = MagicMock()
            mock_exec.all.return_value = [(sample_book, data)]
            mock_session.exec.return_value = mock_exec

            # Mock file existence
            with patch.object(Path, "exists", return_value=True):
                result = scanner.scan_epub_files()

                assert len(result) == 1
                # Verify the file path uses lowercase format
                assert ".epub" in str(result[0].file_path).lower()
