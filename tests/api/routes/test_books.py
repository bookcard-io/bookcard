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

import bookcard.api.routes.books as books
from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.models.core import Book
from bookcard.repositories import BookWithFullRelations, BookWithRelations
from tests.conftest import DummySession


def _create_mock_user() -> User:
    """Create a mock user for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


def _setup_route_mocks(
    monkeypatch: pytest.MonkeyPatch,
    session: DummySession,
    mock_service: MockBookService,
) -> tuple[MockPermissionHelper, MockResponseBuilder]:
    """Set up mocks for route dependencies.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Monkeypatch fixture.
    session : DummySession
        Dummy session.
    mock_service : MockBookService
        Mock book service.

    Returns
    -------
    tuple[MockPermissionHelper, MockResponseBuilder]
        Tuple of (permission_helper, response_builder).
    """

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper = MockPermissionHelper(session)
    mock_response_builder = MockResponseBuilder(mock_service)

    return mock_permission_helper, mock_response_builder


def _mock_permission_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock PermissionService to allow all permissions."""

    class MockPermissionService:
        def __init__(self, session: object) -> None:
            pass  # Accept session but don't use it

        def has_permission(
            self,
            user: User,
            resource: str,
            action: str,
            context: dict[str, object] | None = None,
        ) -> bool:
            return True

        def check_permission(
            self,
            user: User,
            resource: str,
            action: str,
            context: dict[str, object] | None = None,
        ) -> None:
            pass  # Always allow

    # Patch PermissionService in the permission_service module where it's actually used
    monkeypatch.setattr(
        "bookcard.services.permission_service.PermissionService",
        MockPermissionService,
    )


class MockPermissionHelper:
    """Mock BookPermissionHelper for testing."""

    def __init__(self, session: object) -> None:
        """Initialize mock permission helper."""

    def check_read_permission(
        self,
        user: User,
        book_with_rels: object | None = None,
    ) -> None:
        """Mock check_read_permission - always allows."""

    def check_write_permission(
        self,
        user: User,
        book_with_rels: object | None = None,
    ) -> None:
        """Mock check_write_permission - always allows."""

    def check_create_permission(self, user: User) -> None:
        """Mock check_create_permission - always allows."""

    def check_send_permission(
        self,
        user: User,
        book_with_rels: object | None = None,
        book_id: int | None = None,
        session: object | None = None,
    ) -> None:
        """Mock check_send_permission - always allows."""


class MockResponseBuilder:
    """Mock BookResponseBuilder for testing."""

    def __init__(self, book_service: object) -> None:
        """Initialize mock response builder."""
        self._book_service = book_service

    def build_book_read(
        self,
        book_with_rels: BookWithRelations | BookWithFullRelations,
        full: bool = False,
    ) -> object:
        """Mock build_book_read method."""
        from bookcard.api.schemas import BookRead

        book = book_with_rels.book
        if book.id is None:
            raise ValueError("book_missing_id")

        thumbnail_url = None
        if hasattr(self._book_service, "get_thumbnail_url"):
            thumbnail_url = self._book_service.get_thumbnail_url(book_with_rels)  # type: ignore[call-arg]

        book_read = BookRead(
            id=book.id,
            title=book.title,
            authors=book_with_rels.authors,
            author_sort=book.author_sort,
            title_sort=book.sort,
            pubdate=book.pubdate,
            timestamp=book.timestamp,
            series=book_with_rels.series,
            series_index=book.series_index,
            isbn=book.isbn,
            uuid=book.uuid or "",
            thumbnail_url=thumbnail_url,
            has_cover=book.has_cover,
        )

        if full and isinstance(book_with_rels, BookWithFullRelations):
            book_read.tags = book_with_rels.tags
            book_read.identifiers = book_with_rels.identifiers
            book_read.description = book_with_rels.description
            book_read.publisher = book_with_rels.publisher
            book_read.publisher_id = book_with_rels.publisher_id
            book_read.languages = book_with_rels.languages
            book_read.language_ids = book_with_rels.language_ids
            book_read.rating = book_with_rels.rating
            book_read.rating_id = book_with_rels.rating_id
            book_read.series_id = book_with_rels.series_id
            book_read.formats = getattr(book_with_rels, "formats", [])

        return book_read

    def build_book_read_list(
        self,
        books: list[BookWithRelations | BookWithFullRelations],
        full: bool = False,
    ) -> list[object]:
        """Mock build_book_read_list method."""
        return [
            self.build_book_read(book_with_rels, full=full)
            for book_with_rels in books
            if book_with_rels.book.id is not None
        ]


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
        author_id: int | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
        pubdate_month: int | None = None,
        pubdate_day: int | None = None,
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
        isbn: str | None = None,
        tag_names: list[str] | None = None,
        identifiers: list[dict[str, str]] | None = None,
        description: str | None = None,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
        rating_value: int | None = None,
        rating_id: int | None = None,
        author_sort: str | None = None,
        title_sort: str | None = None,
    ) -> BookWithFullRelations | None:
        """Mock update_book method."""
        return self._update_book_result


