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

"""Tests for book routes."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import fundamental.api.routes.books as books
from fundamental.models.config import Library
from fundamental.models.core import Book
from fundamental.repositories import BookWithFullRelations, BookWithRelations
from tests.conftest import DummySession


class MockBookService:
    """Mock BookService for testing."""

    def __init__(
        self,
        *,
        list_books_result: tuple[list[BookWithRelations | BookWithFullRelations], int]
        | None = None,
        get_book_result: BookWithRelations | None = None,
        get_book_full_result: BookWithFullRelations | None = None,
        get_thumbnail_url_result: str | None = None,
        get_thumbnail_path_result: Path | None = None,
        search_suggestions_result: dict[str, list[dict[str, str | int]]] | None = None,
        filter_suggestions_result: list[dict[str, str | int]] | None = None,
        list_books_with_filters_result: tuple[
            list[BookWithRelations | BookWithFullRelations], int
        ]
        | None = None,
        update_book_result: BookWithFullRelations | None = None,
    ) -> None:
        # Allow dynamic assignment of methods for testing
        self.delete_book: object | None = None
        self.add_book: object | None = None
        self._list_books_result = list_books_result or ([], 0)
        self._get_book_result = get_book_result
        self._get_book_full_result = get_book_full_result
        self._get_thumbnail_url_result = get_thumbnail_url_result
        self._get_thumbnail_path_result = get_thumbnail_path_result
        self._search_suggestions_result = search_suggestions_result or {
            "books": [],
            "authors": [],
            "tags": [],
            "series": [],
        }
        self._filter_suggestions_result = filter_suggestions_result or []
        self._list_books_with_filters_result = list_books_with_filters_result or ([], 0)
        self._update_book_result = update_book_result

    def list_books(
        self,
        page: int = 1,
        page_size: int = 20,
        search_query: str | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
    ) -> tuple[list[BookWithRelations | BookWithFullRelations], int]:
        """Mock list_books method."""
        return self._list_books_result

    def get_book(self, book_id: int) -> BookWithRelations | None:
        """Mock get_book method."""
        return self._get_book_result

    def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
        """Mock get_book_full method."""
        return self._get_book_full_result

    def get_thumbnail_url(
        self, book: Book | BookWithRelations | BookWithFullRelations
    ) -> str | None:
        """Mock get_thumbnail_url method."""
        return self._get_thumbnail_url_result

    def get_thumbnail_path(
        self, book: Book | BookWithRelations | BookWithFullRelations
    ) -> Path | None:
        """Mock get_thumbnail_path method."""
        return self._get_thumbnail_path_result

    def search_suggestions(
        self,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Mock search_suggestions method."""
        return self._search_suggestions_result

    def filter_suggestions(
        self,
        query: str,
        filter_type: str,
        limit: int = 10,
    ) -> list[dict[str, str | int]]:
        """Mock filter_suggestions method."""
        return self._filter_suggestions_result

    def list_books_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        author_ids: list[int] | None = None,
        title_ids: list[int] | None = None,
        genre_ids: list[int] | None = None,
        publisher_ids: list[int] | None = None,
        identifier_ids: list[int] | None = None,
        series_ids: list[int] | None = None,
        formats: list[str] | None = None,
        rating_ids: list[int] | None = None,
        language_ids: list[int] | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
    ) -> tuple[list[BookWithRelations | BookWithFullRelations], int]:
        """Mock list_books_with_filters method."""
        return self._list_books_with_filters_result

    def update_book(
        self,
        book_id: int,
        title: str | None = None,
        pubdate: object | None = None,
        author_names: list[str] | None = None,
        series_name: str | None = None,
        series_id: int | None = None,
        series_index: float | None = None,
        tag_names: list[str] | None = None,
        identifiers: list[dict[str, str]] | None = None,
        description: str | None = None,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> BookWithFullRelations | None:
        """Mock update_book method."""
        return self._update_book_result


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
        mock_book_service_class.assert_called_once_with(library, session=session)


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


def test_list_books_with_full_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_books with full=True returns full details (covers lines 263-276)."""
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
    book_with_full_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
        series="Test Series",
        series_id=1,
        tags=["Fiction", "Adventure"],
        identifiers=[{"type": "isbn", "val": "1234567890"}],
        description="Test description",
        publisher="Test Publisher",
        publisher_id=1,
        languages=["en"],
        language_ids=[1],
        rating=5,
        rating_id=1,
        formats=[],
    )

    mock_service = MockBookService(
        list_books_result=([book_with_full_rels], 1),
        get_thumbnail_url_result="/api/books/1/cover",
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.list_books(session, page=1, page_size=20, full=True)
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == 1
    assert result.items[0].title == "Test Book"
    assert result.items[0].tags == ["Fiction", "Adventure"]
    assert result.items[0].identifiers == [{"type": "isbn", "val": "1234567890"}]
    assert result.items[0].description == "Test description"
    assert result.items[0].publisher == "Test Publisher"
    assert result.items[0].publisher_id == 1
    assert result.items[0].languages == ["en"]
    assert result.items[0].language_ids == [1]
    assert result.items[0].rating == 5
    assert result.items[0].rating_id == 1
    assert result.items[0].series_id == 1
    assert result.items[0].formats == []


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


def test_search_suggestions_empty_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test search_suggestions returns empty response for empty query (covers lines 301-313)."""
    session = DummySession()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.search_suggestions(session, q="")
    assert result.books == []
    assert result.authors == []
    assert result.tags == []
    assert result.series == []


def test_search_suggestions_whitespace_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test search_suggestions returns empty response for whitespace-only query (covers lines 301-313)."""
    session = DummySession()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.search_suggestions(session, q="   ")
    assert result.books == []
    assert result.authors == []
    assert result.tags == []
    assert result.series == []


def test_search_suggestions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test search_suggestions succeeds with valid query (covers lines 301-313)."""
    session = DummySession()

    mock_service = MockBookService(
        search_suggestions_result={
            "books": [{"id": 1, "name": "Book 1"}],
            "authors": [{"id": 1, "name": "Author 1"}],
            "tags": [{"id": 1, "name": "Tag 1"}],
            "series": [{"id": 1, "name": "Series 1"}],
        }
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.search_suggestions(session, q="test")
    assert len(result.books) == 1
    assert len(result.authors) == 1
    assert len(result.tags) == 1
    assert len(result.series) == 1
    assert result.books[0].id == 1
    assert result.books[0].name == "Book 1"


def test_filter_suggestions_empty_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_suggestions returns empty response for empty query (covers lines 364-374)."""
    session = DummySession()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.filter_suggestions(session, q="", filter_type="author")
    assert result.suggestions == []


def test_filter_suggestions_whitespace_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_suggestions returns empty response for whitespace-only query (covers lines 364-374)."""
    session = DummySession()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.filter_suggestions(session, q="   ", filter_type="author")
    assert result.suggestions == []


def test_filter_suggestions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_suggestions succeeds with valid query (covers lines 364-374)."""
    session = DummySession()

    mock_service = MockBookService(
        filter_suggestions_result=[
            {"id": 1, "name": "Author 1"},
            {"id": 2, "name": "Author 2"},
        ]
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.filter_suggestions(
        session, q="author", filter_type="author", limit=10
    )
    assert len(result.suggestions) == 2
    assert result.suggestions[0].id == 1
    assert result.suggestions[0].name == "Author 1"


def test_filter_books_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_books succeeds with valid filters (covers lines 422-472)."""
    from fundamental.api.schemas import BookFilterRequest

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
        list_books_with_filters_result=([book_with_rels], 1),
        get_thumbnail_url_result="/api/books/1/cover",
    )
    # Use setattr to allow dynamic assignment for assertion testing
    mock_service.list_books_with_filters = MagicMock(return_value=([book_with_rels], 1))  # type: ignore[method-assign]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    filter_request = BookFilterRequest(
        author_ids=[1, 2],
        title_ids=[3, 4],
        genre_ids=[5, 6],
    )

    result = books.filter_books(
        session,
        filter_request=filter_request,
        page=1,
        page_size=20,
        sort_by="timestamp",
        sort_order="desc",
    )

    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == 1
    assert result.items[0].title == "Test Book"
    # Verify the method was called (MagicMock has assert_called_once)
    list_method = mock_service.list_books_with_filters
    if hasattr(list_method, "assert_called_once"):
        list_method.assert_called_once()  # type: ignore[attr-defined]


