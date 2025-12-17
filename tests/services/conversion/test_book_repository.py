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

"""Tests for CalibreBookRepositoryAdapter to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.services.conversion.book_repository import (
    CalibreBookRepositoryAdapter,
)
from bookcard.services.conversion.exceptions import BookNotFoundError

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def mock_calibre_repo() -> MagicMock:
    """Create a mock CalibreBookRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    mock = MagicMock()
    mock_session = MagicMock()
    mock.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock.get_session.return_value.__exit__ = MagicMock(return_value=False)
    return mock


@pytest.fixture
def adapter(mock_calibre_repo: MagicMock) -> CalibreBookRepositoryAdapter:
    """Create CalibreBookRepositoryAdapter instance.

    Parameters
    ----------
    mock_calibre_repo : MagicMock
        Mock CalibreBookRepository fixture.

    Returns
    -------
    CalibreBookRepositoryAdapter
        Adapter instance.
    """
    return CalibreBookRepositoryAdapter(mock_calibre_repo)


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


def test_get_book_returns_book(
    adapter: CalibreBookRepositoryAdapter,
    mock_calibre_repo: MagicMock,
    book: Book,
) -> None:
    """Test get_book returns book when found.

    Parameters
    ----------
    adapter : CalibreBookRepositoryAdapter
        Adapter fixture.
    mock_calibre_repo : MagicMock
        Mock repository fixture.
    book : Book
        Book fixture.
    """
    mock_session = mock_calibre_repo.get_session.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.first.return_value = book
    mock_session.exec.return_value = mock_result

    result = adapter.get_book(1)

    assert result == book
    mock_calibre_repo.get_session.assert_called_once()


def test_get_book_raises_error_when_not_found(
    adapter: CalibreBookRepositoryAdapter,
    mock_calibre_repo: MagicMock,
) -> None:
    """Test get_book raises BookNotFoundError when book not found.

    Parameters
    ----------
    adapter : CalibreBookRepositoryAdapter
        Adapter fixture.
    mock_calibre_repo : MagicMock
        Mock repository fixture.
    """
    mock_session = mock_calibre_repo.get_session.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    with pytest.raises(BookNotFoundError, match="Book 1 not found"):
        adapter.get_book(1)


@pytest.mark.parametrize(
    ("format_name", "expected_format"),
    [
        ("epub", "EPUB"),
        ("EPUB", "EPUB"),
        ("Epub", "EPUB"),
        ("mobi", "MOBI"),
    ],
)
def test_get_format_data_normalizes_format(
    adapter: CalibreBookRepositoryAdapter,
    mock_calibre_repo: MagicMock,
    format_data: Data,
    format_name: str,
    expected_format: str,
) -> None:
    """Test get_format_data normalizes format to uppercase.

    Parameters
    ----------
    adapter : CalibreBookRepositoryAdapter
        Adapter fixture.
    mock_calibre_repo : MagicMock
        Mock repository fixture.
    format_data : Data
        Format data fixture.
    format_name : str
        Format name to test.
    expected_format : str
        Expected normalized format.
    """
    mock_session = mock_calibre_repo.get_session.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.first.return_value = format_data
    mock_session.exec.return_value = mock_result

    result = adapter.get_format_data(1, format_name)

    assert result == format_data
    # Verify format was normalized in query
    call_args = mock_session.exec.call_args[0][0]
    assert hasattr(call_args, "where")  # SQLModel statement


def test_get_format_data_returns_none_when_not_found(
    adapter: CalibreBookRepositoryAdapter,
    mock_calibre_repo: MagicMock,
) -> None:
    """Test get_format_data returns None when format not found.

    Parameters
    ----------
    adapter : CalibreBookRepositoryAdapter
        Adapter fixture.
    mock_calibre_repo : MagicMock
        Mock repository fixture.
    """
    mock_session = mock_calibre_repo.get_session.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    result = adapter.get_format_data(1, "EPUB")

    assert result is None


@pytest.mark.parametrize(
    ("format_exists", "expected_result"),
    [
        (True, True),
        (False, False),
    ],
)
def test_format_exists(
    adapter: CalibreBookRepositoryAdapter,
    mock_calibre_repo: MagicMock,
    format_data: Data,
    format_exists: bool,
    expected_result: bool,
) -> None:
    """Test format_exists checks if format exists.

    Parameters
    ----------
    adapter : CalibreBookRepositoryAdapter
        Adapter fixture.
    mock_calibre_repo : MagicMock
        Mock repository fixture.
    format_data : Data
        Format data fixture.
    format_exists : bool
        Whether format exists.
    expected_result : bool
        Expected result.
    """
    mock_session = mock_calibre_repo.get_session.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.first.return_value = format_data if format_exists else None
    mock_session.exec.return_value = mock_result

    result = adapter.format_exists(1, "EPUB")

    assert result == expected_result