def test_get_active_library_service_no_active_library() -> None:
    """Test _get_active_library_service raises 404 when no active library."""
    session = DummySession()

    with patch("bookcard.api.routes.books._resolve_active_library") as mock_resolve:
        mock_resolve.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            books._get_active_library_service(session, current_user=None)  # type: ignore[invalid-argument-type]
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
        patch("bookcard.api.routes.books._resolve_active_library") as mock_resolve,
        patch("bookcard.api.routes.books.BookService") as mock_book_service_class,
    ):
        mock_resolve.return_value = library
        mock_book_service = MagicMock()
        mock_book_service_class.return_value = mock_book_service

        result = books._get_active_library_service(session, current_user=None)  # type: ignore[invalid-argument-type]
        assert result == mock_book_service
        mock_book_service_class.assert_called_once_with(library, session=session)


def test_list_books_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_books succeeds with valid parameters."""
    session = DummySession()
    current_user = _create_mock_user()
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
        formats=[],
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
    _mock_permission_service(monkeypatch)

    mock_permission_helper = MockPermissionHelper(session)
    mock_response_builder = MockResponseBuilder(mock_service)

    result = books.list_books(
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=1,
        page_size=20,
    )
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == 1
    assert result.items[0].title == "Test Book"


def test_list_books_pagination_adjustments(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_books adjusts invalid pagination parameters."""
    session = DummySession()
    current_user = _create_mock_user()

    mock_service = MockBookService(list_books_result=([], 0))

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper = MockPermissionHelper(session)
    mock_response_builder = MockResponseBuilder(mock_service)

    # Test page < 1
    result = books.list_books(
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=0,
        page_size=20,
    )
    assert result.page == 1

    # Test page_size < 1
    result = books.list_books(
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=1,
        page_size=0,
    )
    assert result.page_size == 20

    # Test page_size > 100
    result = books.list_books(
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=1,
        page_size=200,
    )
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

    book_with_rels_no_id = BookWithRelations(
        book=book_no_id, authors=[], series=None, formats=[]
    )
    book_with_rels_with_id = BookWithRelations(
        book=book_with_id, authors=[], series=None, formats=[]
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
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    mock_permission_helper = MockPermissionHelper(session)
    mock_response_builder = MockResponseBuilder(mock_service)

    result = books.list_books(
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=1,
        page_size=20,
    )
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

    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    mock_permission_helper = MockPermissionHelper(session)
    mock_response_builder = MockResponseBuilder(mock_service)

    result = books.list_books(
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=1,
        page_size=20,
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
        formats=[],
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

    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = books.get_book(
        current_user=current_user,
        book_id=1,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
    )
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

    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books.get_book(
            current_user=current_user,
            book_id=999,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            response_builder=mock_response_builder,
            session=session,
            library_id=1,
        )
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
    book_with_rels = BookWithRelations(book=book, authors=[], series=None, formats=[])

    mock_service = MockBookService(get_book_result=book_with_rels)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books.get_book(
            current_user=current_user,
            book_id=1,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            response_builder=mock_response_builder,
            session=session,
            library_id=1,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "book_missing_id"


def test_get_book_cover_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_cover succeeds with valid cover."""
    from fastapi.responses import FileResponse

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

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
    book_with_rels = BookWithRelations(book=book, authors=[], series=None, formats=[])

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cover_path = Path(tmpdir) / "test_cover.jpg"
        cover_path.touch()  # Create the file

        mock_service = MockBookService(
            get_book_result=book_with_rels,
            get_thumbnail_path_result=cover_path,
        )

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        result = books.get_book_cover(
            current_user=current_user,
            book_id=1,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
        assert isinstance(result, FileResponse)
        assert result.path == str(cover_path)


def test_get_book_cover_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_cover raises 404 when book not found."""
    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    mock_service = MockBookService(get_book_result=None)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.get_book_cover(
            current_user=current_user,
            book_id=999,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_get_book_cover_file_not_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_cover returns 404 when cover file doesn't exist."""
    from fastapi import Response

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

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
    book_with_rels = BookWithRelations(book=book, authors=[], series=None, formats=[])

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

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.get_book_cover(
        current_user=current_user,
        book_id=1,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )

    assert isinstance(result, Response)
    assert result.status_code == 404


def test_search_suggestions_empty_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test search_suggestions returns empty response for empty query (covers lines 301-313)."""
    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_service = MockBookService()
    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.search_suggestions(
        current_user=current_user,
        q="",
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )
    assert result.books == []
    assert result.authors == []
    assert result.tags == []
    assert result.series == []


def test_search_suggestions_whitespace_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test search_suggestions returns empty response for whitespace-only query (covers lines 301-313)."""
    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_service = MockBookService()
    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.search_suggestions(
        current_user=current_user,
        q="   ",
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )
    assert result.books == []
    assert result.authors == []
    assert result.tags == []
    assert result.series == []


def test_search_suggestions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test search_suggestions succeeds with valid query (covers lines 301-313)."""
    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    mock_service = MockBookService(
        search_suggestions_result={
            "books": [{"id": 1, "name": "Book 1"}],
            "authors": [{"id": 1, "name": "Author 1"}],
            "tags": [{"id": 1, "name": "Tag 1"}],
            "series": [{"id": 1, "name": "Series 1"}],
        }
    )

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.search_suggestions(
        current_user=current_user,
        q="test",
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )
    assert len(result.books) == 1
    assert len(result.authors) == 1
    assert len(result.tags) == 1
    assert len(result.series) == 1
    assert result.books[0].id == 1
    assert result.books[0].name == "Book 1"


def test_filter_suggestions_empty_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_suggestions returns empty response for empty query (covers lines 364-374)."""
    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_service = MockBookService()
    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.filter_suggestions(
        current_user=current_user,
        q="",
        filter_type="author",
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )
    assert result.suggestions == []


def test_filter_suggestions_whitespace_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_suggestions returns empty response for whitespace-only query (covers lines 364-374)."""
    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_service = MockBookService()
    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.filter_suggestions(
        current_user=current_user,
        q="   ",
        filter_type="author",
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )
    assert result.suggestions == []


def test_filter_suggestions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_suggestions succeeds with valid query (covers lines 364-374)."""
    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

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

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.filter_suggestions(
        current_user=current_user,
        q="author",
        filter_type="author",
        limit=10,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )
    assert len(result.suggestions) == 2
    assert result.suggestions[0].id == 1
    assert result.suggestions[0].name == "Author 1"


def test_filter_books_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_books succeeds with valid filters (covers lines 422-472)."""
    from bookcard.api.schemas import BookFilterRequest

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

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
        formats=[],
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

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = books.filter_books(
        current_user=current_user,
        filter_request=filter_request,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
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
    from bookcard.api.schemas import BookFilterRequest

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    mock_service = MockBookService(list_books_with_filters_result=([], 0))
    # Use setattr to allow dynamic assignment for assertion testing
    mock_service.list_books_with_filters = MagicMock(return_value=([], 0))  # type: ignore[method-assign]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    filter_request = BookFilterRequest()

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    # Test page < 1
    result = books.filter_books(
        current_user=current_user,
        filter_request=filter_request,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=0,
        page_size=20,
    )
    assert result.page == 1

    # Test page_size < 1
    result = books.filter_books(
        current_user=current_user,
        filter_request=filter_request,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=1,
        page_size=0,
    )
    assert result.page_size == 20

    # Test page_size > 100
    result = books.filter_books(
        current_user=current_user,
        filter_request=filter_request,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=1,
        page_size=200,
    )
    assert result.page_size == 100


def test_filter_books_skips_books_without_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_books skips books without ID (covers lines 422-472)."""
    from bookcard.api.schemas import BookFilterRequest

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

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

    book_with_rels_no_id = BookWithRelations(
        book=book_no_id, authors=[], series=None, formats=[]
    )
    book_with_rels_with_id = BookWithRelations(
        book=book_with_id, authors=[], series=None, formats=[]
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

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = books.filter_books(
        current_user=current_user,
        filter_request=filter_request,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        page=1,
        page_size=20,
    )
    # Should only include book with ID
    assert len(result.items) == 1
    assert result.items[0].id == 2


def test_filter_books_with_full_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test filter_books with full=True returns full details (covers lines 1149-1162)."""
    from bookcard.api.schemas import BookFilterRequest

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

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

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = books.filter_books(
        current_user=current_user,
        filter_request=filter_request,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
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

    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = books.get_book(
        current_user=current_user,
        book_id=1,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        full=True,
    )
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
        formats=[],
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

    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = books.get_book(
        current_user=current_user,
        book_id=1,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
        library_id=1,
        full=False,
    )
    assert result.id == 1
    assert result.title == "Test Book"
    assert result.tags == []
    assert result.identifiers == []
    assert result.description is None


def test_update_book_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_book succeeds with valid update (covers lines 284-329)."""
    from datetime import datetime

    from bookcard.api.schemas import BookUpdate

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
        formats=[],
    )
    existing_book_full = BookWithFullRelations(
        book=Book(id=1, title="Original Book", uuid="test-uuid"),
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
        get_book_full_result=existing_book_full,
        update_book_result=updated_book,
        get_thumbnail_url_result="/api/books/1/cover",
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

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

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = books.update_book(
        current_user=current_user,
        book_id=1,
        update=update,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        response_builder=mock_response_builder,
        session=session,
    )
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
    from bookcard.api.schemas import BookUpdate

    session = DummySession()

    mock_service = MockBookService(get_book_result=None)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    update = BookUpdate(title="Updated Book")

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books.update_book(
            current_user=current_user,
            book_id=999,
            update=update,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            response_builder=mock_response_builder,
            session=session,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_update_book_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_book raises 404 when update returns None (covers lines 314-318)."""
    from bookcard.api.schemas import BookUpdate

    session = DummySession()

    existing_book = BookWithRelations(
        book=Book(id=1, title="Original Book", uuid="test-uuid"),
        authors=[],
        series=None,
        formats=[],
    )
    existing_book_full = BookWithFullRelations(
        book=Book(id=1, title="Original Book", uuid="test-uuid"),
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
        get_book_full_result=existing_book_full,
        update_book_result=None,
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    update = BookUpdate(title="Updated Book")

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books.update_book(
            current_user=current_user,
            book_id=1,
            update=update,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            response_builder=mock_response_builder,
            session=session,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_update_book_missing_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_book raises 500 when book has no ID (covers lines 320-325)."""
    from bookcard.api.schemas import BookUpdate

    session = DummySession()

    existing_book = BookWithRelations(
        book=Book(id=1, title="Original Book", uuid="test-uuid"),
        authors=[],
        series=None,
        formats=[],
    )
    existing_book_full = BookWithFullRelations(
        book=Book(id=1, title="Original Book", uuid="test-uuid"),
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
        get_book_full_result=existing_book_full,
        update_book_result=updated_book,
    )

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    update = BookUpdate(title="Updated Book")

    mock_permission_helper, mock_response_builder = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books.update_book(
            current_user=current_user,
            book_id=1,
            update=update,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            response_builder=mock_response_builder,
            session=session,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "book_missing_id"


def test_delete_book_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book succeeds (covers lines 482-489)."""
    session = DummySession()

    existing_book_full = BookWithFullRelations(
        book=Book(id=1, title="Test Book", uuid="test-uuid"),
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

    mock_service = MockBookService(get_book_full_result=existing_book_full)
    mock_service.delete_book = MagicMock(return_value=None)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    delete_request = books.BookDeleteRequest(delete_files_from_drive=True)
    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.delete_book(
        current_user=current_user,
        book_id=1,
        delete_request=delete_request,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )
    assert result is None
    mock_service.delete_book.assert_called_once_with(
        book_id=1, delete_files_from_drive=True
    )


def test_delete_book_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book raises 404 when book not found (covers lines 489-495)."""
    session = DummySession()

    existing_book_full = BookWithFullRelations(
        book=Book(id=999, title="Test Book", uuid="test-uuid"),
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

    mock_service = MockBookService(get_book_full_result=existing_book_full)
    mock_service.delete_book = MagicMock(side_effect=ValueError("book_not_found"))

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    delete_request = books.BookDeleteRequest(delete_files_from_drive=False)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.delete_book(
            current_user=current_user,
            book_id=999,
            delete_request=delete_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_delete_book_other_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book raises 500 for other ValueError (covers lines 496-499)."""
    session = DummySession()

    existing_book_full = BookWithFullRelations(
        book=Book(id=1, title="Test Book", uuid="test-uuid"),
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

    mock_service = MockBookService(get_book_full_result=existing_book_full)
    # Use a ValueError that's not "book_not_found" to trigger the else branch
    mock_service.delete_book = MagicMock(side_effect=ValueError("other_error"))

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    delete_request = books.BookDeleteRequest(delete_files_from_drive=False)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.delete_book(
            current_user=current_user,
            book_id=1,
            delete_request=delete_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    # This should execute line 496-499 (the else branch for ValueError)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "other_error"


def test_delete_book_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book handles OSError (covers lines 500-504)."""
    session = DummySession()

    existing_book_full = BookWithFullRelations(
        book=Book(id=1, title="Test Book", uuid="test-uuid"),
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

    mock_service = MockBookService(get_book_full_result=existing_book_full)
    mock_service.delete_book = MagicMock(side_effect=OSError("Permission denied"))

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)
    current_user = _create_mock_user()

    delete_request = books.BookDeleteRequest(delete_files_from_drive=True)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.delete_book(
            current_user=current_user,
            book_id=1,
            delete_request=delete_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "Failed to delete files from filesystem" in exc_info.value.detail


def test_upload_book_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_book succeeds (covers lines 1174-1218)."""
    from unittest.mock import MagicMock

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    # Create mock request with task_runner
    mock_task_runner = MagicMock()
    mock_task_runner.enqueue.return_value = 123  # Return a task_id

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type(
                "App",
                (),
                {"state": type("State", (), {"task_runner": mock_task_runner})()},
            )()

    request = DummyRequest()

    mock_service = MockBookService()
    mock_service.add_book = MagicMock(return_value=1)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_file = MagicMock()
    mock_file.filename = "test.epub"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake epub content"

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    # This should execute lines 1174-1218
    result = books.upload_book(
        request,
        current_user=current_user,
        file=mock_file,
        permission_helper=mock_permission_helper,
        session=session,
    )
    assert result.task_id == 123
    mock_task_runner.enqueue.assert_called_once()


def test_upload_book_no_extension(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_book raises 400 when file has no extension (covers lines 1177-1182)."""
    from unittest.mock import MagicMock

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    # Create mock request with task_runner
    mock_task_runner = MagicMock()
    mock_task_runner.enqueue.return_value = 123

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type(
                "App",
                (),
                {"state": type("State", (), {"task_runner": mock_task_runner})()},
            )()

    request = DummyRequest()

    mock_service = MockBookService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    mock_file = MagicMock()
    mock_file.filename = "test"  # No extension

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.upload_book(
            request,
            current_user=current_user,
            file=mock_file,
            permission_helper=mock_permission_helper,
            session=session,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "file_extension_required"


def test_upload_book_save_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_book handles file save error (covers lines 1195-1200)."""
    from unittest.mock import MagicMock

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    # Create mock request with task_runner
    mock_task_runner = MagicMock()
    mock_task_runner.enqueue.return_value = 123

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type(
                "App",
                (),
                {"state": type("State", (), {"task_runner": mock_task_runner})()},
            )()

    request = DummyRequest()

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

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        with patch("pathlib.Path.unlink"):
            with pytest.raises(HTTPException) as exc_info:
                books.upload_book(
                    request,
                    current_user=current_user,
                    file=mock_file,
                    permission_helper=mock_permission_helper,
                    session=session,
                )
            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == 500
            assert "failed_to_save_file" in exc_info.value.detail


def test_email_config_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _email_config_service creates service with encryptor (covers lines 177-179)."""

    class DummyRequest:
        def __init__(self) -> None:
            from tests.conftest import TEST_ENCRYPTION_KEY

            class DummyConfig:
                encryption_key = TEST_ENCRYPTION_KEY

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()

    with (
        patch("bookcard.api.routes.books.EmailConfigService") as mock_service_class,
        patch("bookcard.api.routes.books.DataEncryptor") as mock_encryptor_class,
    ):
        mock_encryptor = MagicMock()
        mock_encryptor_class.return_value = mock_encryptor
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        result = books._email_config_service(request, session)  # type: ignore[arg-type]
        assert result is mock_service
        mock_encryptor_class.assert_called_once()
        mock_service_class.assert_called_once_with(session, encryptor=mock_encryptor)


def test_send_book_email_server_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test send_book raises 400 when email server not configured (covers lines 755-759)."""

    from bookcard.api.schemas.books import BookSendRequest
    from bookcard.models.auth import User

    class DummyRequest:
        def __init__(self) -> None:
            from tests.conftest import TEST_ENCRYPTION_KEY

            class DummyConfig:
                encryption_key = TEST_ENCRYPTION_KEY

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    payload = BookSendRequest(to_email="device@example.com")

    class MockEmailConfigService:
        def get_config(self, decrypt: bool) -> None:
            return None

    def mock_email_config_service(req: object, sess: object) -> MockEmailConfigService:
        return MockEmailConfigService()

    class MockBookService:
        def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
            book = Book(id=1, title="Test Book", uuid="test-uuid")
            return BookWithFullRelations(
                book=book,
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

    mock_service = MockBookService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(books, "_email_config_service", mock_email_config_service)
    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.send_book_to_device(
            request,
            session,
            book_id=1,
            current_user=user,
            send_request=payload,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "email_server_not_configured_or_disabled"


def test_send_book_email_server_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test send_book raises 400 when email server is disabled (covers line 755)."""
    from datetime import UTC, datetime

    from bookcard.api.schemas.books import BookSendRequest
    from bookcard.models.auth import User
    from bookcard.models.config import EmailServerConfig, EmailServerType

    class DummyRequest:
        def __init__(self) -> None:
            from tests.conftest import TEST_ENCRYPTION_KEY

            class DummyConfig:
                encryption_key = TEST_ENCRYPTION_KEY

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    payload = BookSendRequest(to_email="device@example.com")

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class MockEmailConfigService:
        def get_config(self, decrypt: bool) -> EmailServerConfig:
            return config

    def mock_email_config_service(req: object, sess: object) -> MockEmailConfigService:
        return MockEmailConfigService()

    class MockBookService:
        def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
            book = Book(id=1, title="Test Book", uuid="test-uuid")
            return BookWithFullRelations(
                book=book,
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

    mock_service = MockBookService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(books, "_email_config_service", mock_email_config_service)
    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.send_book_to_device(
            request,
            session,
            book_id=1,
            current_user=user,
            send_request=payload,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "email_server_not_configured_or_disabled"


def test_send_book_user_missing_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test send_book raises 500 when user missing id (covers lines 766-770)."""
    from datetime import UTC, datetime

    from bookcard.api.schemas.books import BookSendRequest
    from bookcard.models.auth import User
    from bookcard.models.config import EmailServerConfig, EmailServerType

    class DummyRequest:
        def __init__(self) -> None:
            from tests.conftest import TEST_ENCRYPTION_KEY

            class DummyConfig:
                encryption_key = TEST_ENCRYPTION_KEY

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=None,  # Missing ID
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    payload = BookSendRequest(to_email="device@example.com")

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class MockEmailConfigService:
        def get_config(self, decrypt: bool) -> EmailServerConfig:
            return config

    class MockBookService:
        def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
            # Return a valid book so the code can proceed to check user ID
            book = Book(id=1, title="Test Book", uuid="test-uuid")
            return BookWithFullRelations(
                book=book,
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

    mock_service = MockBookService()

    def mock_email_config_service(req: object, sess: object) -> MockEmailConfigService:
        return MockEmailConfigService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(books, "_email_config_service", mock_email_config_service)
    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.send_book_to_device(
            request,
            session,
            book_id=1,
            current_user=user,
            send_request=payload,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "user_missing_id"


def test_send_book_success_enqueues_task(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test send_book successfully enqueues background task (covers lines 971-1070)."""
    from datetime import UTC, datetime
    from unittest.mock import MagicMock

    from bookcard.api.schemas.books import BookSendRequest
    from bookcard.models.auth import User
    from bookcard.models.config import EmailServerConfig, EmailServerType
    from bookcard.models.tasks import TaskType

    class DummyRequest:
        def __init__(self) -> None:
            from tests.conftest import TEST_ENCRYPTION_KEY

            class DummyConfig:
                encryption_key = TEST_ENCRYPTION_KEY

            # Create mock task runner
            mock_task_runner = MagicMock()
            mock_task_runner.enqueue.return_value = 123  # Return a task_id

            class DummyState:
                config = DummyConfig()
                task_runner = mock_task_runner

            self.app = type("App", (), {"state": DummyState()})()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    payload = BookSendRequest(to_email="device@example.com", file_format="EPUB")

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class MockEmailConfigService:
        def get_config(self, decrypt: bool) -> EmailServerConfig:
            return config

    class MockBookService:
        def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
            book = Book(id=1, title="Test Book", uuid="test-uuid")
            return BookWithFullRelations(
                book=book,
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

    mock_service = MockBookService()

    def mock_email_config_service(req: object, sess: object) -> MockEmailConfigService:
        return MockEmailConfigService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(books, "_email_config_service", mock_email_config_service)
    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)  # type: ignore[arg-type]

    # Should not raise an exception
    result = books.send_book_to_device(
        request,
        session,
        book_id=1,
        current_user=user,
        send_request=payload,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
    )

    # Should return None (204 No Content)
    assert result is None

    # Verify task was enqueued with correct parameters
    task_runner = request.app.state.task_runner
    task_runner.enqueue.assert_called_once_with(
        task_type=TaskType.EMAIL_SEND,
        payload={
            "book_id": 1,
            "to_email": "device@example.com",
            "file_format": "EPUB",
            "encryption_key": request.app.state.config.encryption_key,
        },
        user_id=1,
        metadata={
            "task_type": TaskType.EMAIL_SEND,
            "book_id": 1,
            "to_email": "device@example.com",
            "file_format": "EPUB",
            # encryption_key intentionally excluded from metadata to avoid exposing it
        },
    )


def test_send_book_task_runner_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test send_book raises 503 when task runner is unavailable (covers lines 1040-1048)."""
    from datetime import UTC, datetime

    from bookcard.api.schemas.books import BookSendRequest
    from bookcard.models.auth import User
    from bookcard.models.config import EmailServerConfig, EmailServerType

    class DummyRequest:
        def __init__(self) -> None:
            from tests.conftest import TEST_ENCRYPTION_KEY

            class DummyConfig:
                encryption_key = TEST_ENCRYPTION_KEY

            # No task_runner in state
            class DummyState:
                config = DummyConfig()
                # task_runner is missing

            self.app = type("App", (), {"state": DummyState()})()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    payload = BookSendRequest(to_email="device@example.com")

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class MockEmailConfigService:
        def get_config(self, decrypt: bool) -> EmailServerConfig:
            return config

    class MockBookService:
        def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
            book = Book(id=1, title="Test Book", uuid="test-uuid")
            return BookWithFullRelations(
                book=book,
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

    mock_service = MockBookService()

    def mock_email_config_service(req: object, sess: object) -> MockEmailConfigService:
        return MockEmailConfigService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(books, "_email_config_service", mock_email_config_service)
    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.send_book_to_device(
            request,
            session,
            book_id=1,
            current_user=user,
            send_request=payload,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Task runner not available"


def test_send_book_task_runner_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test send_book raises 503 when task runner is None (covers lines 1040-1048)."""
    from datetime import UTC, datetime

    from bookcard.api.schemas.books import BookSendRequest
    from bookcard.models.auth import User
    from bookcard.models.config import EmailServerConfig, EmailServerType

    class DummyRequest:
        def __init__(self) -> None:
            from tests.conftest import TEST_ENCRYPTION_KEY

            class DummyConfig:
                encryption_key = TEST_ENCRYPTION_KEY

            # task_runner is explicitly None
            class DummyState:
                config = DummyConfig()
                task_runner = None

            self.app = type("App", (), {"state": DummyState()})()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    payload = BookSendRequest(to_email="device@example.com")

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class MockEmailConfigService:
        def get_config(self, decrypt: bool) -> EmailServerConfig:
            return config

    class MockBookService:
        def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
            book = Book(id=1, title="Test Book", uuid="test-uuid")
            return BookWithFullRelations(
                book=book,
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

    mock_service = MockBookService()

    def mock_email_config_service(req: object, sess: object) -> MockEmailConfigService:
        return MockEmailConfigService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(books, "_email_config_service", mock_email_config_service)
    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.send_book_to_device(
            request,
            session,
            book_id=1,
            current_user=user,
            send_request=payload,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Task runner not available"


def test_send_book_book_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test send_book raises 404 when book not found (covers lines 1012-1017)."""
    from datetime import UTC, datetime
    from unittest.mock import MagicMock

    from bookcard.api.schemas.books import BookSendRequest
    from bookcard.models.auth import User
    from bookcard.models.config import EmailServerConfig, EmailServerType

    class DummyRequest:
        def __init__(self) -> None:
            from tests.conftest import TEST_ENCRYPTION_KEY

            class DummyConfig:
                encryption_key = TEST_ENCRYPTION_KEY

            mock_task_runner = MagicMock()
            mock_task_runner.enqueue.return_value = 123

            class DummyState:
                config = DummyConfig()
                task_runner = mock_task_runner

            self.app = type("App", (), {"state": DummyState()})()

    session = DummySession()
    request = DummyRequest()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    payload = BookSendRequest(to_email="device@example.com")

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class MockEmailConfigService:
        def get_config(self, decrypt: bool) -> EmailServerConfig:
            return config

    class MockBookService:
        def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
            return None  # Book not found

    def mock_email_config_service(req: object, sess: object) -> MockEmailConfigService:
        return MockEmailConfigService()

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return MockBookService()

    mock_service = MockBookService()
    monkeypatch.setattr(books, "_email_config_service", mock_email_config_service)
    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.send_book_to_device(
            request,
            session,
            book_id=999,
            current_user=user,
            send_request=payload,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_download_book_metadata_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test download_book_metadata when book not found (lines 746-753)."""
    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)
    mock_service = MockBookService(get_book_full_result=None)

    with patch("bookcard.api.routes.books._get_active_library_service") as mock_get:
        mock_get.return_value = mock_service

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        with pytest.raises(HTTPException) as exc_info:
            books.download_book_metadata(
                current_user=current_user,
                book_id=1,
                format="json",
                book_service=mock_service,
                permission_helper=mock_permission_helper,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "book_not_found"


def test_download_book_metadata_unsupported_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_book_metadata with unsupported format (lines 764-768)."""
    from datetime import UTC, datetime

    from bookcard.repositories.models import BookWithFullRelations

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)
    book = Book(
        id=1,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=None,
        uuid="test-uuid",
        has_cover=False,
        path="Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
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
    mock_service = MockBookService(get_book_full_result=book_with_rels)

    with patch("bookcard.api.routes.books._get_active_library_service") as mock_get:
        mock_get.return_value = mock_service

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        with pytest.raises(HTTPException) as exc_info:
            books.download_book_metadata(
                current_user=current_user,
                book_id=1,
                format="invalid",
                book_service=mock_service,
                permission_helper=mock_permission_helper,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert "Unsupported format" in str(exc_info.value.detail)


def test_download_book_metadata_other_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_book_metadata with other ValueError (lines 769-773)."""
    from datetime import UTC, datetime

    from bookcard.repositories.models import BookWithFullRelations

    session = DummySession()
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)
    book = Book(
        id=1,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=None,
        uuid="test-uuid",
        has_cover=False,
        path="Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
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
    mock_service = MockBookService(get_book_full_result=book_with_rels)

    with patch("bookcard.api.routes.books._get_active_library_service") as mock_get:
        mock_get.return_value = mock_service

        with patch(
            "bookcard.api.routes.books.MetadataExportService"
        ) as mock_export_service:
            mock_instance = MagicMock()
            mock_instance.export_metadata.side_effect = ValueError("Other error")
            mock_export_service.return_value = mock_instance

            mock_permission_helper, _ = _setup_route_mocks(
                monkeypatch, session, mock_service
            )

            with pytest.raises(HTTPException) as exc_info:
                books.download_book_metadata(
                    current_user=current_user,
                    book_id=1,
                    format="json",
                    book_service=mock_service,
                    permission_helper=mock_permission_helper,
                )
            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == 500
            assert "Other error" in str(exc_info.value.detail)


def test_import_book_metadata_no_filename() -> None:
    """Test import_book_metadata with no filename (lines 809-813)."""
    from fastapi import UploadFile

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = None

    with pytest.raises(HTTPException) as exc_info:
        books.import_book_metadata(mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "filename_required"


def test_import_book_metadata_unsupported_format() -> None:
    """Test import_book_metadata with unsupported format (lines 817-821)."""
    from fastapi import UploadFile

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.txt"

    with pytest.raises(HTTPException) as exc_info:
        books.import_book_metadata(mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in str(exc_info.value.detail)


def test_import_book_metadata_unicode_decode_error() -> None:
    """Test import_book_metadata with UnicodeDecodeError (lines 827-831)."""
    from fastapi import UploadFile

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.opf"
    mock_file.file = MagicMock()
    mock_file.file.read.side_effect = UnicodeDecodeError(
        "utf-8", b"\xff\xfe", 0, 1, "invalid"
    )

    with pytest.raises(HTTPException) as exc_info:
        books.import_book_metadata(mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert "Invalid file encoding" in str(exc_info.value.detail)


def test_import_book_metadata_read_exception() -> None:
    """Test import_book_metadata with read exception (lines 832-836)."""
    from fastapi import UploadFile

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.opf"
    mock_file.file = MagicMock()
    # Use Exception instead of OSError to match the catch-all in the code
    mock_file.file.read.side_effect = Exception("Read error")

    with pytest.raises(HTTPException) as exc_info:
        books.import_book_metadata(mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "failed_to_read_file" in str(exc_info.value.detail)


def test_import_book_metadata_unsupported_format_error() -> None:
    """Test import_book_metadata with unsupported format error (lines 845-849)."""
    from fastapi import UploadFile

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.opf"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"<package></package>"

    with patch(
        "bookcard.api.routes.books.MetadataImportService"
    ) as mock_import_service:
        mock_instance = MagicMock()
        mock_instance.import_metadata.side_effect = ValueError(
            "Unsupported format: invalid"
        )
        mock_import_service.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            books.import_book_metadata(mock_file)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert "Unsupported format" in str(exc_info.value.detail)


def test_import_book_metadata_other_value_error() -> None:
    """Test import_book_metadata with other ValueError (lines 850-854)."""
    from fastapi import UploadFile

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.opf"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"<package></package>"

    with patch(
        "bookcard.api.routes.books.MetadataImportService"
    ) as mock_import_service:
        mock_instance = MagicMock()
        mock_instance.import_metadata.side_effect = ValueError("Parsing error")
        mock_import_service.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            books.import_book_metadata(mock_file)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert "Parsing error" in str(exc_info.value.detail)


def test_import_book_metadata_unexpected_exception() -> None:
    """Test import_book_metadata with unexpected exception (lines 855-860)."""
    from fastapi import UploadFile

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.opf"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"<package></package>"

    with patch(
        "bookcard.api.routes.books.MetadataImportService"
    ) as mock_import_service:
        mock_instance = MagicMock()
        mock_instance.import_metadata.side_effect = RuntimeError("Unexpected error")
        mock_import_service.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            books.import_book_metadata(mock_file)
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 500
        assert "Failed to import metadata" in str(exc_info.value.detail)