def test_filter_books_pagination_adjustments(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_books adjusts invalid pagination parameters (covers lines 422-472)."""
    from fundamental.api.schemas import BookFilterRequest

    session = DummySession()

    mock_service = MockBookService(list_books_with_filters_result=([], 0))
    # Use setattr to allow dynamic assignment for assertion testing
    mock_service.list_books_with_filters = MagicMock(return_value=([], 0))  # type: ignore[method-assign]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    filter_request = BookFilterRequest()

    # Test page < 1
    result = books.filter_books(
        session, filter_request=filter_request, page=0, page_size=20
    )
    assert result.page == 1

    # Test page_size < 1
    result = books.filter_books(
        session, filter_request=filter_request, page=1, page_size=0
    )
    assert result.page_size == 20

    # Test page_size > 100
    result = books.filter_books(
        session, filter_request=filter_request, page=1, page_size=200
    )
    assert result.page_size == 100


def test_filter_books_skips_books_without_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_books skips books without ID (covers lines 422-472)."""
    from fundamental.api.schemas import BookFilterRequest

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
        list_books_with_filters_result=(
            [book_with_rels_no_id, book_with_rels_with_id],
            2,
        ),
        get_thumbnail_url_result=None,
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    filter_request = BookFilterRequest()

    result = books.filter_books(
        session, filter_request=filter_request, page=1, page_size=20
    )
    # Should only include book with ID
    assert len(result.items) == 1
    assert result.items[0].id == 2


def test_filter_books_with_full_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_books with full=True returns full details (covers lines 1149-1162)."""
    from fundamental.api.schemas import BookFilterRequest

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
    book_with_full_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
        series="Test Series",
        series_id=1,
        tags=["Fiction", "Adventure"],
        identifiers=[{"type": "isbn", "val": "1234567890"}],
        description="Test description",
        publisher="Test Publisher",
        publisher_id=1,
        languages=["en"],
        language_ids=[1],
        rating=5,
        rating_id=1,
        formats=[],
    )

    mock_service = MockBookService(
        list_books_with_filters_result=([book_with_full_rels], 1),
        get_thumbnail_url_result="/api/books/1/cover",
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    filter_request = BookFilterRequest(
        author_ids=[1, 2],
        title_ids=[3, 4],
        genre_ids=[5, 6],
    )

    result = books.filter_books(
        session,
        filter_request=filter_request,
        page=1,
        page_size=20,
        sort_by="timestamp",
        sort_order="desc",
        full=True,
    )

    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == 1
    assert result.items[0].title == "Test Book"
    assert result.items[0].tags == ["Fiction", "Adventure"]
    assert result.items[0].identifiers == [{"type": "isbn", "val": "1234567890"}]
    assert result.items[0].description == "Test description"
    assert result.items[0].publisher == "Test Publisher"
    assert result.items[0].publisher_id == 1
    assert result.items[0].languages == ["en"]
    assert result.items[0].language_ids == [1]
    assert result.items[0].rating == 5
    assert result.items[0].rating_id == 1
    assert result.items[0].series_id == 1
    assert result.items[0].formats == []


def test_get_book_with_full_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book with full=True returns full details (covers lines 204, 240-252)."""
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
    book_with_full_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
        series="Test Series",
        series_id=1,
        tags=["Fiction", "Adventure"],
        identifiers=[{"type": "isbn", "val": "1234567890"}],
        description="Test description",
        publisher="Test Publisher",
        publisher_id=1,
        languages=["en"],
        language_ids=[1],
        rating=5,
        rating_id=1,
        formats=[],
    )

    mock_service = MockBookService(
        get_book_full_result=book_with_full_rels,
        get_thumbnail_url_result="/api/books/1/cover",
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    result = books.get_book(session, book_id=1, full=True)
    assert result.id == 1
    assert result.title == "Test Book"
    assert result.tags == ["Fiction", "Adventure"]
    assert result.identifiers == [{"type": "isbn", "val": "1234567890"}]
    assert result.description == "Test description"
    assert result.publisher == "Test Publisher"
    assert result.publisher_id == 1
    assert result.languages == ["en"]
    assert result.language_ids == [1]
    assert result.rating == 5
    assert result.rating_id == 1
    assert result.series_id == 1


def test_get_book_with_full_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book with full=False doesn't return full details (covers line 206)."""
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

    result = books.get_book(session, book_id=1, full=False)
    assert result.id == 1
    assert result.title == "Test Book"
    assert result.tags == []
    assert result.identifiers == []
    assert result.description is None


def test_update_book_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_book succeeds with valid update (covers lines 284-329)."""
    from datetime import datetime

    from fundamental.api.schemas import BookUpdate

    session = DummySession()

    book = Book(
        id=1,
        title="Updated Book",
        author_sort="Author, Test",
        pubdate=datetime(2024, 1, 1, tzinfo=UTC),
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        series_index=1.5,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    updated_book = BookWithFullRelations(
        book=book,
        authors=["Updated Author"],
        series="Updated Series",
        series_id=2,
        tags=["Updated Tag"],
        identifiers=[{"type": "isbn", "val": "0987654321"}],
        description="Updated description",
        publisher="Updated Publisher",
        publisher_id=2,
        languages=["fr"],
        language_ids=[2],
        rating=4,
        rating_id=2,
        formats=[],
    )

    existing_book = BookWithRelations(
        book=Book(id=1, title="Original Book", uuid="test-uuid"),
        authors=[],
        series=None,
    )

    mock_service = MockBookService(
        get_book_result=existing_book,
        update_book_result=updated_book,
        get_thumbnail_url_result="/api/books/1/cover",
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    update = BookUpdate(
        title="Updated Book",
        author_names=["Updated Author"],
        series_name="Updated Series",
        series_index=1.5,
        tag_names=["Updated Tag"],
        identifiers=[{"type": "isbn", "val": "0987654321"}],
        description="Updated description",
        publisher_name="Updated Publisher",
        language_codes=["fr"],
        rating_value=4,
    )

    result = books.update_book(session, book_id=1, update=update)
    assert result.id == 1
    assert result.title == "Updated Book"
    assert result.authors == ["Updated Author"]
    assert result.series == "Updated Series"
    assert result.series_id == 2
    assert result.series_index == 1.5
    assert result.tags == ["Updated Tag"]
    assert result.identifiers == [{"type": "isbn", "val": "0987654321"}]
    assert result.description == "Updated description"
    assert result.publisher == "Updated Publisher"
    assert result.publisher_id == 2
    assert result.languages == ["fr"]
    assert result.language_ids == [2]
    assert result.rating == 4
    assert result.rating_id == 2


def test_update_book_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_book raises 404 when book not found (covers lines 286-292)."""
    from fundamental.api.schemas import BookUpdate

    session = DummySession()

    mock_service = MockBookService(get_book_result=None)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    update = BookUpdate(title="Updated Book")

    with pytest.raises(HTTPException) as exc_info:
        books.update_book(session, book_id=999, update=update)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_update_book_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_book raises 404 when update returns None (covers lines 314-318)."""
    from fundamental.api.schemas import BookUpdate

    session = DummySession()

    existing_book = BookWithRelations(
        book=Book(id=1, title="Original Book", uuid="test-uuid"),
        authors=[],
        series=None,
    )

    mock_service = MockBookService(
        get_book_result=existing_book,
        update_book_result=None,
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    update = BookUpdate(title="Updated Book")

    with pytest.raises(HTTPException) as exc_info:
        books.update_book(session, book_id=1, update=update)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_update_book_missing_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_book raises 500 when book has no ID (covers lines 320-325)."""
    from fundamental.api.schemas import BookUpdate

    session = DummySession()

    existing_book = BookWithRelations(
        book=Book(id=1, title="Original Book", uuid="test-uuid"),
        authors=[],
        series=None,
    )

    book_no_id = Book(
        id=None,
        title="Updated Book",
        uuid="test-uuid",
    )
    updated_book = BookWithFullRelations(
        book=book_no_id,
        authors=[],
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
        formats=[],
    )

    mock_service = MockBookService(
        get_book_result=existing_book,
        update_book_result=updated_book,
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    update = BookUpdate(title="Updated Book")

    with pytest.raises(HTTPException) as exc_info:
        books.update_book(session, book_id=1, update=update)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "book_missing_id"


def test_delete_book_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book succeeds (covers lines 482-489)."""
    session = DummySession()

    mock_service = MockBookService()
    mock_service.delete_book = MagicMock(return_value=None)  # type: ignore[assignment]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    delete_request = books.BookDeleteRequest(delete_files_from_drive=True)
    result = books.delete_book(session, book_id=1, delete_request=delete_request)
    assert result is None
    mock_service.delete_book.assert_called_once_with(
        book_id=1, delete_files_from_drive=True
    )


def test_delete_book_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book raises 404 when book not found (covers lines 489-495)."""
    session = DummySession()

    mock_service = MockBookService()
    mock_service.delete_book = MagicMock(side_effect=ValueError("book_not_found"))  # type: ignore[assignment]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    delete_request = books.BookDeleteRequest(delete_files_from_drive=False)

    with pytest.raises(HTTPException) as exc_info:
        books.delete_book(session, book_id=999, delete_request=delete_request)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_delete_book_other_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book raises 500 for other ValueError (covers lines 496-499)."""
    session = DummySession()

    mock_service = MockBookService()
    # Use a ValueError that's not "book_not_found" to trigger the else branch
    mock_service.delete_book = MagicMock(side_effect=ValueError("other_error"))  # type: ignore[assignment]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    delete_request = books.BookDeleteRequest(delete_files_from_drive=False)

    with pytest.raises(HTTPException) as exc_info:
        books.delete_book(session, book_id=1, delete_request=delete_request)
    # This should execute line 496-499 (the else branch for ValueError)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "other_error"


def test_delete_book_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book handles OSError (covers lines 500-504)."""
    session = DummySession()

    mock_service = MockBookService()
    mock_service.delete_book = MagicMock(side_effect=OSError("Permission denied"))  # type: ignore[assignment]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    delete_request = books.BookDeleteRequest(delete_files_from_drive=True)

    with pytest.raises(HTTPException) as exc_info:
        books.delete_book(session, book_id=1, delete_request=delete_request)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "Failed to delete files from filesystem" in exc_info.value.detail


def test_upload_book_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_book succeeds (covers lines 1174-1218)."""
    import tempfile
    from pathlib import Path
    from unittest.mock import MagicMock

    session = DummySession()

    mock_service = MockBookService()
    mock_service.add_book = MagicMock(return_value=1)  # type: ignore[assignment]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    # Create a real temporary file to test the actual code path
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".epub", prefix="calibre_upload_"
    ) as temp_file:
        temp_path = Path(temp_file.name)
        temp_path.write_bytes(b"fake epub content")

        mock_file = MagicMock()
        mock_file.filename = "test.epub"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = b"fake epub content"

        try:
            # This should execute lines 1174-1218
            result = books.upload_book(session, file=mock_file)
            assert result.book_id == 1
        finally:
            # Clean up
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)


def test_upload_book_no_extension(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_book raises 400 when file has no extension (covers lines 1177-1182)."""
    from unittest.mock import MagicMock

    session = DummySession()

    mock_service = MockBookService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_file = MagicMock()
    mock_file.filename = "test"  # No extension

    with pytest.raises(HTTPException) as exc_info:
        books.upload_book(session, file=mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "file_extension_required"


def test_upload_book_save_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_book handles file save error (covers lines 1195-1200)."""
    from unittest.mock import MagicMock

    session = DummySession()

    mock_service = MockBookService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_file = MagicMock()
    mock_file.filename = "test.epub"
    mock_file.file = MagicMock()
    mock_file.file.read.side_effect = OSError("Read error")

    with patch("tempfile.NamedTemporaryFile") as mock_temp:
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_upload.epub"
        mock_temp_file.__enter__.return_value = mock_temp_file
        mock_temp.return_value = mock_temp_file

        with patch("pathlib.Path.unlink"):
            with pytest.raises(HTTPException) as exc_info:
                books.upload_book(session, file=mock_file)
            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == 500
            assert "failed_to_save_file" in exc_info.value.detail
