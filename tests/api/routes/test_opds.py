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

"""Tests for OPDS API routes to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request, status
from fastapi.responses import FileResponse, Response

import bookcard.api.routes.opds as opds_routes
from bookcard.api.schemas.opds import OpdsFeedResponse
from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.models.core import Book
from bookcard.repositories.models import BookWithRelations

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import DummySession


@pytest.fixture
def opds_user() -> User:
    """Create a test OPDS user.

    Returns
    -------
    User
        Mock user instance.
    """
    return User(
        id=1,
        username="opdsuser",
        email="opds@example.com",
        password_hash="hash",
    )


@pytest.fixture
def mock_request() -> Request:
    """Create a mock Request object.

    Returns
    -------
    Request
        Mock FastAPI request.
    """
    request = MagicMock(spec=Request)
    request.base_url = "http://testserver/"
    request.url = MagicMock()
    request.url.path = "/opds"
    return request


@pytest.fixture
def mock_library() -> Library:
    """Create a mock Library.

    Returns
    -------
    Library
        Mock library instance.
    """
    library = MagicMock(spec=Library)
    library.id = 1
    library.name = "Test Library"
    library.calibre_db_path = "/test/library/metadata.db"
    library.library_root = None
    return library


@pytest.fixture
def mock_feed_response() -> OpdsFeedResponse:
    """Create a mock OPDS feed response.

    Returns
    -------
    OpdsFeedResponse
        Mock feed response.
    """
    return OpdsFeedResponse(
        xml_content="<feed></feed>",
        content_type="application/atom+xml;profile=opds-catalog;kind=acquisition",
    )


def _mock_permission_service(
    monkeypatch: pytest.MonkeyPatch, has_permission: bool = True
) -> None:
    """Mock PermissionService.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    has_permission : bool
        Whether user has permission (default: True).
    """
    mock_permission_service = MagicMock()
    mock_permission_service.has_permission.return_value = has_permission
    monkeypatch.setattr(
        "bookcard.api.routes.opds.PermissionService",
        lambda session: mock_permission_service,
    )


def _mock_library_service(
    monkeypatch: pytest.MonkeyPatch, library: Library | None = None
) -> None:
    """Mock LibraryService.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    library : Library | None
        Library to return (default: None).
    """
    mock_library_service = MagicMock()
    mock_library_service.get_active_library.return_value = library

    mock_library_repo = MagicMock()
    monkeypatch.setattr(
        "bookcard.api.routes.opds.LibraryRepository",
        lambda session: mock_library_repo,
    )
    monkeypatch.setattr(
        "bookcard.api.routes.opds.LibraryService",
        lambda session, repo: mock_library_service,
    )


def _mock_feed_service(
    monkeypatch: pytest.MonkeyPatch,
    feed_response: OpdsFeedResponse | None = None,
) -> MagicMock:
    """Mock OpdsFeedService.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    feed_response : OpdsFeedResponse | None
        Feed response to return (default: None).

    Returns
    -------
    MagicMock
        Mock feed service.
    """
    mock_feed_service = MagicMock()
    if feed_response:
        mock_feed_service.generate_catalog_feed.return_value = feed_response
        mock_feed_service.generate_books_feed.return_value = feed_response
        mock_feed_service.generate_new_feed.return_value = feed_response
        mock_feed_service.generate_discover_feed.return_value = feed_response
        mock_feed_service.generate_search_feed.return_value = feed_response
        mock_feed_service.generate_opensearch_description.return_value = feed_response
        mock_feed_service.generate_books_by_letter_feed.return_value = feed_response
        mock_feed_service.generate_rated_feed.return_value = feed_response
        mock_feed_service.generate_author_index_feed.return_value = feed_response
        mock_feed_service.generate_author_letter_feed.return_value = feed_response
        mock_feed_service.generate_books_by_author_feed.return_value = feed_response
        mock_feed_service.generate_publisher_index_feed.return_value = feed_response
        mock_feed_service.generate_books_by_publisher_feed.return_value = feed_response
        mock_feed_service.generate_category_index_feed.return_value = feed_response
        mock_feed_service.generate_category_letter_feed.return_value = feed_response
        mock_feed_service.generate_books_by_category_feed.return_value = feed_response
        mock_feed_service.generate_series_index_feed.return_value = feed_response
        mock_feed_service.generate_series_letter_feed.return_value = feed_response
        mock_feed_service.generate_books_by_series_feed.return_value = feed_response
        mock_feed_service.generate_rating_index_feed.return_value = feed_response
        mock_feed_service.generate_books_by_rating_feed.return_value = feed_response
        mock_feed_service.generate_format_index_feed.return_value = feed_response
        mock_feed_service.generate_books_by_format_feed.return_value = feed_response
        mock_feed_service.generate_language_index_feed.return_value = feed_response
        mock_feed_service.generate_books_by_language_feed.return_value = feed_response
        mock_feed_service.generate_shelf_index_feed.return_value = feed_response
        mock_feed_service.generate_books_by_shelf_feed.return_value = feed_response
        mock_feed_service.generate_hot_feed.return_value = feed_response
        mock_feed_service.generate_read_books_feed.return_value = feed_response
        mock_feed_service.generate_unread_books_feed.return_value = feed_response

    def _get_opds_feed_service(session: DummySession) -> MagicMock:
        return mock_feed_service

    monkeypatch.setattr(
        "bookcard.api.routes.opds._get_opds_feed_service",
        _get_opds_feed_service,
    )
    return mock_feed_service


class TestCheckOpdsReadPermission:
    """Test _check_opds_read_permission helper."""

    def test_check_permission_no_user(
        self, monkeypatch: pytest.MonkeyPatch, session: DummySession
    ) -> None:
        """Test permission check raises 401 when user is None."""
        _mock_permission_service(monkeypatch)

        with pytest.raises(HTTPException) as exc_info:
            opds_routes._check_opds_read_permission(None, session)  # type: ignore[arg-type]

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "authentication_required" in str(exc_info.value.detail)

    def test_check_permission_no_permission(
        self, monkeypatch: pytest.MonkeyPatch, session: DummySession, opds_user: User
    ) -> None:
        """Test permission check raises 403 when user lacks permission."""
        _mock_permission_service(monkeypatch, has_permission=False)

        with pytest.raises(HTTPException) as exc_info:
            opds_routes._check_opds_read_permission(opds_user, session)  # type: ignore[arg-type]

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_check_permission_success(
        self, monkeypatch: pytest.MonkeyPatch, session: DummySession, opds_user: User
    ) -> None:
        """Test permission check succeeds when user has permission."""
        _mock_permission_service(monkeypatch, has_permission=True)

        # Should not raise
        opds_routes._check_opds_read_permission(opds_user, session)  # type: ignore[arg-type]


class TestGetOpdsFeedService:
    """Test _get_opds_feed_service helper."""

    def test_get_service_no_library(
        self, monkeypatch: pytest.MonkeyPatch, session: DummySession
    ) -> None:
        """Test service getter raises 404 when no active library."""
        _mock_library_service(monkeypatch, library=None)

        with pytest.raises(HTTPException) as exc_info:
            opds_routes._get_opds_feed_service(session)  # type: ignore[arg-type]

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_service_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        mock_library: Library,
    ) -> None:
        """Test service getter returns service when library exists."""
        _mock_library_service(monkeypatch, library=mock_library)

        service = opds_routes._get_opds_feed_service(session)  # type: ignore[arg-type]
        assert service is not None

    """Test feed_index endpoint."""

    def test_feed_index_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_request: Request,
        mock_feed_response: OpdsFeedResponse,
    ) -> None:
        """Test feed_index returns catalog feed."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=MagicMock(spec=Library))
        _mock_feed_service(monkeypatch, feed_response=mock_feed_response)

        response = opds_routes.feed_index(
            request=mock_request,
            session=session,  # type: ignore[arg-type]
            opds_user=opds_user,
        )

        assert isinstance(response, Response)
        assert response.body == b"<feed></feed>"


