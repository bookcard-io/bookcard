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

"""Tests for tracked book routes to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

import bookcard.api.routes.tracked_books as tracked_books
from bookcard.api.schemas.tracked_books import (
    TrackedBookCreate,
    TrackedBookListResponse,
    TrackedBookRead,
    TrackedBookStatusResponse,
    TrackedBookUpdate,
)
from bookcard.models.auth import User
from bookcard.models.pvr import TrackedBook, TrackedBookStatus

# Rebuild Pydantic models to resolve forward references
TrackedBookRead.model_rebuild()
TrackedBookStatusResponse.model_rebuild()

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def user() -> User:
    """Create a test user.

    Returns
    -------
    User
        User instance.
    """
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
        is_admin=False,
    )


@pytest.fixture
def tracked_book() -> TrackedBook:
    """Create a tracked book for testing.

    Returns
    -------
    TrackedBook
        Tracked book instance.
    """
    return TrackedBook(
        id=1,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
        library_id=1,
        metadata_source_id="google",
        metadata_external_id="123",
        status=TrackedBookStatus.WANTED,
        auto_search_enabled=True,
        auto_download_enabled=False,
        preferred_formats=["epub"],
        matched_book_id=None,
        matched_library_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestGetTrackedBookService:
    """Test _get_tracked_book_service function."""

    def test_get_tracked_book_service(self, session: DummySession) -> None:
        """Test _get_tracked_book_service creates TrackedBookService instance (covers line 63).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = tracked_books._get_tracked_book_service(session)
        assert service is not None
        assert hasattr(service, "_session")
        assert service._session == session


class TestRaiseNotFound:
    """Test _raise_not_found function."""

    @pytest.mark.parametrize("book_id", [1, 42, 999])
    def test_raise_not_found(self, book_id: int) -> None:
        """Test _raise_not_found raises HTTPException with 404 (covers line 79).

        Parameters
        ----------
        book_id : int
            Tracked book ID to test.
        """
        with pytest.raises(HTTPException) as exc_info:
            tracked_books._raise_not_found(book_id)

        exc = exc_info.value
        assert isinstance(exc, HTTPException)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == f"Tracked book {book_id} not found"


class TestListTrackedBooks:
    """Test list_tracked_books endpoint."""

    def test_list_tracked_books(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test list_tracked_books returns books (covers lines 105-108).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_tracked_books.return_value = [tracked_book]
            mock_service_class.return_value = mock_service

            result = tracked_books.list_tracked_books(
                session=session,
                status_filter=None,
            )

            assert isinstance(result, TrackedBookListResponse)
            assert result.total == 1
            assert len(result.items) == 1
            assert result.items[0].id == tracked_book.id
            mock_service.list_tracked_books.assert_called_once_with(status=None)


class TestGetTrackedBook:
    """Test get_tracked_book endpoint."""

    def test_get_tracked_book_success(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test get_tracked_book returns book when found (covers lines 139-140).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_tracked_book.return_value = tracked_book
            mock_service_class.return_value = mock_service

            result = tracked_books.get_tracked_book(
                tracked_book_id=1,
                session=session,
            )

            assert isinstance(result, TrackedBookRead)
            assert result.id == tracked_book.id
            mock_service.get_tracked_book.assert_called_once_with(1)

    def test_get_tracked_book_not_found(self, session: DummySession) -> None:
        """Test get_tracked_book raises 404 when not found (covers lines 141-143).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_tracked_book.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tracked_books.get_tracked_book(
                    tracked_book_id=999,
                    session=session,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCreateTrackedBook:
    """Test create_tracked_book endpoint."""

    def test_create_tracked_book_success(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test create_tracked_book creates book successfully (covers lines 177-179).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        create_data = TrackedBookCreate(
            title="Test Book",
            author="Test Author",
        )

        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_tracked_book.return_value = tracked_book
            mock_service_class.return_value = mock_service

            result = tracked_books.create_tracked_book(
                data=create_data,
                session=session,
            )

            assert isinstance(result, TrackedBookRead)
            assert result.id == tracked_book.id
            mock_service.create_tracked_book.assert_called_once_with(create_data)

    def test_create_tracked_book_value_error(self, session: DummySession) -> None:
        """Test create_tracked_book handles ValueError (covers lines 180-184).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        create_data = TrackedBookCreate(
            title="Test Book",
            author="Test Author",
        )

        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_tracked_book.side_effect = ValueError("Already tracked")
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tracked_books.create_tracked_book(
                    data=create_data,
                    session=session,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == "Already tracked"

    def test_create_tracked_book_generic_exception(self, session: DummySession) -> None:
        """Test create_tracked_book handles generic Exception (covers lines 185-189).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        create_data = TrackedBookCreate(
            title="Test Book",
            author="Test Author",
        )

        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_tracked_book.side_effect = RuntimeError("DB Error")
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tracked_books.create_tracked_book(
                    data=create_data,
                    session=session,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create tracked book" in str(exc_info.value.detail)


class TestUpdateTrackedBook:
    """Test update_tracked_book endpoint."""

    def test_update_tracked_book_success(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test update_tracked_book updates book successfully (covers lines 222-225).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        update_data = TrackedBookUpdate(status=TrackedBookStatus.SEARCHING)

        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_tracked_book.return_value = tracked_book
            mock_service_class.return_value = mock_service

            result = tracked_books.update_tracked_book(
                tracked_book_id=1,
                data=update_data,
                session=session,
            )

            assert isinstance(result, TrackedBookRead)
            mock_service.update_tracked_book.assert_called_once_with(1, update_data)

    def test_update_tracked_book_not_found(self, session: DummySession) -> None:
        """Test update_tracked_book raises 404 when not found (covers lines 224).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        update_data = TrackedBookUpdate(status=TrackedBookStatus.SEARCHING)

        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_tracked_book.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tracked_books.update_tracked_book(
                    tracked_book_id=999,
                    data=update_data,
                    session=session,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteTrackedBook:
    """Test delete_tracked_book endpoint."""

    def test_delete_tracked_book_success(self, session: DummySession) -> None:
        """Test delete_tracked_book deletes book successfully (covers line 251).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_tracked_book.return_value = True
            mock_service_class.return_value = mock_service

            result = tracked_books.delete_tracked_book(
                tracked_book_id=1,
                session=session,
            )

            assert result is None
            mock_service.delete_tracked_book.assert_called_once_with(1)

    def test_delete_tracked_book_not_found(self, session: DummySession) -> None:
        """Test delete_tracked_book raises 404 when not found (covers lines 252-253).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_tracked_book.return_value = False
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tracked_books.delete_tracked_book(
                    tracked_book_id=999,
                    session=session,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetTrackedBookStatus:
    """Test get_tracked_book_status endpoint."""

    def test_get_tracked_book_status_success(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test get_tracked_book_status returns status (covers lines 279-282).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.check_status.return_value = tracked_book
            mock_service_class.return_value = mock_service

            result = tracked_books.get_tracked_book_status(
                tracked_book_id=1,
                session=session,
            )

            assert isinstance(result, TrackedBookStatusResponse)
            assert result.id == tracked_book.id
            assert result.status == tracked_book.status
            mock_service.check_status.assert_called_once_with(1)

    def test_get_tracked_book_status_not_found(self, session: DummySession) -> None:
        """Test get_tracked_book_status raises 404 when not found (covers lines 281).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        with patch(
            "bookcard.api.routes.tracked_books.TrackedBookService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.check_status.return_value = None
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                tracked_books.get_tracked_book_status(
                    tracked_book_id=999,
                    session=session,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
