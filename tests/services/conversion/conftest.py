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

"""Shared fixtures for conversion service tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from fundamental.models.config import Library
from fundamental.models.conversion import BookConversion, ConversionStatus
from fundamental.models.core import Book
from fundamental.models.media import Data

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test files.

    Returns
    -------
    Path
        Path to temporary directory.
    """
    temp = TemporaryDirectory()
    yield Path(temp.name)
    temp.cleanup()


@pytest.fixture
def library(temp_dir: Path) -> Library:
    """Create a test library configuration.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory fixture.

    Returns
    -------
    Library
        Library instance.
    """
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path=str(temp_dir / "metadata.db"),
        library_root=str(temp_dir),
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


@pytest.fixture
def mock_calibre_repo() -> MagicMock:
    """Create a mock CalibreBookRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    mock = MagicMock()
    mock.get_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock.get_session.return_value.__exit__ = MagicMock(return_value=False)
    return mock


@pytest.fixture
def mock_conversion_strategy() -> MagicMock:
    """Create a mock ConversionStrategy.

    Returns
    -------
    MagicMock
        Mock strategy instance.
    """
    mock = MagicMock()
    mock.supports.return_value = True
    return mock


@pytest.fixture
def book_conversion() -> BookConversion:
    """Create a test book conversion record.

    Returns
    -------
    BookConversion
        BookConversion instance.
    """
    return BookConversion(
        id=1,
        book_id=1,
        library_id=1,
        user_id=None,
        original_format="MOBI",
        target_format="EPUB",
        original_file_path="/path/to/book.mobi",
        converted_file_path="/path/to/book.epub",
        original_backed_up=True,
        conversion_method="manual",
        status=ConversionStatus.COMPLETED,
    )
