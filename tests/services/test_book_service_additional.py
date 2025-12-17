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

"""Additional tests for book service to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from bookcard.models.config import Library
from bookcard.models.core import Book
from bookcard.services.book_service import BookService


def test_get_thumbnail_path_with_library_root() -> None:
    """Test get_thumbnail_path uses library_root when set (covers line 260)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/db",
        calibre_db_file="metadata.db",
        library_root="/path/to/books",
    )

    book = Book(
        id=123,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (123)",
    )

    with (
        patch("bookcard.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=True) as mock_exists,
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book)

        assert result is not None
        # Verify it uses library_root instead of calibre_db_path
        assert str(result) == str(
            Path("/path/to/books") / "Author Name/Test Book (123)" / "cover.jpg"
        )
        mock_exists.assert_called_once()
