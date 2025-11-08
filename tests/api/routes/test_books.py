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

"""Tests for book routes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import fundamental.api.routes.books as books
from fundamental.models.config import Library
from fundamental.models.core import Book
from fundamental.repositories.calibre_book_repository import BookWithRelations
from tests.conftest import DummySession


class MockBookService:
    """Mock BookService for testing."""

    def __init__(
        self,
        *,
        list_books_result: tuple[list[BookWithRelations], int] | None = None,
        get_book_result: BookWithRelations | None = None,
        get_thumbnail_url_result: str | None = None,
        get_thumbnail_path_result: Path | None = None,
    ) -> None:
        self._list_books_result = list_books_result or ([], 0)
        self._get_book_result = get_book_result
        self._get_thumbnail_url_result = get_thumbnail_url_result
        self._get_thumbnail_path_result = get_thumbnail_path_result

    def list_books(
        self,
        page: int = 1,
        page_size: int = 20,
        search_query: str | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> tuple[list[BookWithRelations], int]:
        """Mock list_books method."""
        return self._list_books_result

    def get_book(self, book_id: int) -> BookWithRelations | None:
        """Mock get_book method."""
        return self._get_book_result

    def get_thumbnail_url(self, book: Book | BookWithRelations) -> str | None:
        """Mock get_thumbnail_url method."""
        return self._get_thumbnail_url_result

    def get_thumbnail_path(self, book: Book | BookWithRelations) -> Path | None:
        """Mock get_thumbnail_path method."""
        return self._get_thumbnail_path_result


def test_get_active_library_service_no_active_library() -> None:
    """Test _get_active_library_service raises 404 when no active library."""
    session = DummySession()

    with (
        patch("fundamental.api.routes.books.LibraryRepository") as mock_repo_class,
        patch("fundamental.api.routes.books.LibraryService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            books._get_active_library_service(session)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "no_active_library"


def test_get_active_library_service_success() -> None:
    """Test _get_active_library_service returns BookService when library exists."""
    session = DummySession()
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    with (
        patch("fundamental.api.routes.books.LibraryRepository") as mock_repo_class,
        patch("fundamental.api.routes.books.LibraryService") as mock_service_class,
        patch("fundamental.api.routes.books.BookService") as mock_book_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_service_class.return_value = mock_service
        mock_book_service = MagicMock()
        mock_book_service_class.return_value = mock_book_service

        result = books._get_active_library_service(session)
        assert result == mock_book_service
        mock_book_service_class.assert_called_once_with(library)


def test_list_books_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_books succeeds with valid parameters."""
    session = DummySession()
    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithRelations(
        book=book,
        authors=["Test Author"],
        series=None,
    )

    mock_service = MockBookService(
        list_books_result=([book_with_rels], 1),
        get_thumbnail_url_result="/api/books/1/cover",
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.list_books(session, page=1, page_size=20)
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == 1
    assert result.items[0].title == "Test Book"


def test_list_books_pagination_adjustments(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_books adjusts invalid pagination parameters."""
    session = DummySession()

    mock_service = MockBookService(list_books_result=([], 0))

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    # Test page < 1
    result = books.list_books(session, page=0, page_size=20)
    assert result.page == 1

    # Test page_size < 1
    result = books.list_books(session, page=1, page_size=0)
    assert result.page_size == 20

    # Test page_size > 100
    result = books.list_books(session, page=1, page_size=200)
    assert result.page_size == 100


def test_list_books_skips_books_without_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_books skips books without ID."""
    session = DummySession()

    book_no_id = Book(
        id=None,
        title="Book Without ID",
        author_sort="Author",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=False,
        path="test/path",
    )
    book_with_id = Book(
        id=2,
        title="Book With ID",
        author_sort="Author",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=False,
        path="test/path",
    )

    book_with_rels_no_id = BookWithRelations(book=book_no_id, authors=[], series=None)
    book_with_rels_with_id = BookWithRelations(
        book=book_with_id, authors=[], series=None
    )

    mock_service = MockBookService(
        list_books_result=([book_with_rels_no_id, book_with_rels_with_id], 2),
        get_thumbnail_url_result=None,
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.list_books(session, page=1, page_size=20)
    # Should only include book with ID
    assert len(result.items) == 1
    assert result.items[0].id == 2


def test_get_book_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book succeeds with valid book."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithRelations(
        book=book,
        authors=["Test Author"],
        series=None,
    )

    mock_service = MockBookService(
        get_book_result=book_with_rels,
        get_thumbnail_url_result="/api/books/1/cover",
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.get_book(session, book_id=1)
    assert result.id == 1
    assert result.title == "Test Book"


def test_get_book_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book raises 404 when book not found."""
    session = DummySession()

    mock_service = MockBookService(get_book_result=None)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books.get_book(session, book_id=999)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_get_book_missing_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book raises 500 when book has no ID."""
    session = DummySession()

    book = Book(
        id=None,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=False,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    mock_service = MockBookService(get_book_result=book_with_rels)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books.get_book(session, book_id=1)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "book_missing_id"


def test_get_book_cover_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_cover succeeds with valid cover."""
    from fastapi.responses import FileResponse

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    cover_path = Path("/tmp/test_cover.jpg")
    cover_path.touch()  # Create the file

    try:
        mock_service = MockBookService(
            get_book_result=book_with_rels,
            get_thumbnail_path_result=cover_path,
        )

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )

        result = books.get_book_cover(session, book_id=1)
        assert isinstance(result, FileResponse)
        assert result.path == str(cover_path)
    finally:
        cover_path.unlink(missing_ok=True)


def test_get_book_cover_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_cover raises 404 when book not found."""
    session = DummySession()

    mock_service = MockBookService(get_book_result=None)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books.get_book_cover(session, book_id=999)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_get_book_cover_file_not_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_cover returns 404 when cover file doesn't exist."""
    from fastapi import Response

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    # Path that doesn't exist
    non_existent_path = Path("/nonexistent/cover.jpg")

    mock_service = MockBookService(
        get_book_result=book_with_rels,
        get_thumbnail_path_result=non_existent_path,
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.get_book_cover(session, book_id=1)
    assert isinstance(result, Response)
    assert result.status_code == 404