@pytest.mark.parametrize(
    ("endpoint_func", "feed_method"),
    [
        ("feed_books", "generate_books_feed"),
        ("feed_new", "generate_new_feed"),
        ("feed_discover", "generate_discover_feed"),
        ("feed_search", "generate_search_feed"),
        ("feed_osd", "generate_opensearch_description"),
        ("feed_books_letter", "generate_books_by_letter_feed"),
        ("feed_rated", "generate_rated_feed"),
        ("feed_author_index", "generate_author_index_feed"),
        ("feed_author_letter", "generate_author_letter_feed"),
        ("feed_author", "generate_books_by_author_feed"),
        ("feed_publisher_index", "generate_publisher_index_feed"),
        ("feed_publisher", "generate_books_by_publisher_feed"),
        ("feed_category_index", "generate_category_index_feed"),
        ("feed_category_letter", "generate_category_letter_feed"),
        ("feed_category", "generate_books_by_category_feed"),
        ("feed_series_index", "generate_series_index_feed"),
        ("feed_series_letter", "generate_series_letter_feed"),
        ("feed_series", "generate_books_by_series_feed"),
        ("feed_rating_index", "generate_rating_index_feed"),
        ("feed_ratings", "generate_books_by_rating_feed"),
        ("feed_format_index", "generate_format_index_feed"),
        ("feed_format", "generate_books_by_format_feed"),
        ("feed_language_index", "generate_language_index_feed"),
        ("feed_language", "generate_books_by_language_feed"),
        ("feed_shelf_index", "generate_shelf_index_feed"),
        ("feed_shelf", "generate_books_by_shelf_feed"),
        ("feed_hot", "generate_hot_feed"),
        ("feed_read_books", "generate_read_books_feed"),
        ("feed_unread_books", "generate_unread_books_feed"),
    ],
)
class TestFeedEndpoints:
    """Test various feed endpoints using parametrization."""

    def test_feed_endpoint_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_request: Request,
        mock_feed_response: OpdsFeedResponse,
        endpoint_func: str,
        feed_method: str,
    ) -> None:
        """Test feed endpoint returns feed."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=MagicMock(spec=Library))
        _mock_feed_service(monkeypatch, feed_response=mock_feed_response)

        func = getattr(opds_routes, endpoint_func)
        kwargs = self._build_endpoint_kwargs(
            endpoint_func, mock_request, session, opds_user
        )

        response = func(**kwargs)

        assert isinstance(response, Response)
        assert response.body == b"<feed></feed>"

    @staticmethod
    def _build_endpoint_kwargs(
        endpoint_func: str,
        mock_request: Request,
        session: DummySession,
        opds_user: User,
    ) -> dict[str, object]:
        """Build kwargs for endpoint function call.

        Parameters
        ----------
        endpoint_func : str
            Endpoint function name.
        mock_request : Request
            Mock request object.
        session : DummySession
            Mock database session.
        opds_user : User
            Mock user.

        Returns
        -------
        dict[str, object]
            Keyword arguments for endpoint function.
        """
        kwargs: dict[str, object] = {
            "request": mock_request,
            "session": session,  # type: ignore[arg-type]
            "opds_user": opds_user,
        }

        TestFeedEndpoints._add_pagination_params(endpoint_func, kwargs)
        TestFeedEndpoints._add_endpoint_specific_params(endpoint_func, kwargs)

        return kwargs

    @staticmethod
    def _add_pagination_params(endpoint_func: str, kwargs: dict[str, object]) -> None:
        """Add pagination parameters to kwargs.

        Parameters
        ----------
        endpoint_func : str
            Endpoint function name.
        kwargs : dict[str, object]
            Keyword arguments dictionary to modify.
        """
        no_pagination_endpoints = (
            "feed_osd",
            "feed_category_letter",
            "feed_series_letter",
            "feed_shelf",
            "feed_publisher_index",
            "feed_category_index",
            "feed_series_index",
            "feed_rating_index",
            "feed_format_index",
            "feed_language_index",
            "feed_shelf_index",
            "feed_read_books",
            "feed_unread_books",
        )

        if endpoint_func == "feed_discover":
            kwargs["page_size"] = 20
        elif endpoint_func not in no_pagination_endpoints:
            kwargs["offset"] = 0
            kwargs["page_size"] = 20

    @staticmethod
    def _add_endpoint_specific_params(
        endpoint_func: str, kwargs: dict[str, object]
    ) -> None:
        """Add endpoint-specific parameters to kwargs.

        Parameters
        ----------
        endpoint_func : str
            Endpoint function name.
        kwargs : dict[str, object]
            Keyword arguments dictionary to modify.
        """
        # Handle letter endpoints
        if "letter" in endpoint_func:
            kwargs["letter"] = "A"
            return

        # Handle search endpoint
        if endpoint_func == "feed_search":
            kwargs["query"] = "test"
            return

        # Handle entity-specific endpoints (not index, not letter)
        entity_params: dict[str, tuple[str, object]] = {
            "author": ("author_id", 1),
            "publisher": ("publisher_id", 1),
            "category": ("category_id", 1),
            "series": ("series_id", 1),
            "rating": ("rating_id", 1),
            "format": ("format_name", "EPUB"),
            "language": ("language_id", 1),
            "shelf": ("shelf_id", 1),
        }

        for entity, (param_name, param_value) in entity_params.items():
            if (
                entity in endpoint_func
                and "index" not in endpoint_func
                and "letter" not in endpoint_func
            ):
                kwargs[param_name] = param_value
                return


class TestFeedSearchPath:
    """Test feed_search_path endpoint."""

    def test_feed_search_path_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_request: Request,
        mock_feed_response: OpdsFeedResponse,
    ) -> None:
        """Test feed_search_path with query."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=MagicMock(spec=Library))
        _mock_feed_service(monkeypatch, feed_response=mock_feed_response)

        response = opds_routes.feed_search_path(
            request=mock_request,
            session=session,  # type: ignore[arg-type]
            opds_user=opds_user,
            query="test+query",
            offset=0,
            page_size=20,
        )

        assert isinstance(response, Response)

    def test_feed_search_path_empty_query(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_request: Request,
    ) -> None:
        """Test feed_search_path raises 400 for empty query."""
        _mock_permission_service(monkeypatch)

        with pytest.raises(HTTPException) as exc_info:
            opds_routes.feed_search_path(
                request=mock_request,
                session=session,  # type: ignore[arg-type]
                opds_user=opds_user,
                query="   ",  # Whitespace only
            )

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


