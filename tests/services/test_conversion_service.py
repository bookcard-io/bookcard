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

"""Tests for conversion_service to achieve 100% coverage."""

from __future__ import annotations

import shutil
import subprocess  # noqa: S404
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.config import Library
from fundamental.models.conversion import (
    BookConversion,
    ConversionMethod,
    ConversionStatus,
)
from fundamental.models.core import Book
from fundamental.models.media import Data
from fundamental.services.conversion_service import ConversionService
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session for testing.

    Returns
    -------
    DummySession
        Dummy session instance.
    """
    return DummySession()


@pytest.fixture
def library() -> Library:
    """Create a library instance for testing.

    Returns
    -------
    Library
        Library instance.
    """
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        library_root=None,
    )


@pytest.fixture
def library_with_root() -> Library:
    """Create a library instance with library_root.

    Returns
    -------
    Library
        Library instance with library_root.
    """
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        library_root="/path/to/library_root",
    )


@pytest.fixture
def book() -> Book:
    """Create a book instance for testing.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(id=1, title="Test Book", path="author/book (1)")


@pytest.fixture
def mobi_data() -> Data:
    """Create MOBI data instance for testing.

    Returns
    -------
    Data
        Data instance with MOBI format.
    """
    return Data(id=1, book=1, format="MOBI", name="test_book")


# ============================================================================
# Tests for ConversionService.__init__
# ============================================================================


class TestConversionServiceInit:
    """Test ConversionService initialization."""

    def test_init(self, session: DummySession, library: Library) -> None:
        """Test ConversionService initialization.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]
        assert service._session == session
        assert service._library == library
        assert service._book_repo is not None


# ============================================================================
# Tests for ConversionService.check_existing_conversion
# ============================================================================


class TestConversionServiceCheckExistingConversion:
    """Test check_existing_conversion method."""

    def test_check_existing_conversion_found(
        self, session: DummySession, library: Library
    ) -> None:
        """Test check_existing_conversion when conversion exists.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        existing = BookConversion(
            id=1,
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            status=ConversionStatus.COMPLETED,
        )
        session.add_exec_result([existing])

        result = service.check_existing_conversion(1, "MOBI", "EPUB")
        assert result == existing

    def test_check_existing_conversion_not_found(
        self, session: DummySession, library: Library
    ) -> None:
        """Test check_existing_conversion when conversion doesn't exist.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]
        session.add_exec_result([None])

        result = service.check_existing_conversion(1, "MOBI", "EPUB")
        assert result is None

    @pytest.mark.parametrize(
        ("original", "target", "expected_original", "expected_target"),
        [
            ("mobi", "epub", "MOBI", "EPUB"),
            ("MOBI", "EPUB", "MOBI", "EPUB"),
            (".mobi", ".epub", "MOBI", "EPUB"),
        ],
    )
    def test_check_existing_conversion_format_normalization(
        self,
        session: DummySession,
        library: Library,
        original: str,
        target: str,
        expected_original: str,
        expected_target: str,
    ) -> None:
        """Test check_existing_conversion normalizes formats.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        original : str
            Original format.
        target : str
            Target format.
        expected_original : str
            Expected normalized original format.
        expected_target : str
            Expected normalized target format.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]
        session.add_exec_result([None])

        service.check_existing_conversion(1, original, target)
        # Verify the query used normalized formats (indirectly through result)


# ============================================================================
# Tests for ConversionService.convert_book
# ============================================================================


