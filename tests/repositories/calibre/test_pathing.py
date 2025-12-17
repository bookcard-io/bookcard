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

"""Tests for pathing module."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from bookcard.models.core import Book
from bookcard.repositories.calibre.pathing import BookPathService

if TYPE_CHECKING:
    from sqlmodel import Session


class TestBookPathService:
    """Test suite for BookPathService."""

    def test_normalize_title_and_author_with_provided_values(self) -> None:
        """Test normalize_title_and_author with provided values."""
        service = BookPathService()
        metadata = MagicMock()
        title, author = service.normalize_title_and_author(
            title="Test Title", author_name="Test Author", metadata=metadata
        )
        assert title == "Test Title"
        assert author == "Test Author"

    def test_normalize_title_and_author_from_metadata(self) -> None:
        """Test normalize_title_and_author falls back to metadata."""
        service = BookPathService()
        metadata = MagicMock()
        metadata.title = "Metadata Title"
        metadata.author = "Metadata Author"
        title, author = service.normalize_title_and_author(
            title=None, author_name=None, metadata=metadata
        )
        assert title == "Metadata Title"
        assert author == "Metadata Author"

    def test_normalize_title_and_author_falls_back_to_unknown(self) -> None:
        """Test normalize_title_and_author falls back to 'Unknown'."""
        service = BookPathService()
        metadata = MagicMock()
        metadata.title = None
        metadata.author = None
        title, author = service.normalize_title_and_author(
            title=None, author_name=None, metadata=metadata
        )
        assert title == "Unknown"
        assert author == "Unknown"

    def test_normalize_title_and_author_empty_strings(self) -> None:
        """Test normalize_title_and_author handles empty strings."""
        service = BookPathService()
        metadata = MagicMock()
        metadata.title = ""
        metadata.author = ""
        title, author = service.normalize_title_and_author(
            title="", author_name="", metadata=metadata
        )
        assert title == "Unknown"
        assert author == "Unknown"

    def test_normalize_title_and_author_whitespace_only(self) -> None:
        """Test normalize_title_and_author handles whitespace-only strings."""
        service = BookPathService()
        metadata = MagicMock()
        metadata.title = None
        metadata.author = None
        title, author = service.normalize_title_and_author(
            title="   ", author_name="   ", metadata=metadata
        )
        assert title == "Unknown"
        assert author == "Unknown"

    def test_sanitize_title_dir(self) -> None:
        """Test sanitize_title_dir sanitizes title."""
        service = BookPathService()
        result = service.sanitize_title_dir("Test Book")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_sanitize_title_dir_with_max_length(self) -> None:
        """Test sanitize_title_dir respects max_length."""
        service = BookPathService()
        long_title = "A" * 200
        result = service.sanitize_title_dir(long_title, max_length=50)
        assert len(result) <= 50

    def test_calculate_book_path_with_valid_inputs(self) -> None:
        """Test calculate_book_path with valid inputs."""
        service = BookPathService()
        result = service.calculate_book_path(
            author_names=["Test Author"], title="Test Book"
        )
        assert result is not None
        assert isinstance(result, str)
        assert "Test Author" in result or "Test" in result

    def test_calculate_book_path_with_no_author_names(self) -> None:
        """Test calculate_book_path returns None with no author names."""
        service = BookPathService()
        result = service.calculate_book_path(author_names=None, title="Test Book")
        assert result is None

    def test_calculate_book_path_with_empty_author_names(self) -> None:
        """Test calculate_book_path returns None with empty author names."""
        service = BookPathService()
        result = service.calculate_book_path(author_names=[], title="Test Book")
        assert result is None

    def test_calculate_book_path_with_no_title(self) -> None:
        """Test calculate_book_path returns None with no title."""
        service = BookPathService()
        result = service.calculate_book_path(author_names=["Test Author"], title=None)
        assert result is None

    def test_calculate_book_path_uses_first_author(self) -> None:
        """Test calculate_book_path uses first author."""
        service = BookPathService()
        result = service.calculate_book_path(
            author_names=["First Author", "Second Author"], title="Test Book"
        )
        assert result is not None

    def test_prepare_book_path_and_format_without_session(self) -> None:
        """Test prepare_book_path_and_format without session."""
        service = BookPathService()
        book_path, title_dir, format_upper = service.prepare_book_path_and_format(
            session=None,
            title="Test Book",
            author_name="Test Author",
            file_format="epub",
        )
        assert isinstance(book_path, str)
        assert isinstance(title_dir, str)
        assert format_upper == "EPUB"

    def test_prepare_book_path_and_format_with_session_unique_path(
        self, in_memory_db: Session
    ) -> None:
        """Test prepare_book_path_and_format with session and unique path."""
        service = BookPathService()
        book_path, title_dir, format_upper = service.prepare_book_path_and_format(
            session=in_memory_db,
            title="Unique Book",
            author_name="Unique Author",
            file_format="pdf",
        )
        assert isinstance(book_path, str)
        assert isinstance(title_dir, str)
        assert format_upper == "PDF"

    def test_prepare_book_path_and_format_with_session_existing_path(
        self, in_memory_db: Session
    ) -> None:
        """Test prepare_book_path_and_format makes path unique if exists."""
        service = BookPathService()
        # Create existing book with same path
        book = Book(
            id=1,
            title="Test Book",
            path="Test Author/Test Book",
            uuid="existing-uuid",
            timestamp=datetime.now(UTC),
        )
        in_memory_db.add(book)
        in_memory_db.commit()

        book_path, title_dir, format_upper = service.prepare_book_path_and_format(
            session=in_memory_db,
            title="Test Book",
            author_name="Test Author",
            file_format="epub",
        )
        # Path should be made unique
        assert book_path != "Test Author/Test Book"
        assert "(2)" in book_path or "(2)" in title_dir
        assert format_upper == "EPUB"

    def test_prepare_book_path_and_format_raises_on_invalid_input(self) -> None:
        """Test prepare_book_path_and_format raises on invalid input."""
        service = BookPathService()
        with pytest.raises(ValueError, match="Cannot calculate book path"):
            service.prepare_book_path_and_format(
                session=None,
                title="",
                author_name="",
                file_format="epub",
            )

    def test_prepare_book_path_and_format_strips_dot_from_format(self) -> None:
        """Test prepare_book_path_and_format strips dot from format."""
        service = BookPathService()
        _, _, format_upper = service.prepare_book_path_and_format(
            session=None,
            title="Test Book",
            author_name="Test Author",
            file_format=".epub",
        )
        assert format_upper == "EPUB"

    def test_make_path_unique_with_no_existing_book(
        self, in_memory_db: Session
    ) -> None:
        """Test make_path_unique returns original path if no conflict."""
        service = BookPathService()
        path, title = service.make_path_unique(
            session=in_memory_db,
            base_path="Author/Book",
            base_title="Book",
            author_name="Author",
        )
        assert path == "Author/Book"
        assert title == "Book"

    def test_make_path_unique_with_existing_book(self, in_memory_db: Session) -> None:
        """Test make_path_unique appends number if path exists."""
        service = BookPathService()
        # Create existing book
        book = Book(
            id=1,
            title="Book",
            path="Author/Book",
            uuid="existing-uuid",
            timestamp=datetime.now(UTC),
        )
        in_memory_db.add(book)
        in_memory_db.commit()

        path, title = service.make_path_unique(
            session=in_memory_db,
            base_path="Author/Book",
            base_title="Book",
            author_name="Author",
        )
        assert path != "Author/Book"
        assert "(2)" in title

    def test_make_path_unique_with_multiple_conflicts(
        self, in_memory_db: Session
    ) -> None:
        """Test make_path_unique handles multiple conflicts."""
        service = BookPathService()
        # Create multiple existing books
        for i in range(1, 4):
            book = Book(
                id=i,
                title=f"Book ({i})" if i > 1 else "Book",
                path=f"Author/Book ({i})" if i > 1 else "Author/Book",
                uuid=f"uuid-{i}",
                timestamp=datetime.now(UTC),
            )
            in_memory_db.add(book)
        in_memory_db.commit()

        _path, title = service.make_path_unique(
            session=in_memory_db,
            base_path="Author/Book",
            base_title="Book",
            author_name="Author",
        )
        assert "(4)" in title

    def test_make_path_unique_with_uuid_fallback(self, in_memory_db: Session) -> None:
        """Test make_path_unique uses UUID fallback after 1000 attempts."""
        service = BookPathService()
        # Create 1000+ existing books with same path pattern
        for i in range(1, 1002):
            book = Book(
                id=i,
                title=f"Book ({i})" if i > 1 else "Book",
                path=f"Author/Book ({i})" if i > 1 else "Author/Book",
                uuid=f"uuid-{i}",
                timestamp=datetime.now(UTC),
            )
            in_memory_db.add(book)
        in_memory_db.commit()

        path, title = service.make_path_unique(
            session=in_memory_db,
            base_path="Author/Book",
            base_title="Book",
            author_name="Author",
        )
        # Should use UUID fallback
        assert path != "Author/Book"
        assert "Book" in title
        assert len(title) > len("Book")

    @pytest.mark.parametrize(
        ("title", "author", "expected_title", "expected_author"),
        [
            ("Test Book", "Test Author", "Test Book", "Test Author"),
            (None, None, "Unknown", "Unknown"),
            ("", "", "Unknown", "Unknown"),
            ("   ", "   ", "Unknown", "Unknown"),
        ],
    )
    def test_normalize_title_and_author_parametrized(
        self,
        title: str | None,
        author: str | None,
        expected_title: str,
        expected_author: str,
    ) -> None:
        """Test normalize_title_and_author with various inputs (parametrized)."""
        service = BookPathService()
        metadata = MagicMock()
        metadata.title = None
        metadata.author = None
        result_title, result_author = service.normalize_title_and_author(
            title=title, author_name=author, metadata=metadata
        )
        assert result_title == expected_title
        assert result_author == expected_author

    @pytest.mark.parametrize(
        ("file_format", "expected_format"),
        [
            ("epub", "EPUB"),
            ("EPUB", "EPUB"),
            (".epub", "EPUB"),
            (".EPUB", "EPUB"),
            ("pdf", "PDF"),
            ("mobi", "MOBI"),
        ],
    )
    def test_prepare_book_path_and_format_formats_parametrized(
        self, file_format: str, expected_format: str
    ) -> None:
        """Test prepare_book_path_and_format handles various formats (parametrized)."""
        service = BookPathService()
        _, _, format_upper = service.prepare_book_path_and_format(
            session=None,
            title="Test Book",
            author_name="Test Author",
            file_format=file_format,
        )
        assert format_upper == expected_format
