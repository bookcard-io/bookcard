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

"""Tests for KoboDownloadService to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from bookcard.models.config import Library
from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.kobo.download_service import (
    MEDIA_TYPES,
    KoboDownloadService,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def library() -> Library:
    """Create a test library.

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
    """Create a test library with library_root.

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
def mock_book_service(library: Library) -> MagicMock:
    """Create a mock BookService.

    Parameters
    ----------
    library : Library
        Test library.

    Returns
    -------
    MagicMock
        Mock book service instance.
    """
    service = MagicMock()
    service._library = library
    service.get_book_full = MagicMock(return_value=None)
    return service


@pytest.fixture
def download_service(mock_book_service: MagicMock) -> KoboDownloadService:
    """Create KoboDownloadService instance for testing.

    Parameters
    ----------
    mock_book_service : MagicMock
        Mock book service.

    Returns
    -------
    KoboDownloadService
        Service instance.
    """
    return KoboDownloadService(mock_book_service)


@pytest.fixture
def book() -> Book:
    """Create a test book.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(id=1, title="Test Book", path="Author/Test Book (1)")


@pytest.fixture
def book_with_rels(book: Book) -> BookWithFullRelations:
    """Create a test book with relations.

    Parameters
    ----------
    book : Book
        Test book.

    Returns
    -------
    BookWithFullRelations
        Book with relations instance.
    """
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
        formats=[{"format": "EPUB", "name": "test.epub", "size": 1000}],
    )


# ============================================================================
# Tests for KoboDownloadService.__init__
# ============================================================================


def test_init(mock_book_service: MagicMock) -> None:
    """Test KoboDownloadService initialization.

    Parameters
    ----------
    mock_book_service : MagicMock
        Mock book service.
    """
    service = KoboDownloadService(mock_book_service)
    assert service._book_service == mock_book_service


# ============================================================================
# Tests for KoboDownloadService.get_download_file_info
# ============================================================================


def test_get_download_file_info_success(
    download_service: KoboDownloadService,
    mock_book_service: MagicMock,
    book_with_rels: BookWithFullRelations,
    library: Library,
) -> None:
    """Test getting download file info successfully.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    library : Library
        Test library.
    """
    with TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book_with_rels.book.path
        book_path.mkdir(parents=True, exist_ok=True)
        file_path = book_path / "test.epub"
        file_path.write_text("fake epub content")

        mock_book_service._library = library
        mock_book_service._library.calibre_db_path = str(library_path)
        mock_book_service.get_book_full.return_value = book_with_rels

        result = download_service.get_download_file_info(book_id=1, book_format="EPUB")

        assert result.file_path == file_path
        assert result.filename == "test.epub"
        assert result.media_type == MEDIA_TYPES["EPUB"]


def test_get_download_file_info_book_not_found(
    download_service: KoboDownloadService,
    mock_book_service: MagicMock,
) -> None:
    """Test getting download file info when book not found.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    """
    mock_book_service.get_book_full.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        download_service.get_download_file_info(book_id=999, book_format="EPUB")

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "book_not_found"


def test_get_download_file_info_format_not_found(
    download_service: KoboDownloadService,
    mock_book_service: MagicMock,
    book_with_rels: BookWithFullRelations,
) -> None:
    """Test getting download file info when format not found.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    """
    mock_book_service.get_book_full.return_value = book_with_rels

    with pytest.raises(HTTPException) as exc_info:
        download_service.get_download_file_info(book_id=1, book_format="MOBI")

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "format_not_found: MOBI" in exc_info.value.detail


def test_get_download_file_info_file_not_found(
    download_service: KoboDownloadService,
    mock_book_service: MagicMock,
    book_with_rels: BookWithFullRelations,
    library: Library,
) -> None:
    """Test getting download file info when file not found.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    library : Library
        Test library.
    """
    with TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        mock_book_service._library = library
        mock_book_service._library.calibre_db_path = str(library_path)
        mock_book_service.get_book_full.return_value = book_with_rels

        with pytest.raises(HTTPException) as exc_info:
            download_service.get_download_file_info(book_id=1, book_format="EPUB")

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "file_not_found"


# ============================================================================
# Tests for KoboDownloadService._find_format
# ============================================================================


@pytest.mark.parametrize(
    ("formats", "book_format", "expected"),
    [
        (
            [{"format": "EPUB", "name": "test.epub"}],
            "EPUB",
            {"format": "EPUB", "name": "test.epub"},
        ),
        (
            [{"format": "epub", "name": "test.epub"}],
            "EPUB",
            {"format": "epub", "name": "test.epub"},
        ),
        (
            [{"format": "EPUB", "name": "test.epub"}],
            "epub",
            {"format": "EPUB", "name": "test.epub"},
        ),
        (
            [{"format": "KEPUB", "name": "test.kepub"}],
            "KEPUB",
            {"format": "KEPUB", "name": "test.kepub"},
        ),
        ([{"format": "EPUB", "name": "test.epub"}], "MOBI", None),
        ([], "EPUB", None),
    ],
)
def test_find_format(
    download_service: KoboDownloadService,
    book_with_rels: BookWithFullRelations,
    formats: list[dict[str, object]],
    book_format: str,
    expected: dict[str, object] | None,
) -> None:
    """Test finding format in book formats.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    formats : list[dict[str, object]]
        List of formats.
    book_format : str
        Format to find.
    expected : dict[str, object] | None
        Expected result.
    """
    book_with_rels.formats = formats  # type: ignore[assignment]
    result = download_service._find_format(book_with_rels, book_format)
    assert result == expected


