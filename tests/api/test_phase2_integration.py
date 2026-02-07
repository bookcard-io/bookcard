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

"""Tests for Phase 2 integration: BookRead schema, BookResponseBuilder, and _resolve_requested_library."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from bookcard.api.routes.books import _resolve_requested_library
from bookcard.api.schemas.books import BookRead
from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.models.core import Book
from bookcard.models.user_library import UserLibrary
from bookcard.repositories.models import BookWithRelations
from bookcard.services.book_response_builder import BookResponseBuilder
from bookcard.services.book_service import BookService
from tests.conftest import DummySession


def _make_library(lib_id: int = 1, name: str = "Test Library") -> Library:
    """Create a test library."""
    lib = Library(id=lib_id, name=name)
    lib.calibre_db_path = "/fake/path"
    return lib


def _make_user(user_id: int = 1) -> User:
    """Create a test user."""
    return User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


def _make_book_with_rels(book_id: int = 1) -> BookWithRelations:
    """Create a BookWithRelations for testing."""
    book = Book(id=book_id, title="Test Book", sort="Test Book", author_sort="Author")
    return BookWithRelations(
        book=book,
        authors=["Test Author"],
        series=None,
        formats=[],
    )


class TestBookReadSchema:
    """Tests for library fields on BookRead schema."""

    def test_library_id_defaults_to_none(self) -> None:
        """library_id defaults to None for backward compatibility."""
        book_read = BookRead(
            id=1,
            title="Test",
            authors=[],
            author_ids=[],
            author_sort="",
            title_sort="",
            uuid="",
            thumbnail_url=None,
            has_cover=False,
            tags=[],
            tag_ids=[],
            formats=[],
        )
        assert book_read.library_id is None
        assert book_read.library_name is None

    def test_library_fields_populated(self) -> None:
        """library_id and library_name can be set."""
        book_read = BookRead(
            id=1,
            title="Test",
            authors=[],
            author_ids=[],
            author_sort="",
            title_sort="",
            uuid="",
            thumbnail_url=None,
            has_cover=False,
            tags=[],
            tag_ids=[],
            formats=[],
            library_id=42,
            library_name="Comics",
        )
        assert book_read.library_id == 42
        assert book_read.library_name == "Comics"


class TestBookResponseBuilderLibraryFields:
    """Tests for BookResponseBuilder populating library fields."""

    def test_build_book_read_populates_library_fields(self) -> None:
        """build_book_read should set library_id and library_name from BookService."""
        library = _make_library(lib_id=42, name="Comics")
        mock_service = MagicMock(spec=BookService)
        mock_service.library = library
        mock_service.get_thumbnail_url.return_value = None

        builder = BookResponseBuilder(mock_service)
        book_with_rels = _make_book_with_rels(book_id=10)

        result = builder.build_book_read(book_with_rels)

        assert result.library_id == 42
        assert result.library_name == "Comics"

    def test_build_book_read_list_populates_library_fields(self) -> None:
        """build_book_read_list should set library fields on each item."""
        library = _make_library(lib_id=7, name="Literature")
        mock_service = MagicMock(spec=BookService)
        mock_service.library = library
        mock_service.get_thumbnail_url.return_value = None

        builder = BookResponseBuilder(mock_service)
        books = [_make_book_with_rels(book_id=i) for i in range(1, 4)]

        results = builder.build_book_read_list(books)

        assert len(results) == 3
        for br in results:
            assert br.library_id == 7
            assert br.library_name == "Literature"


class TestResolveRequestedLibrary:
    """Tests for _resolve_requested_library in books.py."""

    @patch("bookcard.api.routes.books.LibraryRepository")
    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_returns_service_for_accessible_library(
        self,
        mock_ul_repo_cls: MagicMock,
        mock_lib_repo_cls: MagicMock,
    ) -> None:
        """Return a BookService tuple when user has access."""
        session = DummySession()
        user = _make_user(user_id=1)
        target_library = _make_library(lib_id=42, name="Comics")

        mock_ul_repo = MagicMock()
        mock_ul_repo.find_by_user_and_library.return_value = UserLibrary(
            id=1, user_id=1, library_id=42, is_visible=True, is_active=False
        )
        mock_ul_repo_cls.return_value = mock_ul_repo

        mock_lib_repo = MagicMock()
        mock_lib_repo.get.return_value = target_library
        mock_lib_repo_cls.return_value = mock_lib_repo

        svc, builder, lib_id = _resolve_requested_library(session, user, 42)  # type: ignore[arg-type]

        assert lib_id == 42
        assert svc.library is target_library
        assert isinstance(builder, BookResponseBuilder)

    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_raises_401_for_anonymous_user(
        self,
        mock_ul_repo_cls: MagicMock,
    ) -> None:
        """Raise 401 when user is anonymous (None)."""
        session = DummySession()

        with pytest.raises(HTTPException) as exc_info:
            _resolve_requested_library(session, None, 42)  # type: ignore[arg-type]

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "authentication_required"

    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_raises_403_when_no_association(
        self,
        mock_ul_repo_cls: MagicMock,
    ) -> None:
        """Raise 403 when user has no UserLibrary association."""
        session = DummySession()
        user = _make_user(user_id=1)

        mock_ul_repo = MagicMock()
        mock_ul_repo.find_by_user_and_library.return_value = None
        mock_ul_repo_cls.return_value = mock_ul_repo

        with pytest.raises(HTTPException) as exc_info:
            _resolve_requested_library(session, user, 42)  # type: ignore[arg-type]

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "library_access_denied"

    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_raises_403_when_not_visible(
        self,
        mock_ul_repo_cls: MagicMock,
    ) -> None:
        """Raise 403 when user's association is not visible."""
        session = DummySession()
        user = _make_user(user_id=1)

        mock_ul_repo = MagicMock()
        mock_ul_repo.find_by_user_and_library.return_value = UserLibrary(
            id=1, user_id=1, library_id=42, is_visible=False, is_active=False
        )
        mock_ul_repo_cls.return_value = mock_ul_repo

        with pytest.raises(HTTPException) as exc_info:
            _resolve_requested_library(session, user, 42)  # type: ignore[arg-type]

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "library_access_denied"

    @patch("bookcard.api.routes.books.LibraryRepository")
    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_raises_404_when_library_not_found(
        self,
        mock_ul_repo_cls: MagicMock,
        mock_lib_repo_cls: MagicMock,
    ) -> None:
        """Raise 404 when the library doesn't exist in the database."""
        session = DummySession()
        user = _make_user(user_id=1)

        mock_ul_repo = MagicMock()
        mock_ul_repo.find_by_user_and_library.return_value = UserLibrary(
            id=1, user_id=1, library_id=42, is_visible=True, is_active=False
        )
        mock_ul_repo_cls.return_value = mock_ul_repo

        mock_lib_repo = MagicMock()
        mock_lib_repo.get.return_value = None
        mock_lib_repo_cls.return_value = mock_lib_repo

        with pytest.raises(HTTPException) as exc_info:
            _resolve_requested_library(session, user, 42)  # type: ignore[arg-type]

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "library_not_found"
