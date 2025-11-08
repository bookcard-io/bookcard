# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for book service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fundamental.models.config import Library
from fundamental.models.core import Book
from fundamental.repositories.calibre_book_repository import BookWithRelations
from fundamental.services.book_service import BookService


def test_book_service_init() -> None:
    """Test BookService initialization (covers lines 52-57)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        service = BookService(library)
        assert service._library is library
        mock_repo_class.assert_called_once_with(
            calibre_db_path="/path/to/library",
            calibre_db_file="metadata.db",
        )


def test_list_books_calculates_offset() -> None:
    """Test list_books calculates offset correctly (covers lines 87-96)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_books.return_value = []
        mock_repo.count_books.return_value = 0
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        books, total = service.list_books(page=2, page_size=20)

        # Page 2 with page_size 20 should have offset 20
        mock_repo.list_books.assert_called_once_with(
            limit=20,
            offset=20,
            search_query=None,
            sort_by="timestamp",
            sort_order="desc",
        )
        mock_repo.count_books.assert_called_once_with(search_query=None)
        assert books == []
        assert total == 0


def test_list_books_with_search() -> None:
    """Test list_books passes search query (covers lines 87-96)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_books.return_value = []
        mock_repo.count_books.return_value = 0
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        service.list_books(search_query="test query")

        mock_repo.list_books.assert_called_once()
        assert mock_repo.list_books.call_args[1]["search_query"] == "test query"
        mock_repo.count_books.assert_called_once_with(search_query="test query")


def test_get_book_delegates_to_repo() -> None:
    """Test get_book delegates to repository (covers line 111)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_book = MagicMock()
        mock_repo.get_book.return_value = mock_book
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.get_book(123)

        assert result is mock_book
        mock_repo.get_book.assert_called_once_with(123)


def test_get_thumbnail_url_with_book_has_cover() -> None:
    """Test get_thumbnail_url returns URL when book has cover (covers lines 126-134)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=123, title="Test Book", uuid="test-uuid", has_cover=True)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book)

        assert result == "/api/books/123/cover"


def test_get_thumbnail_url_with_book_no_cover() -> None:
    """Test get_thumbnail_url returns None when book has no cover (covers lines 126-130)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=123, title="Test Book", uuid="test-uuid", has_cover=False)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book)

        assert result is None


def test_get_thumbnail_url_with_book_with_relations_has_cover() -> None:
    """Test get_thumbnail_url with BookWithRelations has cover (covers lines 126-134)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=456, title="Test Book", uuid="test-uuid", has_cover=True)
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book_with_rels)

        assert result == "/api/books/456/cover"


def test_get_thumbnail_url_with_book_with_relations_no_cover() -> None:
    """Test get_thumbnail_url with BookWithRelations no cover (covers lines 126-130)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=456, title="Test Book", uuid="test-uuid", has_cover=False)
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book_with_rels)

        assert result is None


def test_get_thumbnail_path_with_book_has_cover_exists() -> None:
    """Test get_thumbnail_path returns path when cover exists (covers lines 149-161)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )

    book = Book(
        id=123,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (123)",
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=True) as mock_exists,
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book)

        assert result is not None
        assert str(result).endswith("cover.jpg")
        mock_exists.assert_called_once()


def test_get_thumbnail_path_with_book_no_cover() -> None:
    """Test get_thumbnail_path returns None when book has no cover (covers lines 149-152)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=123, title="Test Book", uuid="test-uuid", has_cover=False)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_path(book)

        assert result is None


def test_get_thumbnail_path_with_book_cover_not_exists() -> None:
    """Test get_thumbnail_path returns None when cover file doesn't exist (covers lines 149-161)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )

    book = Book(
        id=123,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (123)",
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=False) as mock_exists,
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book)

        assert result is None
        mock_exists.assert_called_once()


def test_get_thumbnail_path_with_book_with_relations() -> None:
    """Test get_thumbnail_path with BookWithRelations (covers lines 149-161)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )

    book = Book(
        id=456,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (456)",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=True),
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book_with_rels)

        assert result is not None
        assert str(result).endswith("cover.jpg")