# ============================================================================
# Tests for KoboDownloadService._resolve_library_path
# ============================================================================


def test_resolve_library_path_with_root(
    download_service: KoboDownloadService,
    library_with_root: Library,
    mock_book_service: MagicMock,
) -> None:
    """Test resolving library path when library_root is set.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    library_with_root : Library
        Library with root.
    mock_book_service : MagicMock
        Mock book service.
    """
    mock_book_service._library = library_with_root
    result = download_service._resolve_library_path()
    assert result == Path("/path/to/library_root")


def test_resolve_library_path_dir(
    download_service: KoboDownloadService,
    library: Library,
    mock_book_service: MagicMock,
) -> None:
    """Test resolving library path when calibre_db_path is a directory.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    library : Library
        Test library.
    mock_book_service : MagicMock
        Mock book service.
    """
    with TemporaryDirectory() as tmpdir:
        library.calibre_db_path = tmpdir
        mock_book_service._library = library
        result = download_service._resolve_library_path()
        assert result == Path(tmpdir)


def test_resolve_library_path_file(
    download_service: KoboDownloadService,
    library: Library,
    mock_book_service: MagicMock,
) -> None:
    """Test resolving library path when calibre_db_path is a file.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    library : Library
        Test library.
    mock_book_service : MagicMock
        Mock book service.
    """
    with TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.write_text("fake db")
        library.calibre_db_path = str(db_file)
        mock_book_service._library = library
        result = download_service._resolve_library_path()
        assert result == Path(tmpdir)


# ============================================================================
# Tests for KoboDownloadService._resolve_file_path
# ============================================================================


def test_resolve_file_path_success(
    download_service: KoboDownloadService,
    book: Book,
) -> None:
    """Test resolving file path successfully.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    book : Book
        Test book.
    """
    with TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        file_path = book_path / "test.epub"
        file_path.write_text("content")

        format_data = {"format": "EPUB", "name": "test.epub", "size": 1000}
        result_path, result_name = download_service._resolve_file_path(
            book=book,
            library_path=library_path,
            book_id=1,
            book_format="EPUB",
            format_data=format_data,
        )

        assert result_path == file_path
        assert result_name == "test.epub"


def test_resolve_file_path_alternative_naming(
    download_service: KoboDownloadService,
    book: Book,
) -> None:
    """Test resolving file path with alternative naming.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    book : Book
        Test book.
    """
    with TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        alt_file = book_path / "1.epub"
        alt_file.write_text("content")

        format_data = {"format": "EPUB", "name": "nonexistent.epub", "size": 1000}
        result_path, result_name = download_service._resolve_file_path(
            book=book,
            library_path=library_path,
            book_id=1,
            book_format="EPUB",
            format_data=format_data,
        )

        assert result_path == alt_file
        assert result_name == "1.epub"


def test_resolve_file_path_no_name(
    download_service: KoboDownloadService,
    book: Book,
) -> None:
    """Test resolving file path when format data has no name.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    book : Book
        Test book.
    """
    with TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)

        format_data = {"format": "EPUB", "size": 1000}
        result_path, result_name = download_service._resolve_file_path(
            book=book,
            library_path=library_path,
            book_id=1,
            book_format="EPUB",
            format_data=format_data,
        )

        assert result_name == "1.epub"
        assert result_path.name == "1.epub"


def test_resolve_file_path_wrong_extension(
    download_service: KoboDownloadService,
    book: Book,
) -> None:
    """Test resolving file path when filename has wrong extension.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    book : Book
        Test book.
    """
    with TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)

        format_data = {"format": "EPUB", "name": "test.txt", "size": 1000}
        result_path, result_name = download_service._resolve_file_path(
            book=book,
            library_path=library_path,
            book_id=1,
            book_format="EPUB",
            format_data=format_data,
        )

        assert result_name == "test.txt.epub"
        assert result_path.name == "test.txt.epub"


def test_resolve_file_path_non_string_name(
    download_service: KoboDownloadService,
    book: Book,
) -> None:
    """Test resolving file path when name is not a string.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    book : Book
        Test book.
    """
    with TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)

        format_data = {"format": "EPUB", "name": 123, "size": 1000}
        _result_path, result_name = download_service._resolve_file_path(
            book=book,
            library_path=library_path,
            book_id=1,
            book_format="EPUB",
            format_data=format_data,
        )

        assert result_name == "1.epub"


# ============================================================================
# Tests for KoboDownloadService._get_media_type
# ============================================================================


@pytest.mark.parametrize(
    ("book_format", "expected"),
    [
        ("EPUB", MEDIA_TYPES["EPUB"]),
        ("KEPUB", MEDIA_TYPES["KEPUB"]),
        ("PDF", MEDIA_TYPES["PDF"]),
        ("MOBI", MEDIA_TYPES["MOBI"]),
        ("epub", MEDIA_TYPES["EPUB"]),
        ("UNKNOWN", "application/octet-stream"),
    ],
)
def test_get_media_type(
    download_service: KoboDownloadService,
    book_format: str,
    expected: str,
) -> None:
    """Test getting media type for book format.

    Parameters
    ----------
    download_service : KoboDownloadService
        Service instance.
    book_format : str
        Book format.
    expected : str
        Expected media type.
    """
    result = download_service._get_media_type(book_format)
    assert result == expected