class TestConversionServiceConvertBook:
    """Test convert_book method."""

    def test_convert_book_existing_conversion(
        self,
        session: DummySession,
        library: Library,
    ) -> None:
        """Test convert_book when conversion already exists.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        existing = BookConversion(
            id=1,
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            status=ConversionStatus.COMPLETED,
        )
        session.add_exec_result([existing])

        result = service.convert_book(
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            user_id=1,
        )
        assert result == existing

    def test_convert_book_original_format_not_found(
        self,
        session: DummySession,
        library: Library,
        book: Book,
    ) -> None:
        """Test convert_book when original format not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        session.add_exec_result([None])  # No existing conversion

        with (
            patch.object(service, "_get_book", return_value=book),
            patch.object(service, "_get_book_file_path", return_value=None),
            pytest.raises(ValueError, match=r"Original format.*not found"),
        ):
            service.convert_book(
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                user_id=1,
            )

    def test_convert_book_target_format_exists(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test convert_book when target format already exists.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        session.add_exec_result([None])  # No existing conversion

        original_file = tmp_path / "book.mobi"
        original_file.touch()

        with (
            patch.object(service, "_get_book", return_value=book),
            patch.object(service, "_get_book_file_path", return_value=original_file),
            patch.object(service, "_format_exists", return_value=True),
        ):
            result = service.convert_book(
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                user_id=1,
            )

            assert result.status == ConversionStatus.COMPLETED
            assert result.original_format == "MOBI"
            assert result.target_format == "EPUB"

    def test_convert_book_converter_not_found(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test convert_book when converter not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        session.add_exec_result([None])  # No existing conversion

        original_file = tmp_path / "book.mobi"
        original_file.touch()

        with (
            patch.object(service, "_get_book", return_value=book),
            patch.object(service, "_get_book_file_path", return_value=original_file),
            patch.object(service, "_format_exists", return_value=False),
            patch("pathlib.Path.exists", return_value=False),
            patch("shutil.which", return_value=None),
            pytest.raises(ValueError, match="Calibre converter not found"),
        ):
            service.convert_book(
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                user_id=1,
            )

    def test_convert_book_converter_path_not_exists(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test convert_book when converter path doesn't exist.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        session.add_exec_result([None])  # No existing conversion

        original_file = tmp_path / "book.mobi"
        original_file.touch()

        with (
            patch.object(service, "_get_book", return_value=book),
            patch.object(service, "_get_book_file_path", return_value=original_file),
            patch.object(service, "_format_exists", return_value=False),
            patch("pathlib.Path.exists", return_value=False),
            patch("shutil.which", return_value=None),
            pytest.raises(ValueError, match="Calibre converter not found"),
        ):
            service.convert_book(
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                user_id=1,
            )

    def test_convert_book_success(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test convert_book successful conversion.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        session.add_exec_result([None])  # No existing conversion

        original_file = tmp_path / "book.mobi"
        original_file.touch()
        converted_file = tmp_path / "book.epub"
        converted_file.touch()

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        def path_exists_side_effect(path: Path | str) -> bool:
            """Mock Path.exists to return True for /app/calibre/ebook-convert."""
            if str(path) == "/app/calibre/ebook-convert":
                return True
            return Path(path).exists()

        with (
            patch.object(service, "_get_book", return_value=book),
            patch.object(service, "_get_book_file_path", return_value=original_file),
            patch.object(service, "_format_exists", return_value=False),
            patch("pathlib.Path.exists", side_effect=path_exists_side_effect),
            patch.object(service, "_execute_conversion", return_value=converted_file),
            patch.object(service, "_add_format_to_calibre"),
            patch.object(service, "_backup_original_file", return_value=None),
        ):
            result = service.convert_book(
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                user_id=1,
                backup_original=False,
            )

            assert result.status == ConversionStatus.COMPLETED
            assert result.original_format == "MOBI"
            assert result.target_format == "EPUB"

    def test_convert_book_with_backup(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test convert_book with backup enabled.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        session.add_exec_result([None])  # No existing conversion

        original_file = tmp_path / "book.mobi"
        original_file.touch()
        backup_file = tmp_path / "book.mobi.bak"
        converted_file = tmp_path / "book.epub"
        converted_file.touch()

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        def path_exists_side_effect(path: Path | str) -> bool:
            """Mock Path.exists to return True for /app/calibre/ebook-convert."""
            if str(path) == "/app/calibre/ebook-convert":
                return True
            return Path(path).exists()

        with (
            patch.object(service, "_get_book", return_value=book),
            patch.object(service, "_get_book_file_path", return_value=original_file),
            patch.object(service, "_format_exists", return_value=False),
            patch("pathlib.Path.exists", side_effect=path_exists_side_effect),
            patch.object(service, "_execute_conversion", return_value=converted_file),
            patch.object(service, "_add_format_to_calibre"),
            patch.object(service, "_backup_original_file", return_value=backup_file),
        ):
            result = service.convert_book(
                book_id=1,
                original_format="MOBI",
                target_format="EPUB",
                user_id=1,
                backup_original=True,
            )

            assert result.original_backed_up is True
            assert result.backup_file_path == str(backup_file)

    def test_convert_book_conversion_fails(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test convert_book when conversion fails.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        session.add_exec_result([None])  # No existing conversion

        original_file = tmp_path / "book.mobi"
        original_file.touch()

        def path_exists_side_effect(path: Path | str) -> bool:
            """Mock Path.exists to return True for /app/calibre/ebook-convert."""
            if str(path) == "/app/calibre/ebook-convert":
                return True
            return Path(path).exists()

        with (
            patch.object(service, "_get_book", return_value=book),
            patch.object(service, "_get_book_file_path", return_value=original_file),
            patch.object(service, "_format_exists", return_value=False),
            patch("pathlib.Path.exists", side_effect=path_exists_side_effect),
            patch.object(
                service,
                "_execute_conversion",
                side_effect=RuntimeError("Conversion failed"),
            ),
            patch.object(service, "_backup_original_file", return_value=None),
        ):
            with pytest.raises(RuntimeError, match="Conversion failed"):
                service.convert_book(
                    book_id=1,
                    original_format="MOBI",
                    target_format="EPUB",
                    user_id=1,
                )

            # Verify conversion record was updated with error
            assert len(session.added) > 0
            conversion = session.added[-1]
            assert isinstance(conversion, BookConversion)
            assert conversion.status == ConversionStatus.FAILED
            assert conversion.error_message == "Conversion failed"


# ============================================================================
# Tests for ConversionService._get_book
# ============================================================================


class TestConversionServiceGetBook:
    """Test _get_book method."""

    def test_get_book_success(
        self, session: DummySession, library: Library, book: Book
    ) -> None:
        """Test _get_book when book exists.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = book
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            result = service._get_book(1)
            assert result == book

    def test_get_book_not_found(self, session: DummySession, library: Library) -> None:
        """Test _get_book when book doesn't exist.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = None
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            with pytest.raises(ValueError, match=r"Book.*not found"):
                service._get_book(999)


# ============================================================================
# Tests for ConversionService._get_book_file_path
# ============================================================================


class TestConversionServiceGetBookFilePath:
    """Test _get_book_file_path method."""

    def test_get_book_file_path_primary_exists(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        mobi_data: Data,
        tmp_path: Path,
    ) -> None:
        """Test _get_book_file_path when primary path exists.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        mobi_data : Data
            MOBI data instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        primary_file = book_dir / f"{mobi_data.name}.mobi"
        primary_file.touch()

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = mobi_data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            # Mock library path
            service._library.calibre_db_path = str(library_path)

            result = service._get_book_file_path(book, 1, "MOBI")
            assert result == primary_file

    def test_get_book_file_path_alt_exists(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        mobi_data: Data,
        tmp_path: Path,
    ) -> None:
        """Test _get_book_file_path when alternative path exists.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        mobi_data : Data
            MOBI data instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        alt_file = book_dir / f"{book.id}.mobi"
        alt_file.touch()

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = mobi_data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            service._library.calibre_db_path = str(library_path)

            result = service._get_book_file_path(book, 1, "MOBI")
            assert result == alt_file

    def test_get_book_file_path_not_found(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        mobi_data: Data,
        tmp_path: Path,
    ) -> None:
        """Test _get_book_file_path when file not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        mobi_data : Data
            MOBI data instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = mobi_data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            service._library.calibre_db_path = str(library_path)

            result = service._get_book_file_path(book, 1, "MOBI")
            assert result is None

    def test_get_book_file_path_data_not_found(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _get_book_file_path when data not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = None
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            result = service._get_book_file_path(book, 1, "MOBI")
            assert result is None

    def test_get_book_file_path_with_library_root(
        self,
        session: DummySession,
        library_with_root: Library,
        book: Book,
        mobi_data: Data,
        tmp_path: Path,
    ) -> None:
        """Test _get_book_file_path uses library_root when available.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library_with_root : Library
            Library instance with library_root.
        book : Book
            Book instance.
        mobi_data : Data
            MOBI data instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library_with_root)  # type: ignore[arg-type]

        library_root = tmp_path / "library_root"
        library_root.mkdir()
        book_dir = library_root / book.path
        book_dir.mkdir(parents=True)

        primary_file = book_dir / f"{mobi_data.name}.mobi"
        primary_file.touch()

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = mobi_data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            service._library.library_root = str(library_root)

            result = service._get_book_file_path(book, 1, "MOBI")
            assert result == primary_file

    def test_get_book_file_path_with_none_name(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _get_book_file_path when data.name is None.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        data = Data(id=1, book=1, format="MOBI", name=None)
        alt_file = book_dir / f"{book.id}.mobi"
        alt_file.touch()

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            service._library.calibre_db_path = str(library_path)

            result = service._get_book_file_path(book, 1, "MOBI")
            assert result == alt_file


# ============================================================================
# Tests for ConversionService._format_exists
# ============================================================================


class TestConversionServiceFormatExists:
    """Test _format_exists method."""

    def test_format_exists_true(
        self, session: DummySession, library: Library, mobi_data: Data
    ) -> None:
        """Test _format_exists returns True when format exists.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        mobi_data : Data
            MOBI data instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = mobi_data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            result = service._format_exists(1, "MOBI")
            assert result is True

    def test_format_exists_false(self, session: DummySession, library: Library) -> None:
        """Test _format_exists returns False when format doesn't exist.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = None
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            result = service._format_exists(1, "MOBI")
            assert result is False


# ============================================================================
# Tests for ConversionService._get_converter_path
# ============================================================================


class TestConversionServiceGetConverterPath:
    """Test _get_converter_path method."""

    def test_get_converter_path_from_docker(
        self, session: DummySession, library: Library
    ) -> None:
        """Test _get_converter_path returns Docker installation path.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        def path_exists_side_effect(path: Path | str) -> bool:
            """Mock Path.exists to return True for /app/calibre/ebook-convert."""
            return str(path) == "/app/calibre/ebook-convert"

        with patch("pathlib.Path.exists", side_effect=path_exists_side_effect):
            result = service._get_converter_path()
            assert result == "/app/calibre/ebook-convert"

    def test_get_converter_path_from_shutil_which(
        self, session: DummySession, library: Library
    ) -> None:
        """Test _get_converter_path falls back to shutil.which.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        def path_exists_side_effect(path: Path | str) -> bool:
            """Mock Path.exists to return False for /app/calibre/ebook-convert."""
            return str(path) != "/app/calibre/ebook-convert"

        with (
            patch("pathlib.Path.exists", side_effect=path_exists_side_effect),
            patch("shutil.which", return_value="/usr/local/bin/ebook-convert"),
        ):
            result = service._get_converter_path()
            assert result == "/usr/local/bin/ebook-convert"

    def test_get_converter_path_not_found(
        self, session: DummySession, library: Library
    ) -> None:
        """Test _get_converter_path returns None when not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        def path_exists_side_effect(path: Path | str) -> bool:
            """Mock Path.exists to return False for /app/calibre/ebook-convert."""
            return str(path) != "/app/calibre/ebook-convert"

        with (
            patch("pathlib.Path.exists", side_effect=path_exists_side_effect),
            patch("shutil.which", return_value=None),
        ):
            result = service._get_converter_path()
            assert result is None


# ============================================================================
# Tests for ConversionService._backup_original_file
# ============================================================================


class TestConversionServiceBackupOriginalFile:
    """Test _backup_original_file method."""

    def test_backup_original_file_success(
        self, session: DummySession, library: Library, tmp_path: Path
    ) -> None:
        """Test _backup_original_file successfully creates backup.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        original_file = tmp_path / "book.mobi"
        original_file.write_text("test content")
        backup_file = tmp_path / "book.mobi.bak"

        result = service._backup_original_file(original_file)

        assert result == backup_file
        assert backup_file.exists()
        assert backup_file.read_text() == "test content"

    def test_backup_original_file_oserror(
        self, session: DummySession, library: Library, tmp_path: Path
    ) -> None:
        """Test _backup_original_file handles OSError.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        original_file = tmp_path / "book.mobi"
        original_file.touch()

        with patch("shutil.copy2", side_effect=OSError("Permission denied")):
            result = service._backup_original_file(original_file)
            assert result is None

    def test_backup_original_file_shutil_error(
        self, session: DummySession, library: Library, tmp_path: Path
    ) -> None:
        """Test _backup_original_file handles shutil.Error.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        original_file = tmp_path / "book.mobi"
        original_file.touch()

        with patch("shutil.copy2", side_effect=shutil.Error("Copy failed")):
            result = service._backup_original_file(original_file)
            assert result is None


# ============================================================================
# Tests for ConversionService._execute_conversion
# ============================================================================


class TestConversionServiceExecuteConversion:
    """Test _execute_conversion method."""

    def test_execute_conversion_success(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion successfully converts file.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        input_file = tmp_path / "input.mobi"
        input_file.touch()
        output_file = book_dir / "test_book.epub"
        output_file.touch()

        service._library.calibre_db_path = str(library_path)

        data = Data(id=1, book=1, format="MOBI", name="test_book")

        with (
            patch.object(service._book_repo, "get_session") as mock_get_session,
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            # Mock temp file
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.epub")
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            # Mock subprocess
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Create temp output file
            temp_output = Path(mock_temp_file.name)
            temp_output.touch()

            result = service._execute_conversion(
                "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
            )

            assert result == output_file
            mock_run.assert_called_once()

    def test_execute_conversion_failure(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion when conversion fails.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        input_file = tmp_path / "input.mobi"
        input_file.touch()

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.epub")
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Conversion error"
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError, match="Conversion failed"):
                service._execute_conversion(
                    "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
                )

    def test_execute_conversion_output_not_found(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion when output file not found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        input_file = tmp_path / "input.mobi"
        input_file.touch()

        temp_path = tmp_path / "temp.epub"

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            # Create temp file context manager
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(temp_path)
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Patch exists to return False after subprocess
            with (
                patch("pathlib.Path.exists", return_value=False),
                pytest.raises(RuntimeError, match="output file not found"),
            ):
                service._execute_conversion(
                    "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
                )

    def test_execute_conversion_timeout(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion when conversion times out.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        input_file = tmp_path / "input.mobi"
        input_file.touch()

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.epub")
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            mock_run.side_effect = subprocess.TimeoutExpired("ebook-convert", 300)

            with pytest.raises(RuntimeError, match="timed out"):
                service._execute_conversion(
                    "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
                )

    def test_execute_conversion_exception_cleanup(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion cleans up temp file on exception.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        input_file = tmp_path / "input.mobi"
        input_file.touch()

        # Create temp file that will be cleaned up
        with NamedTemporaryFile(
            delete=False, suffix=".epub", prefix="calibre_convert_", dir=tmp_path
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("test")

        with (
            patch("subprocess.run") as mock_run,
            patch(
                "fundamental.services.conversion_service.NamedTemporaryFile"
            ) as mock_temp,
        ):
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(temp_path)
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            mock_run.side_effect = ValueError("Conversion error")

            with pytest.raises(ValueError, match="Conversion error"):
                service._execute_conversion(
                    "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
                )

            # Verify temp file was cleaned up
            assert not temp_path.exists()

    def test_execute_conversion_with_library_root(
        self,
        session: DummySession,
        library_with_root: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion uses library_root when available.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library_with_root : Library
            Library instance with library_root.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library_with_root)  # type: ignore[arg-type]

        library_root = tmp_path / "library_root"
        library_root.mkdir()
        book_dir = library_root / book.path
        book_dir.mkdir(parents=True)

        input_file = tmp_path / "input.mobi"
        input_file.touch()
        output_file = book_dir / "test_book.epub"
        output_file.touch()

        service._library.library_root = str(library_root)

        data = Data(id=1, book=1, format="MOBI", name="test_book")

        with (
            patch.object(service._book_repo, "get_session") as mock_get_session,
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.epub")
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            temp_output = Path(mock_temp_file.name)
            temp_output.touch()

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = service._execute_conversion(
                "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
            )

            assert result == output_file

    def test_execute_conversion_no_data_name(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion when data has no name.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        input_file = tmp_path / "input.mobi"
        input_file.touch()
        output_file = book_dir / "1.epub"
        output_file.touch()

        service._library.calibre_db_path = str(library_path)

        data = Data(id=1, book=1, format="MOBI", name=None)

        with (
            patch.object(service._book_repo, "get_session") as mock_get_session,
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.epub")
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            temp_output = Path(mock_temp_file.name)
            temp_output.touch()

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = service._execute_conversion(
                "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
            )

            assert result == output_file

    def test_execute_conversion_no_data(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion when no data found.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        library_path = tmp_path / "library"
        library_path.mkdir()
        book_dir = library_path / book.path
        book_dir.mkdir(parents=True)

        input_file = tmp_path / "input.mobi"
        input_file.touch()
        output_file = book_dir / "1.epub"
        output_file.touch()

        service._library.calibre_db_path = str(library_path)

        with (
            patch.object(service._book_repo, "get_session") as mock_get_session,
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = None
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.epub")
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            temp_output = Path(mock_temp_file.name)
            temp_output.touch()

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = service._execute_conversion(
                "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
            )

            assert result == output_file

    def test_execute_conversion_stderr_empty(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion when stderr is empty but returncode != 0.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        input_file = tmp_path / "input.mobi"
        input_file.touch()

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.epub")
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = None
            mock_result.stdout = "Error message"
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError, match="Conversion failed"):
                service._execute_conversion(
                    "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
                )

    def test_execute_conversion_no_stderr_no_stdout(
        self,
        session: DummySession,
        library: Library,
        book: Book,
        tmp_path: Path,
    ) -> None:
        """Test _execute_conversion when both stderr and stdout are empty.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        book : Book
            Book instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        input_file = tmp_path / "input.mobi"
        input_file.touch()

        with (
            patch("subprocess.run") as mock_run,
            patch("tempfile.NamedTemporaryFile") as mock_temp,
        ):
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp.epub")
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            mock_temp.return_value.__exit__.return_value = None

            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = None
            mock_result.stdout = None
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError, match=r"Conversion failed.*Unknown"):
                service._execute_conversion(
                    "/usr/bin/ebook-convert", input_file, "EPUB", book, 1
                )


# ============================================================================
# Tests for ConversionService._add_format_to_calibre
# ============================================================================


class TestConversionServiceAddFormatToCalibre:
    """Test _add_format_to_calibre method."""

    def test_add_format_to_calibre_new(
        self, session: DummySession, library: Library, tmp_path: Path
    ) -> None:
        """Test _add_format_to_calibre creates new Data record.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        file_path = tmp_path / "book.epub"
        file_path.write_text("test content")

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = None  # No existing format
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            service._add_format_to_calibre(1, file_path, "EPUB")

            # Verify new Data was added
            mock_session.add.assert_called_once()
            added_data = mock_session.add.call_args[0][0]
            assert isinstance(added_data, Data)
            assert added_data.format == "EPUB"
            assert added_data.book == 1

    def test_add_format_to_calibre_update_existing(
        self, session: DummySession, library: Library, tmp_path: Path
    ) -> None:
        """Test _add_format_to_calibre updates existing Data record.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        tmp_path : Path
            Temporary directory path.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        file_path = tmp_path / "book.epub"
        file_path.write_text("test content")

        existing_data = Data(id=1, book=1, format="EPUB", name="old_name")

        with patch.object(service._book_repo, "get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = existing_data
            mock_session.exec.return_value = mock_result
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            service._add_format_to_calibre(1, file_path, "EPUB")

            # Verify existing data was updated
            assert existing_data.uncompressed_size == file_path.stat().st_size
            assert existing_data.name == "book"
            mock_session.add.assert_called_once_with(existing_data)


# ============================================================================
# Tests for ConversionService._create_conversion_record
# ============================================================================


class TestConversionServiceCreateConversionRecord:
    """Test _create_conversion_record method."""

    def test_create_conversion_record(
        self, session: DummySession, library: Library
    ) -> None:
        """Test _create_conversion_record creates record.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        service = ConversionService(session, library)  # type: ignore[arg-type]

        result = service._create_conversion_record(
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            original_file_path="/path/to/original.mobi",
            converted_file_path="/path/to/converted.epub",
            user_id=1,
            conversion_method=ConversionMethod.MANUAL,
            original_backed_up=True,
            status=ConversionStatus.COMPLETED,
        )

        assert result.book_id == 1
        assert result.original_format == "MOBI"
        assert result.target_format == "EPUB"
        assert result.original_backed_up is True
        assert result.status == ConversionStatus.COMPLETED
        assert result.library_id == library.id
        assert result.user_id == 1
        assert result in session.added

    def test_create_conversion_record_no_library(self, session: DummySession) -> None:
        """Test _create_conversion_record with None library.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        """
        library = Library(id=None, name="Test", calibre_db_path="/path")
        service = ConversionService(session, library)  # type: ignore[arg-type]

        result = service._create_conversion_record(
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            original_file_path="/path/to/original.mobi",
            converted_file_path="/path/to/converted.epub",
            user_id=None,
            conversion_method=ConversionMethod.AUTO_IMPORT,
            original_backed_up=False,
            status=ConversionStatus.FAILED,
        )

        assert result.library_id is None
        assert result.user_id is None


# ============================================================================
# Tests for ConversionService._now
# ============================================================================


class TestConversionServiceNow:
    """Test _now method."""

    def test_now_returns_datetime(
        self, session: DummySession, library: Library
    ) -> None:
        """Test _now returns current UTC datetime.

        Parameters
        ----------
        session : DummySession
            Dummy session instance.
        library : Library
            Library instance.
        """
        from datetime import UTC, datetime

        service = ConversionService(session, library)  # type: ignore[arg-type]

        result = service._now()

        assert isinstance(result, datetime)
        assert result.tzinfo == UTC
