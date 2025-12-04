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

"""Tests for ConversionService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from fundamental.api.schemas.conversion import ConversionRequest
from fundamental.models.config import Library
from fundamental.models.conversion import (
    BookConversion,
    ConversionMethod,
    ConversionStatus,
)
from fundamental.models.core import Book
from fundamental.models.media import Data
from fundamental.services.conversion.backup import FileBackupService
from fundamental.services.conversion.book_repository import BookRepository
from fundamental.services.conversion.exceptions import (
    BookNotFoundError,
    FormatNotFoundError,
)
from fundamental.services.conversion.repository import ConversionRepository
from fundamental.services.conversion.service import ConversionService

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def mock_book_repository() -> MagicMock:
    """Create a mock BookRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    return MagicMock(spec=BookRepository)


@pytest.fixture
def mock_conversion_repository(session: DummySession) -> ConversionRepository:  # type: ignore[valid-type]
    """Create a ConversionRepository instance.

    Parameters
    ----------
    session : DummySession
        Session fixture.

    Returns
    -------
    ConversionRepository
        Repository instance.
    """
    return ConversionRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def mock_conversion_strategy() -> MagicMock:
    """Create a mock ConversionStrategy.

    Returns
    -------
    MagicMock
        Mock strategy instance.
    """
    return MagicMock()


@pytest.fixture
def conversion_service(
    session: DummySession,  # type: ignore[valid-type]
    mock_book_repository: MagicMock,
    mock_conversion_repository: ConversionRepository,
    mock_conversion_strategy: MagicMock,
    temp_dir: Path,
) -> ConversionService:
    """Create ConversionService instance.

    Parameters
    ----------
    session : DummySession
        Session fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    mock_conversion_repository : ConversionRepository
        Conversion repository fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    temp_dir : Path
        Temporary directory fixture.

    Returns
    -------
    ConversionService
        Service instance.
    """
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path=str(temp_dir / "metadata.db"),
        library_root=str(temp_dir),
    )
    return ConversionService(
        session=session,  # type: ignore[arg-type]
        library=library,
        book_repository=mock_book_repository,
        conversion_repository=mock_conversion_repository,
        conversion_strategy=mock_conversion_strategy,
    )