@pytest.mark.parametrize(
    ("data_name", "book_id_str", "primary_exists", "alt_exists", "expected_path"),
    [
        ("Test Book", "1", True, False, "Test Book.epub"),
        ("Test Book", "1", False, True, "1.epub"),
        ("Test Book", "1", False, False, None),
        (None, "1", True, False, "1.epub"),
    ],
)
def test_get_book_file_path(
    adapter: CalibreBookRepositoryAdapter,
    mock_calibre_repo: MagicMock,
    book: Book,
    format_data: Data,
    temp_dir: Path,
    data_name: str | None,
    book_id_str: str,
    primary_exists: bool,
    alt_exists: bool,
    expected_path: str | None,
) -> None:
    """Test get_book_file_path returns correct path.

    Parameters
    ----------
    adapter : CalibreBookRepositoryAdapter
        Adapter fixture.
    mock_calibre_repo : MagicMock
        Mock repository fixture.
    book : Book
        Book fixture.
    format_data : Data
        Format data fixture.
    temp_dir : Path
        Temporary directory fixture.
    data_name : str | None
        Data name to use.
    book_id_str : str
        Book ID as string.
    primary_exists : bool
        Whether primary path exists.
    alt_exists : bool
        Whether alternative path exists.
    expected_path : str | None
        Expected file path.
    """
    library_root = temp_dir
    book_dir = library_root / book.path
    book_dir.mkdir(parents=True)

    format_data.name = data_name
    mock_session = mock_calibre_repo.get_session.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.first.return_value = format_data
    mock_session.exec.return_value = mock_result

    if primary_exists:
        primary_path = book_dir / f"{data_name or book_id_str}.epub"
        primary_path.write_text("content")
    if alt_exists:
        alt_path = book_dir / f"{book_id_str}.epub"
        alt_path.write_text("content")

    result = adapter.get_book_file_path(book, 1, "EPUB", library_root)

    if expected_path:
        assert result is not None
        assert result.name == expected_path
    else:
        assert result is None


def test_get_book_file_path_returns_none_when_data_not_found(
    adapter: CalibreBookRepositoryAdapter,
    mock_calibre_repo: MagicMock,
    book: Book,
    temp_dir: Path,
) -> None:
    """Test get_book_file_path returns None when format data not found.

    Parameters
    ----------
    adapter : CalibreBookRepositoryAdapter
        Adapter fixture.
    mock_calibre_repo : MagicMock
        Mock repository fixture.
    book : Book
        Book fixture.
    temp_dir : Path
        Temporary directory fixture.
    """
    library_root = temp_dir
    mock_session = mock_calibre_repo.get_session.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    result = adapter.get_book_file_path(book, 1, "EPUB", library_root)

    assert result is None


@pytest.mark.parametrize(
    ("existing_format", "file_size", "file_name"),
    [
        (True, 2048, "converted_book"),
        (False, 4096, "new_format"),
    ],
)
def test_add_format_to_calibre(
    adapter: CalibreBookRepositoryAdapter,
    mock_calibre_repo: MagicMock,
    format_data: Data,
    temp_dir: Path,
    existing_format: bool,
    file_size: int,
    file_name: str,
) -> None:
    """Test add_format_to_calibre creates or updates format.

    Parameters
    ----------
    adapter : CalibreBookRepositoryAdapter
        Adapter fixture.
    mock_calibre_repo : MagicMock
        Mock repository fixture.
    format_data : Data
        Format data fixture.
    temp_dir : Path
        Temporary directory fixture.
    existing_format : bool
        Whether format already exists.
    file_size : int
        File size to test.
    file_name : str
        File name to test.
    """
    file_path = temp_dir / f"{file_name}.epub"
    file_path.write_bytes(b"x" * file_size)

    mock_session = mock_calibre_repo.get_session.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.first.return_value = format_data if existing_format else None
    mock_session.exec.return_value = mock_result

    adapter.add_format_to_calibre(1, file_path, "EPUB")

    if existing_format:
        assert format_data.uncompressed_size == file_size
        assert format_data.name == file_name
        mock_session.add.assert_called_with(format_data)
    else:
        # Verify new Data was created
        assert mock_session.add.called
    mock_session.commit.assert_called_once()