class TestOpdsDownload:
    """Test opds_download endpoint."""

    def test_download_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_library: Library,
        tmp_path: Path,
    ) -> None:
        """Test download returns file."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=mock_library)

        # Create test file
        book_path = tmp_path / "book_path"
        book_path.mkdir()
        test_file = book_path / "1.epub"
        test_file.write_text("test content")

        mock_library.library_root = str(tmp_path)
        mock_library.calibre_db_path = str(tmp_path / "metadata.db")

        # Mock book service
        mock_book_with_rels = MagicMock(spec=BookWithRelations)
        mock_book_with_rels.book = MagicMock(spec=Book)
        mock_book_with_rels.book.id = 1
        mock_book_with_rels.book.title = "Test Book"
        mock_book_with_rels.book.path = "book_path"
        mock_book_with_rels.authors = ["Test Author"]
        mock_book_with_rels.formats = [{"format": "EPUB", "name": "1.epub"}]

        mock_book_service = MagicMock()
        mock_book_service.get_book_full.return_value = mock_book_with_rels
        mock_book_service.get_format_file_path.return_value = test_file

        with patch("bookcard.api.routes.opds.BookService") as mock_book_service_class:
            mock_book_service_class.return_value = mock_book_service

            response = opds_routes.opds_download(
                session=session,  # type: ignore[arg-type]
                opds_user=opds_user,
                book_id=1,
                book_format="EPUB",
            )

            assert isinstance(response, FileResponse)
            assert response.path == str(test_file)

    def test_download_no_library(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
    ) -> None:
        """Test download raises 404 when no library."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=None)

        with pytest.raises(HTTPException) as exc_info:
            opds_routes.opds_download(
                session=session,  # type: ignore[arg-type]
                opds_user=opds_user,
                book_id=1,
                book_format="EPUB",
            )

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_download_book_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_library: Library,
    ) -> None:
        """Test download raises 404 when book not found."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=mock_library)

        mock_book_service = MagicMock()
        mock_book_service.get_book_full.return_value = None

        with patch("bookcard.api.routes.opds.BookService") as mock_book_service_class:
            mock_book_service_class.return_value = mock_book_service

            with pytest.raises(HTTPException) as exc_info:
                opds_routes.opds_download(
                    session=session,  # type: ignore[arg-type]
                    opds_user=opds_user,
                    book_id=1,
                    book_format="EPUB",
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert exc_info.value.detail == "book_not_found"

    def test_download_format_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_library: Library,
    ) -> None:
        """Test download raises 404 when format not found."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=mock_library)

        mock_book_with_rels = MagicMock(spec=BookWithRelations)
        mock_book_with_rels.book = MagicMock(spec=Book)
        mock_book_with_rels.book.id = 1
        mock_book_with_rels.authors = ["Test Author"]
        mock_book_with_rels.formats = [{"format": "PDF", "name": "1.pdf"}]

        mock_book_service = MagicMock()
        mock_book_service.get_book_full.return_value = mock_book_with_rels
        mock_book_service.get_format_file_path.side_effect = ValueError(
            "format_not_found"
        )

        with patch("bookcard.api.routes.opds.BookService") as mock_book_service_class:
            mock_book_service_class.return_value = mock_book_service

            # Current behavior: missing format returns a plain 404 Response (not an exception)
            response = opds_routes.opds_download(
                session=session,  # type: ignore[arg-type]
                opds_user=opds_user,
                book_id=1,
                book_format="EPUB",
            )

            assert isinstance(response, Response)
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestOpdsCover:
    """Test opds_cover endpoint."""

    def test_cover_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_library: Library,
        tmp_path: Path,
    ) -> None:
        """Test cover returns image."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=mock_library)

        # Create test cover file
        cover_path = tmp_path / "cover.jpg"
        cover_path.write_bytes(b"fake image data")

        mock_book_with_rels = MagicMock(spec=BookWithRelations)
        mock_book_with_rels.book = MagicMock(spec=Book)
        mock_book_with_rels.book.id = 1
        mock_book_with_rels.authors = ["Test Author"]

        mock_book_service = MagicMock()
        mock_book_service.get_book.return_value = mock_book_with_rels
        mock_book_service.get_thumbnail_path.return_value = cover_path

        with patch("bookcard.api.routes.opds.BookService") as mock_book_service_class:
            mock_book_service_class.return_value = mock_book_service

            response = opds_routes.opds_cover(
                session=session,  # type: ignore[arg-type]
                opds_user=opds_user,
                book_id=1,
            )

            assert isinstance(response, FileResponse)

    def test_cover_no_library(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
    ) -> None:
        """Test cover raises 404 when no library."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=None)

        with pytest.raises(HTTPException) as exc_info:
            opds_routes.opds_cover(
                session=session,  # type: ignore[arg-type]
                opds_user=opds_user,
                book_id=1,
            )

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cover_book_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_library: Library,
    ) -> None:
        """Test cover returns 404 when book not found."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=mock_library)

        mock_book_service = MagicMock()
        mock_book_service.get_book.return_value = None

        with patch("bookcard.api.routes.opds.BookService") as mock_book_service_class:
            mock_book_service_class.return_value = mock_book_service

            response = opds_routes.opds_cover(
                session=session,  # type: ignore[arg-type]
                opds_user=opds_user,
                book_id=1,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cover_no_thumbnail(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
        mock_library: Library,
    ) -> None:
        """Test cover returns 404 when no thumbnail."""
        _mock_permission_service(monkeypatch)
        _mock_library_service(monkeypatch, library=mock_library)

        mock_book_with_rels = MagicMock(spec=BookWithRelations)
        mock_book_with_rels.book = MagicMock(spec=Book)
        mock_book_with_rels.book.id = 1
        mock_book_with_rels.authors = ["Test Author"]

        mock_book_service = MagicMock()
        mock_book_service.get_book.return_value = mock_book_with_rels
        mock_book_service.get_thumbnail_path.return_value = None

        with patch("bookcard.api.routes.opds.BookService") as mock_book_service_class:
            mock_book_service_class.return_value = mock_book_service

            response = opds_routes.opds_cover(
                session=session,  # type: ignore[arg-type]
                opds_user=opds_user,
                book_id=1,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestOpdsStats:
    """Test opds_stats endpoint."""

    def test_stats_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
    ) -> None:
        """Test stats returns JSON."""
        _mock_permission_service(monkeypatch)

        # Mock session.exec to return counts
        session.set_exec_result([(10,)])  # books
        session.add_exec_result([(5,)])  # authors
        session.add_exec_result([(3,)])  # tags
        session.add_exec_result([(2,)])  # series

        response = opds_routes.opds_stats(
            session=session,  # type: ignore[arg-type]
            opds_user=opds_user,
        )

        assert isinstance(response, Response)
        assert response.media_type == "application/json"


class TestGetOpdsLibraryPath:
    """Test _get_opds_library_path helper."""

    def test_get_path_removed(self) -> None:
        """Test _get_opds_library_path is no longer needed."""
        # This functionality is now handled by BookService.


class TestFindOpdsFormatData:
    """Test _find_opds_format_data helper."""

    def test_find_format_removed(self) -> None:
        """Test _find_opds_format_data is no longer needed."""
        # This functionality is now handled by BookService.


class TestGetOpdsMediaType:
    """Test _get_opds_media_type helper."""

    @pytest.mark.parametrize(
        ("format_name", "expected"),
        [
            ("EPUB", "application/epub+zip"),
            ("PDF", "application/pdf"),
            ("MOBI", "application/x-mobipocket-ebook"),
            ("AZW3", "application/vnd.amazon.ebook"),
            ("UNKNOWN", "application/octet-stream"),
            ("epub", "application/epub+zip"),  # Case insensitive
        ],
    )
    def test_get_media_type(self, format_name: str, expected: str) -> None:
        """Test getting media type."""
        result = opds_routes._get_opds_media_type(format_name)
        assert result == expected


class TestSanitizeOpdsFilename:
    """Test _sanitize_opds_filename helper."""

    @pytest.mark.parametrize(
        ("authors", "title", "book_id", "format_name", "expected_pattern"),
        [
            (["Author"], "Title", 1, "EPUB", "Author - Title.epub"),
            ([], "Title", 1, "PDF", "Unknown - Title.pdf"),
            (["Author"], "", 1, "MOBI", "Author - book_1.mobi"),
            (
                ["Author 1", "Author 2"],
                "Title",
                1,
                "EPUB",
                "Author 1, Author 2 - Title.epub",
            ),
        ],
    )
    def test_sanitize_filename(
        self,
        authors: list[str],
        title: str,
        book_id: int,
        format_name: str,
        expected_pattern: str,
    ) -> None:
        """Test filename sanitization."""
        result = opds_routes._sanitize_opds_filename(
            authors, title, book_id, format_name
        )
        assert result == expected_pattern


class TestFindOpdsFilePath:
    """Test _find_opds_file_path helper."""

    def test_find_file_path_removed(self) -> None:
        """Test _find_opds_file_path is no longer needed."""
        # This functionality is now handled by BookService.


class TestGetMetadataCalibreCompanion:
    """Test get_metadata_calibre_companion endpoint."""

    def test_get_metadata_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
    ) -> None:
        """Test get_metadata returns JSON."""
        _mock_permission_service(monkeypatch)

        book = Book(
            id=1,
            title="Test Book",
            uuid=str(uuid4()),
            timestamp=None,
            pubdate=None,
        )
        session.set_exec_result([book])

        response = opds_routes.get_metadata_calibre_companion(
            session=session,  # type: ignore[arg-type]
            opds_user=opds_user,
            uuid="test-uuid",
        )

        assert isinstance(response, Response)
        assert response.media_type == "application/json; charset=utf-8"

    def test_get_metadata_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        session: DummySession,
        opds_user: User,
    ) -> None:
        """Test get_metadata returns empty when book not found."""
        _mock_permission_service(monkeypatch)

        session.set_exec_result([])

        response = opds_routes.get_metadata_calibre_companion(
            session=session,  # type: ignore[arg-type]
            opds_user=opds_user,
            uuid="nonexistent",
        )

        assert isinstance(response, Response)
        assert response.body == b""