@pytest.fixture
def book() -> Book:
    """Create a test book.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(
        id=1,
        title="Test Book",
        path="Author Name/Test Book (1)",
        timestamp=1234567890,
    )


@pytest.fixture
def format_data() -> Data:
    """Create test format data.

    Returns
    -------
    Data
        Data instance.
    """
    return Data(
        id=1,
        book=1,
        format="EPUB",
        uncompressed_size=1024,
        name="Test Book",
    )


@pytest.mark.parametrize(
    ("library_root", "use_library_root"),
    [
        ("/test/library", True),
        (None, False),
    ],
)
def test_library_root_property(
    session: DummySession,  # type: ignore[valid-type]
    mock_book_repository: MagicMock,
    mock_conversion_repository: ConversionRepository,
    mock_conversion_strategy: MagicMock,
    temp_dir: Path,
    library_root: str | None,
    use_library_root: bool,
) -> None:
    """Test _library_root property returns correct path.

    Parameters
    ----------
    session : DummySession
        Session fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    mock_conversion_repository : ConversionRepository
        Conversion repository fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    temp_dir : Path
        Temporary directory fixture.
    library_root : str | None
        Library root to set.
    use_library_root : bool
        Whether to use library_root.
    """
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path=str(temp_dir / "metadata.db"),
        library_root=library_root if use_library_root else None,
    )
    service = ConversionService(
        session=session,  # type: ignore[arg-type]
        library=library,
        book_repository=mock_book_repository,
        conversion_repository=mock_conversion_repository,
        conversion_strategy=mock_conversion_strategy,
    )

    result = service._library_root

    if use_library_root:
        assert result == Path(library_root)
    else:
        assert result == Path(library.calibre_db_path)


def test_init_with_backup_service(
    session: DummySession,  # type: ignore[valid-type]
    library: Library,
    mock_book_repository: MagicMock,
    mock_conversion_repository: ConversionRepository,
    mock_conversion_strategy: MagicMock,
) -> None:
    """Test __init__ with provided backup service.

    Parameters
    ----------
    session : DummySession
        Session fixture.
    library : Library
        Library fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    mock_conversion_repository : ConversionRepository
        Conversion repository fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    """
    backup_service = FileBackupService()

    service = ConversionService(
        session=session,  # type: ignore[arg-type]
        library=library,
        book_repository=mock_book_repository,
        conversion_repository=mock_conversion_repository,
        conversion_strategy=mock_conversion_strategy,
        backup_service=backup_service,
    )

    assert service._backup_service == backup_service


def test_init_without_backup_service(
    conversion_service: ConversionService,
) -> None:
    """Test __init__ creates default backup service.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    """
    assert isinstance(conversion_service._backup_service, FileBackupService)


@pytest.mark.parametrize(
    ("format_name", "expected"),
    [
        ("epub", "EPUB"),
        ("EPUB", "EPUB"),
        (".epub", "EPUB"),
        (".EPUB", "EPUB"),
        ("mobi", "MOBI"),
    ],
)
def test_normalize_format(
    conversion_service: ConversionService,
    format_name: str,
    expected: str,
) -> None:
    """Test _normalize_format normalizes format strings.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    format_name : str
        Format name to test.
    expected : str
        Expected normalized format.
    """
    result = conversion_service._normalize_format(format_name)

    assert result == expected


def test_check_existing_conversion(
    conversion_service: ConversionService,
    mock_conversion_repository: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
) -> None:
    """Test check_existing_conversion finds existing conversion.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_conversion_repository : ConversionRepository
        Conversion repository fixture.
    session : DummySession
        Session fixture.
    """
    existing = BookConversion(
        book_id=1,
        original_format="MOBI",
        target_format="EPUB",
        status=ConversionStatus.COMPLETED,
        conversion_method="manual",
    )
    session.set_exec_result([existing])

    result = conversion_service.check_existing_conversion(1, "mobi", "epub")

    assert result == existing


def test_check_existing_conversion_returns_none(
    conversion_service: ConversionService,
    session: DummySession,  # type: ignore[valid-type]
) -> None:
    """Test check_existing_conversion returns None when not found.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    session : DummySession
        Session fixture.
    """
    session.set_exec_result([])

    result = conversion_service.check_existing_conversion(1, "mobi", "epub")

    assert result is None


def test_convert_book_returns_existing_conversion(
    conversion_service: ConversionService,
    session: DummySession,  # type: ignore[valid-type]
) -> None:
    """Test convert_book returns existing conversion.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    session : DummySession
        Session fixture.
    """
    existing = BookConversion(
        book_id=1,
        original_format="MOBI",
        target_format="EPUB",
        status=ConversionStatus.COMPLETED,
        conversion_method="manual",
    )
    session.set_exec_result([existing])

    result = conversion_service.convert_book(1, "mobi", "epub")

    assert result == existing


def test_convert_book_records_existing_format(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    session: DummySession,  # type: ignore[valid-type]
    book: Book,
    temp_dir: Path,
) -> None:
    """Test convert_book records existing format when target exists.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    session : DummySession
        Session fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    """
    session.set_exec_result([])  # No existing conversion
    mock_book_repository.get_book.return_value = book
    mock_book_repository.format_exists.return_value = True
    mock_book_repository.get_book_file_path.return_value = temp_dir / "book.mobi"

    result = conversion_service.convert_book(1, "mobi", "epub")

    assert result.status == ConversionStatus.COMPLETED
    assert result.original_format == "MOBI"
    assert result.target_format == "EPUB"


def test_validate_conversion_request_raises_book_not_found(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
) -> None:
    """Test _validate_conversion_request raises BookNotFoundError.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    """
    mock_book_repository.get_book.side_effect = BookNotFoundError(1)

    with pytest.raises(BookNotFoundError):
        conversion_service._validate_conversion_request(1, "MOBI", "EPUB")


def test_validate_conversion_request_raises_format_not_found(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    book: Book,
) -> None:
    """Test _validate_conversion_request raises FormatNotFoundError.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    book : Book
        Book fixture.
    """
    mock_book_repository.get_book.return_value = book
    mock_book_repository.get_book_file_path.return_value = None

    with pytest.raises(FormatNotFoundError):
        conversion_service._validate_conversion_request(1, "MOBI", "EPUB")


def test_validate_conversion_request_returns_request(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    book: Book,
    temp_dir: Path,
) -> None:
    """Test _validate_conversion_request returns ConversionRequest.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    """
    mock_book_repository.get_book.return_value = book
    mock_book_repository.get_book_file_path.return_value = temp_dir / "book.mobi"

    result = conversion_service._validate_conversion_request(1, "MOBI", "EPUB")

    assert isinstance(result, ConversionRequest)
    assert result.book_id == 1
    assert result.original_format == "MOBI"
    assert result.target_format == "EPUB"


def test_record_existing_format(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    session: DummySession,  # type: ignore[valid-type]
    book: Book,
    temp_dir: Path,
) -> None:
    """Test _record_existing_format creates conversion record.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    session : DummySession
        Session fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    """
    request = ConversionRequest(book_id=1, original_format="MOBI", target_format="EPUB")
    mock_book_repository.get_book.return_value = book
    mock_book_repository.get_book_file_path.return_value = temp_dir / "book.mobi"
    session.set_exec_result([])  # No existing conversion

    result = conversion_service._record_existing_format(
        request, user_id=None, conversion_method=ConversionMethod.MANUAL
    )

    assert result.status == ConversionStatus.COMPLETED
    assert result.original_format == "MOBI"
    assert result.target_format == "EPUB"
    assert session.commit_count == 1


def test_perform_conversion_with_backup(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    mock_conversion_strategy: MagicMock,
    session: DummySession,  # type: ignore[valid-type]
    book: Book,
    temp_dir: Path,
) -> None:
    """Test _perform_conversion with backup.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    session : DummySession
        Session fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    """
    request = ConversionRequest(book_id=1, original_format="MOBI", target_format="EPUB")
    original_file = temp_dir / "book.mobi"
    original_file.write_text("content")
    book_dir = temp_dir / book.path
    book_dir.mkdir(parents=True)

    mock_book_repository.get_book.return_value = book
    mock_book_repository.get_book_file_path.return_value = original_file
    mock_book_repository.get_format_data.return_value = Data(
        book=1, format="MOBI", name="Test Book", uncompressed_size=100
    )
    mock_book_repository.format_exists.return_value = True
    mock_book_repository.add_format_to_calibre.return_value = None

    mock_conversion_strategy.convert.return_value = None
    session.set_exec_result([])  # No existing conversion

    with patch.object(
        conversion_service._backup_service,
        "backup",
        return_value=temp_dir / "book.mobi.bak",
    ):
        result = conversion_service._perform_conversion(
            request,
            user_id=None,
            conversion_method=ConversionMethod.MANUAL,
            backup_original=True,
        )

    assert result.status == ConversionStatus.COMPLETED
    assert result.original_backed_up is True
    assert session.commit_count == 1


def test_perform_conversion_handles_conversion_error(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    mock_conversion_strategy: MagicMock,
    session: DummySession,  # type: ignore[valid-type]
    book: Book,
    temp_dir: Path,
) -> None:
    """Test _perform_conversion handles conversion errors.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    session : DummySession
        Session fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    """
    request = ConversionRequest(book_id=1, original_format="MOBI", target_format="EPUB")
    original_file = temp_dir / "book.mobi"
    original_file.write_text("content")

    mock_book_repository.get_book.return_value = book
    mock_book_repository.get_book_file_path.return_value = original_file
    mock_conversion_strategy.convert.side_effect = Exception("Conversion failed")
    session.set_exec_result([])  # No existing conversion

    with pytest.raises(Exception, match="Conversion failed"):
        conversion_service._perform_conversion(
            request,
            user_id=None,
            conversion_method=ConversionMethod.MANUAL,
            backup_original=False,
        )

    # Verify error was recorded
    assert session.added
    conversion = session.added[0]
    assert conversion.status == ConversionStatus.FAILED
    assert conversion.error_message == "Conversion failed"


def test_execute_conversion_with_target_data(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    mock_conversion_strategy: MagicMock,
    book: Book,
    temp_dir: Path,
    format_data: Data,
) -> None:
    """Test _execute_conversion with target format data.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    format_data : Data
        Format data fixture.
    """
    input_file = temp_dir / "book.mobi"
    input_file.write_text("content")
    book_dir = temp_dir / book.path
    book_dir.mkdir(parents=True)

    mock_book_repository.get_format_data.return_value = format_data
    mock_conversion_strategy.convert.return_value = None

    temp_file_path = temp_dir / "temp_convert.epub"
    temp_file_path.write_text("converted content")
    final_path = book_dir / f"{format_data.name}.epub"

    with (
        patch("tempfile.NamedTemporaryFile") as mock_temp,
        patch("shutil.move") as mock_move,
    ):
        mock_temp_file = MagicMock()
        mock_temp_file.name = str(temp_file_path)
        mock_temp_file.__enter__ = MagicMock(return_value=mock_temp_file)
        mock_temp_file.__exit__ = MagicMock(return_value=False)
        mock_temp.return_value = mock_temp_file

        # Make shutil.move actually create the destination file
        def move_side_effect(src: str, dst: str) -> None:
            Path(dst).write_text(Path(src).read_text())

        mock_move.side_effect = move_side_effect

        result = conversion_service._execute_conversion(input_file, "EPUB", book, 1)

        assert mock_move.called
        assert result == final_path
        assert result.exists()


def test_execute_conversion_without_target_data(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    mock_conversion_strategy: MagicMock,
    book: Book,
    temp_dir: Path,
    format_data: Data,
) -> None:
    """Test _execute_conversion without target format data.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    format_data : Data
        Format data fixture.
    """
    input_file = temp_dir / "book.mobi"
    input_file.write_text("content")
    book_dir = temp_dir / book.path
    book_dir.mkdir(parents=True)

    mock_book_repository.get_format_data.side_effect = [
        None,  # Target format not found
        format_data,  # First format found
    ]
    mock_book_repository.format_exists.return_value = True
    mock_conversion_strategy.convert.return_value = None

    temp_file_path = temp_dir / "temp_convert.epub"
    temp_file_path.write_text("converted content")
    final_path = book_dir / f"{format_data.name}.epub"

    with (
        patch("tempfile.NamedTemporaryFile") as mock_temp,
        patch("shutil.move") as mock_move,
    ):
        mock_temp_file = MagicMock()
        mock_temp_file.name = str(temp_file_path)
        mock_temp_file.__enter__ = MagicMock(return_value=mock_temp_file)
        mock_temp_file.__exit__ = MagicMock(return_value=False)
        mock_temp.return_value = mock_temp_file

        # Make shutil.move actually create the destination file
        def move_side_effect(src: str, dst: str) -> None:
            Path(dst).write_text(Path(src).read_text())

        mock_move.side_effect = move_side_effect

        result = conversion_service._execute_conversion(input_file, "EPUB", book, 1)

        assert mock_move.called
        assert result == final_path
        assert result.exists()


def test_execute_conversion_without_any_format_data(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    mock_conversion_strategy: MagicMock,
    book: Book,
    temp_dir: Path,
) -> None:
    """Test _execute_conversion without any format data.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    """
    input_file = temp_dir / "book.mobi"
    input_file.write_text("content")
    book_dir = temp_dir / book.path
    book_dir.mkdir(parents=True)

    mock_book_repository.get_format_data.return_value = None
    mock_book_repository.format_exists.return_value = False
    mock_conversion_strategy.convert.return_value = None

    temp_file_path = temp_dir / "temp_convert.epub"
    temp_file_path.write_text("converted content")
    final_path = book_dir / "1.epub"  # Uses book_id when no format data

    with (
        patch("tempfile.NamedTemporaryFile") as mock_temp,
        patch("shutil.move") as mock_move,
    ):
        mock_temp_file = MagicMock()
        mock_temp_file.name = str(temp_file_path)
        mock_temp_file.__enter__ = MagicMock(return_value=mock_temp_file)
        mock_temp_file.__exit__ = MagicMock(return_value=False)
        mock_temp.return_value = mock_temp_file

        # Make shutil.move actually create the destination file
        def move_side_effect(src: str, dst: str) -> None:
            Path(dst).write_text(Path(src).read_text())

        mock_move.side_effect = move_side_effect

        result = conversion_service._execute_conversion(input_file, "EPUB", book, 1)

        assert mock_move.called
        assert result == final_path
        assert result.exists()


def test_execute_conversion_cleans_up_on_error(
    conversion_service: ConversionService,
    mock_conversion_strategy: MagicMock,
    book: Book,
    temp_dir: Path,
) -> None:
    """Test _execute_conversion cleans up temp file on error.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_conversion_strategy : MagicMock
        Mock conversion strategy fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    """
    input_file = temp_dir / "book.mobi"
    input_file.write_text("content")
    temp_path = temp_dir / "temp_convert.epub"
    temp_path.write_text("converted")

    mock_conversion_strategy.convert.side_effect = Exception("Conversion failed")

    with patch("tempfile.NamedTemporaryFile") as mock_temp:
        mock_temp_file = MagicMock()
        mock_temp_file.name = str(temp_path)
        mock_temp_file.__enter__ = MagicMock(return_value=mock_temp_file)
        mock_temp_file.__exit__ = MagicMock(return_value=False)
        mock_temp.return_value = mock_temp_file

        with patch("pathlib.Path.unlink") as mock_unlink:
            with pytest.raises(Exception, match="Conversion failed"):
                conversion_service._execute_conversion(input_file, "EPUB", book, 1)

            # Temp file cleanup should be attempted
            mock_unlink.assert_called()


@pytest.mark.parametrize(
    ("formats", "expected"),
    [
        (["EPUB"], "EPUB"),
        (["MOBI"], "MOBI"),
        (["AZW3"], "AZW3"),
        (["PDF"], "PDF"),
        ([], ""),
    ],
)
def test_get_first_format(
    conversion_service: ConversionService,
    mock_book_repository: MagicMock,
    formats: list[str],
    expected: str,
) -> None:
    """Test _get_first_format returns first available format.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    mock_book_repository : MagicMock
        Mock book repository fixture.
    formats : list[str]
        Formats that exist.
    expected : str
        Expected first format.
    """

    def format_exists_side_effect(book_id: int, format_name: str) -> bool:
        return format_name in formats

    mock_book_repository.format_exists.side_effect = format_exists_side_effect

    result = conversion_service._get_first_format(1)

    assert result == expected


def test_now_returns_utc_datetime(
    conversion_service: ConversionService,
) -> None:
    """Test _now returns UTC datetime.

    Parameters
    ----------
    conversion_service : ConversionService
        Service fixture.
    """
    result = conversion_service._now()

    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
