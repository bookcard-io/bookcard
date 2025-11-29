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

"""Tests for library path resolver to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from fundamental.models.config import Library
from fundamental.services.metadata_enforcement.library_path_resolver import (
    LibraryPathResolver,
)


@pytest.fixture
def library() -> Library:
    """Create a test library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/test/library",
        calibre_db_file="metadata.db",
    )


@pytest.fixture
def library_path_resolver(library: Library) -> LibraryPathResolver:
    """Create a library path resolver instance."""
    return LibraryPathResolver(library)


def test_init(library: Library) -> None:
    """Test LibraryPathResolver initialization."""
    resolver = LibraryPathResolver(library)
    assert resolver._library == library
    assert resolver._locator is not None


def test_get_library_root(
    library_path_resolver: LibraryPathResolver, library: Library
) -> None:
    """Test get_library_root method."""
    mock_path = Path("/test/library/root")
    with patch.object(
        library_path_resolver._locator, "get_location", return_value=mock_path
    ):
        result = library_path_resolver.get_library_root()
        assert result == mock_path


def test_get_book_directory(
    library_path_resolver: LibraryPathResolver, library: Library
) -> None:
    """Test get_book_directory method."""
    mock_library_root = Path("/test/library/root")
    with patch.object(
        library_path_resolver._locator, "get_location", return_value=mock_library_root
    ):
        book_path = "Author Name/Test Book (1)"
        result = library_path_resolver.get_book_directory(book_path)
        assert result == mock_library_root / book_path


@pytest.mark.parametrize(
    "book_path",
    [
        "Author Name/Test Book (1)",
        "Simple Book",
        "Nested/Path/To/Book",
        "",
    ],
)
def test_get_book_directory_various_paths(
    library_path_resolver: LibraryPathResolver,
    book_path: str,
) -> None:
    """Test get_book_directory with various book paths."""
    mock_library_root = Path("/test/library/root")
    with patch.object(
        library_path_resolver._locator, "get_location", return_value=mock_library_root
    ):
        result = library_path_resolver.get_book_directory(book_path)
        assert result == mock_library_root / book_path
