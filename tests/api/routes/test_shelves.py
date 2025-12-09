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

"""Tests for shelf routes."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from fastapi.responses import FileResponse, Response

import fundamental.api.routes.shelves as shelves
from fundamental.api.schemas.shelves import (
    ShelfCreate,
    ShelfReorderRequest,
    ShelfUpdate,
)
from fundamental.models.auth import User
from fundamental.models.config import Library
from fundamental.models.shelves import BookShelfLink, Shelf
from tests.conftest import DummySession


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

    monkeypatch.setattr(shelves, "PermissionService", MockPermissionService)


class MockShelfService:
    """Mock ShelfService for testing."""

    def __init__(self) -> None:
        self.create_shelf_result: Shelf | None = None
        self.update_shelf_result: Shelf | None = None
        self.delete_shelf_exception: Exception | None = None
        self.add_book_to_shelf_exception: Exception | None = None
        self.remove_book_from_shelf_exception: Exception | None = None
        self.reorder_books_exception: Exception | None = None
        self.upload_cover_picture_result: Shelf | None = None
        self.upload_cover_picture_exception: Exception | None = None
        self.delete_cover_picture_result: Shelf | None = None
        self.delete_cover_picture_exception: Exception | None = None
        self.list_user_shelves_result: list[Shelf] = []
        self.can_view_shelf_result: bool = True
        self.can_edit_shelf_result: bool = True

    def create_shelf(
        self,
        library_id: int,
        user_id: int,
        name: str,
        is_public: bool,
        description: str | None = None,
        shelf_type: object | None = None,
    ) -> Shelf:
        """Mock create_shelf method."""
        if self.create_shelf_result is None:
            raise ValueError("create_shelf not mocked")
        return self.create_shelf_result

    def update_shelf(
        self,
        shelf_id: int,
        user_id: int,
        name: str | None = None,
        description: str | None = None,
        is_public: bool | None = None,
        shelf_type: object | None = None,
    ) -> Shelf:
        """Mock update_shelf method."""
        if self.update_shelf_result is None:
            raise ValueError("update_shelf not mocked")
        return self.update_shelf_result

    def delete_shelf(self, shelf_id: int, user_id: int) -> None:
        """Mock delete_shelf method."""
        if self.delete_shelf_exception:
            raise self.delete_shelf_exception

    def add_book_to_shelf(
        self,
        shelf_id: int,
        book_id: int,
        user_id: int,
    ) -> BookShelfLink:
        """Mock add_book_to_shelf method."""
        if self.add_book_to_shelf_exception:
            raise self.add_book_to_shelf_exception
        return BookShelfLink(
            shelf_id=shelf_id,
            book_id=book_id,
            order=0,
            date_added=datetime.now(UTC),
        )

    def remove_book_from_shelf(
        self,
        shelf_id: int,
        book_id: int,
        user_id: int,
    ) -> None:
        """Mock remove_book_from_shelf method."""
        if self.remove_book_from_shelf_exception:
            raise self.remove_book_from_shelf_exception

    def reorder_books(
        self,
        shelf_id: int,
        book_orders: dict[int, int],
        user_id: int,
    ) -> None:
        """Mock reorder_books method."""
        if self.reorder_books_exception:
            raise self.reorder_books_exception

    def upload_cover_picture(
        self,
        shelf_id: int,
        user_id: int,
        file_content: bytes,
        filename: str,
    ) -> Shelf:
        """Mock upload_cover_picture method."""
        if self.upload_cover_picture_exception:
            raise self.upload_cover_picture_exception
        if self.upload_cover_picture_result is None:
            raise ValueError("upload_cover_picture not mocked")
        return self.upload_cover_picture_result

    def delete_cover_picture(
        self,
        shelf_id: int,
        user_id: int,
    ) -> Shelf:
        """Mock delete_cover_picture method."""
        if self.delete_cover_picture_exception:
            raise self.delete_cover_picture_exception
        if self.delete_cover_picture_result is None:
            raise ValueError("delete_cover_picture not mocked")
        return self.delete_cover_picture_result

    def list_user_shelves(
        self,
        library_id: int,
        user_id: int,
        include_public: bool = True,
    ) -> list[Shelf]:
        """Mock list_user_shelves method."""
        return self.list_user_shelves_result

    def can_view_shelf(self, shelf: Shelf, user_id: int | None) -> bool:
        """Mock can_view_shelf method."""
        return self.can_view_shelf_result

    def can_edit_shelf(self, shelf: Shelf, user_id: int, is_admin: bool) -> bool:
        """Mock can_edit_shelf method."""
        return self.can_edit_shelf_result


@pytest.fixture
def mock_user() -> User:
    """Create a mock user."""
    return User(
        id=1, username="testuser", email="test@example.com", password_hash="hash"
    )


@pytest.fixture
def mock_library() -> Library:
    """Create a mock library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def mock_shelf() -> Shelf:
    """Create a mock shelf."""
    return Shelf(
        id=1,
        name="Test Shelf",
        description="Test description",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )


def test_shelf_service_dependency() -> None:
    """Test _shelf_service dependency (covers lines 74-77)."""
    session = DummySession()
    mock_request = MagicMock(spec=Request)
    mock_config = MagicMock()
    mock_config.data_directory = "/data"
    mock_request.app.state.config = mock_config

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
        patch("fundamental.api.routes.shelves.ShelfService") as mock_service_class,
    ):
        _service = shelves._shelf_service(mock_request, session)  # type: ignore[arg-type]

        mock_repo_class.assert_called_once_with(session)
        mock_link_repo_class.assert_called_once_with(session)
        mock_service_class.assert_called_once()


def test_get_active_library_id_no_library() -> None:
    """Test _get_active_library_id raises 404 when no active library (covers lines 105-113)."""
    session = DummySession()

    with (
        patch("fundamental.api.routes.shelves.LibraryRepository") as mock_repo_class,
        patch("fundamental.api.routes.shelves.LibraryService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = None
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            shelves._get_active_library_id(session)  # type: ignore[arg-type]
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]  # type: ignore[attr-defined]
        assert exc_info.value.detail == "no_active_library"  # type: ignore[attr-defined]


def test_get_active_library_id_no_id() -> None:
    """Test _get_active_library_id raises 404 when library has no ID (covers lines 115-119)."""
    session = DummySession()
    library = Library(
        id=None,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    with (
        patch("fundamental.api.routes.shelves.LibraryRepository") as mock_repo_class,
        patch("fundamental.api.routes.shelves.LibraryService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            shelves._get_active_library_id(session)  # type: ignore[arg-type]
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]  # type: ignore[attr-defined]
        assert exc_info.value.detail == "no_active_library"  # type: ignore[attr-defined]


def test_get_active_library_id_success() -> None:
    """Test _get_active_library_id returns library ID (covers line 121)."""
    session = DummySession()
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    with (
        patch("fundamental.api.routes.shelves.LibraryRepository") as mock_repo_class,
        patch("fundamental.api.routes.shelves.LibraryService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service.get_active_library.return_value = library
        mock_service_class.return_value = mock_service

        result = shelves._get_active_library_id(session)  # type: ignore[arg-type]
        assert result == 1


def test_create_shelf_success(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create_shelf succeeds (covers lines 158-191)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.create_shelf_result = mock_shelf
    _mock_permission_service(monkeypatch)

    with (
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = []
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.create_shelf(
            shelf_data=ShelfCreate(name="Test Shelf", is_public=False),
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert result.id == 1
        assert result.name == "Test Shelf"
        assert result.book_count == 0


def test_create_shelf_no_id(
    mock_user: User, mock_library: Library, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test create_shelf raises 500 when shelf has no ID (covers lines 170-174)."""
    session = DummySession()
    shelf_no_id = Shelf(
        id=None,
        name="Test Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    mock_service = MockShelfService()
    mock_service.create_shelf_result = shelf_no_id
    _mock_permission_service(monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        shelves.create_shelf(
            shelf_data=ShelfCreate(name="Test Shelf", is_public=False),
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR  # type: ignore[attr-defined]


def test_create_shelf_value_error(
    mock_user: User, mock_library: Library, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test create_shelf handles ValueError (covers lines 192-196)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.create_shelf_result = None
    _mock_permission_service(monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        shelves.create_shelf(
            shelf_data=ShelfCreate(name="Test Shelf", is_public=False),
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]


def test_list_shelves_success(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test list_shelves succeeds (covers lines 222-251)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.list_user_shelves_result = [mock_shelf]
    _mock_permission_service(monkeypatch)

    with (
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = []
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.list_shelves(
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert len(result.shelves) == 1
        assert result.total == 1
        assert result.shelves[0].id == 1


def test_get_shelf_success(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_shelf succeeds (covers lines 285-316)."""
    session = DummySession()
    mock_service = MockShelfService()
    _mock_permission_service(monkeypatch)

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = []
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.get_shelf(
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert result.id == 1
        assert result.name == "Test Shelf"


def test_get_shelf_not_found(mock_user: User, mock_library: Library) -> None:
    """Test get_shelf raises 404 when shelf not found (covers lines 287-291)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.get_shelf(
                shelf_id=999,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_get_shelf_permission_denied(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf raises 403 when permission denied (covers lines 293-297)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.can_view_shelf_result = False

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.get_shelf(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN  # type: ignore[attr-defined]


def test_get_shelf_wrong_library(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf raises 404 when shelf belongs to different library (covers lines 300-304)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_shelf.library_id = 2  # Different library

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.get_shelf(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_get_shelf_no_id(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_shelf raises 500 when shelf has no ID (covers lines 310-314)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_shelf.id = None
    _mock_permission_service(monkeypatch)

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = []
        mock_link_repo_class.return_value = mock_link_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.get_shelf(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR  # type: ignore[attr-defined]


def test_update_shelf_success(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test update_shelf succeeds (covers lines 368-409)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.update_shelf_result = mock_shelf
    _mock_permission_service(monkeypatch)

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = []
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.update_shelf(
            shelf_id=1,
            shelf_data=ShelfUpdate(name="Updated Shelf"),
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert result.id == 1


def test_update_shelf_not_found(mock_user: User, mock_library: Library) -> None:
    """Test update_shelf raises 404 when shelf not found (covers lines 370-374)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.update_shelf(
                shelf_id=999,
                shelf_data=ShelfUpdate(name="Updated Shelf"),
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_update_shelf_wrong_library(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test update_shelf raises 404 when shelf belongs to different library (covers lines 370-374)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_shelf.library_id = 2

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.update_shelf(
                shelf_id=1,
                shelf_data=ShelfUpdate(name="Updated Shelf"),
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_update_shelf_value_error(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test update_shelf handles ValueError (covers lines 410-414)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.update_shelf_result = None
    _mock_permission_service(monkeypatch)

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.update_shelf(
                shelf_id=1,
                shelf_data=ShelfUpdate(name="Updated Shelf"),
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]


def test_update_shelf_no_id_after_update(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test update_shelf raises 500 when shelf has no ID after update (covers lines 388-392)."""
    session = DummySession()
    shelf_no_id = Shelf(
        id=None,
        name="Updated Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    mock_service = MockShelfService()
    mock_service.update_shelf_result = shelf_no_id
    _mock_permission_service(monkeypatch)

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.update_shelf(
                shelf_id=1,
                shelf_data=ShelfUpdate(name="Updated Shelf"),
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR  # type: ignore[attr-defined]


def test_delete_shelf_success(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test delete_shelf succeeds (covers lines 444-459)."""
    session = DummySession()
    mock_service = MockShelfService()
    _mock_permission_service(monkeypatch)

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        result = shelves.delete_shelf(
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert result is None


def test_delete_shelf_not_found(mock_user: User, mock_library: Library) -> None:
    """Test delete_shelf raises 404 when shelf not found (covers lines 446-450)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.delete_shelf(
                shelf_id=999,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_delete_shelf_value_error(
    mock_user: User,
    mock_shelf: Shelf,
    mock_library: Library,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test delete_shelf handles ValueError (covers lines 455-459)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.delete_shelf_exception = ValueError("Shelf not found")
    _mock_permission_service(monkeypatch)

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.delete_shelf(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]


def test_add_book_to_shelf_success(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test add_book_to_shelf succeeds (covers lines 495-510)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        result = shelves.add_book_to_shelf(
            shelf_id=1,
            book_id=100,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert result is None


def test_add_book_to_shelf_not_found(mock_user: User, mock_library: Library) -> None:
    """Test add_book_to_shelf raises 404 when shelf not found (covers lines 497-501)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.add_book_to_shelf(
                shelf_id=999,
                book_id=100,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_add_book_to_shelf_value_error(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test add_book_to_shelf handles ValueError (covers lines 506-510)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.add_book_to_shelf_exception = ValueError("Book already in shelf")

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.add_book_to_shelf(
                shelf_id=1,
                book_id=100,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]


def test_remove_book_from_shelf_success(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test remove_book_from_shelf succeeds (covers lines 546-561)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        result = shelves.remove_book_from_shelf(
            shelf_id=1,
            book_id=100,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert result is None


def test_remove_book_from_shelf_not_found(
    mock_user: User, mock_library: Library
) -> None:
    """Test remove_book_from_shelf raises 404 when shelf not found (covers lines 548-552)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.remove_book_from_shelf(
                shelf_id=999,
                book_id=100,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_remove_book_from_shelf_value_error(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test remove_book_from_shelf handles ValueError (covers lines 557-561)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.remove_book_from_shelf_exception = ValueError("Book not in shelf")

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.remove_book_from_shelf(
                shelf_id=1,
                book_id=100,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]


def test_reorder_shelf_books_success(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test reorder_shelf_books succeeds (covers lines 597-616)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        result = shelves.reorder_shelf_books(
            shelf_id=1,
            reorder_data=ShelfReorderRequest(book_orders={100: 0, 101: 1}),
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert result is None


def test_reorder_shelf_books_not_found(mock_user: User, mock_library: Library) -> None:
    """Test reorder_shelf_books raises 404 when shelf not found (covers lines 599-603)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.reorder_shelf_books(
                shelf_id=999,
                reorder_data=ShelfReorderRequest(book_orders={100: 0}),
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_reorder_shelf_books_value_error(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test reorder_shelf_books handles ValueError (covers lines 612-616)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.reorder_books_exception = ValueError("Shelf not found")

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.reorder_shelf_books(
                shelf_id=1,
                reorder_data=ShelfReorderRequest(book_orders={100: 0}),
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]


def test_get_shelf_books_success(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_books succeeds (covers lines 668-704)."""
    session = DummySession()
    mock_service = MockShelfService()

    link1 = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        order=0,
        date_added=datetime.now(UTC),
    )
    link2 = BookShelfLink(
        id=2,
        shelf_id=1,
        book_id=101,
        order=1,
        date_added=datetime.now(UTC),
    )

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = [link1, link2]
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.get_shelf_books(
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
            page=1,
            page_size=20,
            sort_by="order",
            sort_order="asc",
        )

        assert len(result) == 2
        assert 100 in result
        assert 101 in result


def test_get_shelf_books_not_found(mock_user: User, mock_library: Library) -> None:
    """Test get_shelf_books raises 404 when shelf not found (covers lines 670-674)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.get_shelf_books(
                shelf_id=999,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_get_shelf_books_wrong_library(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_books raises 404 when shelf belongs to different library (covers lines 677-681)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_shelf.library_id = 2

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.get_shelf_books(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_get_shelf_books_permission_denied(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_books raises 403 when permission denied (covers lines 683-687)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.can_view_shelf_result = False

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.get_shelf_books(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN  # type: ignore[attr-defined]


def test_get_shelf_books_sort_by_date_added(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_books sorts by date_added (covers lines 695-696)."""
    session = DummySession()
    mock_service = MockShelfService()

    link1 = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        order=0,
        date_added=datetime(2024, 1, 1, tzinfo=UTC),
    )
    link2 = BookShelfLink(
        id=2,
        shelf_id=1,
        book_id=101,
        order=1,
        date_added=datetime(2024, 1, 2, tzinfo=UTC),
    )

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = [link1, link2]
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.get_shelf_books(
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
            page=1,  # Explicitly pass int values
            page_size=20,
            sort_by="date_added",
            sort_order="desc",
        )

        assert result[0] == 101  # Newer first


def test_get_shelf_books_sort_by_book_id(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_books sorts by book_id (covers lines 697-698)."""
    session = DummySession()
    mock_service = MockShelfService()

    link1 = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=200,
        order=0,
        date_added=datetime.now(UTC),
    )
    link2 = BookShelfLink(
        id=2,
        shelf_id=1,
        book_id=100,
        order=1,
        date_added=datetime.now(UTC),
    )

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = [link1, link2]
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.get_shelf_books(
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
            page=1,  # Explicitly pass int values
            page_size=20,
            sort_by="book_id",
            sort_order="asc",
        )

        assert result[0] == 100  # Lower ID first


def test_get_shelf_books_pagination(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_books pagination (covers lines 701-703)."""
    session = DummySession()
    mock_service = MockShelfService()

    links = [
        BookShelfLink(
            id=i,
            shelf_id=1,
            book_id=100 + i,
            order=i,
            date_added=datetime.now(UTC),
        )
        for i in range(10)
    ]

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = links
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.get_shelf_books(
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
            page=2,
            page_size=3,
        )

        assert len(result) == 3
        assert result[0] == 103  # Second page, first item


def test_upload_shelf_cover_picture_success(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture succeeds (covers lines 750-804)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.upload_cover_picture_result = mock_shelf

    mock_file = MagicMock()
    mock_file.filename = "cover.jpg"
    mock_file.file.read.return_value = b"image content"

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = []
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.upload_shelf_cover_picture(
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
            file=mock_file,  # type: ignore[arg-type]
        )

        assert result.id == 1


def test_upload_shelf_cover_picture_not_found(
    mock_user: User, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture raises 404 when shelf not found (covers lines 752-756)."""
    session = DummySession()
    mock_service = MockShelfService()

    mock_file = MagicMock()
    mock_file.filename = "cover.jpg"

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.upload_shelf_cover_picture(
                shelf_id=999,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_upload_shelf_cover_picture_no_filename(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture raises 400 when no filename (covers lines 758-762)."""
    session = DummySession()
    mock_service = MockShelfService()

    mock_file = MagicMock()
    mock_file.filename = None

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.upload_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]


def test_upload_shelf_cover_picture_read_error(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture handles file read error (covers lines 765-770)."""
    session = DummySession()
    mock_service = MockShelfService()

    mock_file = MagicMock()
    mock_file.filename = "cover.jpg"
    mock_file.file.read.side_effect = OSError("Read error")

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.upload_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR  # type: ignore[attr-defined]


def test_upload_shelf_cover_picture_value_error_shelf_not_found(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture handles ValueError shelf_not_found (covers lines 807-808)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.upload_cover_picture_exception = ValueError("shelf_not_found")

    mock_file = MagicMock()
    mock_file.filename = "cover.jpg"
    mock_file.file.read.return_value = b"image content"

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.upload_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )
        assert exc_info.value.status_code == 404  # type: ignore[attr-defined]


def test_upload_shelf_cover_picture_value_error_invalid_file_type(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture handles ValueError invalid_file_type (covers lines 809-810)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.upload_cover_picture_exception = ValueError("invalid_file_type")

    mock_file = MagicMock()
    mock_file.filename = "cover.txt"
    mock_file.file.read.return_value = b"content"

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.upload_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )
        assert exc_info.value.status_code == 400  # type: ignore[attr-defined]


def test_upload_shelf_cover_picture_value_error_failed_to_save(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture handles ValueError failed_to_save_file (covers lines 811-812)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.upload_cover_picture_exception = ValueError(
        "failed_to_save_file: error"
    )

    mock_file = MagicMock()
    mock_file.filename = "cover.jpg"
    mock_file.file.read.return_value = b"image content"

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.upload_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )
        assert exc_info.value.status_code == 500  # type: ignore[attr-defined]


def test_upload_shelf_cover_picture_permission_error(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture handles PermissionError (covers lines 814-818)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.upload_cover_picture_exception = PermissionError("permission_denied")

    mock_file = MagicMock()
    mock_file.filename = "cover.jpg"
    mock_file.file.read.return_value = b"image content"

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.upload_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN  # type: ignore[attr-defined]


def test_upload_shelf_cover_picture_no_id_after_upload(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture raises 500 when shelf has no ID after upload (covers lines 783-787)."""
    session = DummySession()
    shelf_no_id = Shelf(
        id=None,
        name="Test Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    mock_service = MockShelfService()
    mock_service.upload_cover_picture_result = shelf_no_id

    mock_file = MagicMock()
    mock_file.filename = "cover.jpg"
    mock_file.file.read.return_value = b"image content"

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.upload_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR  # type: ignore[attr-defined]


def test_upload_shelf_cover_picture_unexpected_value_error(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test upload_shelf_cover_picture re-raises unexpected ValueError (covers line 813)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.upload_cover_picture_exception = ValueError("unexpected_error")

    mock_file = MagicMock()
    mock_file.filename = "cover.jpg"
    mock_file.file.read.return_value = b"image content"

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(ValueError, match="unexpected_error"):
            shelves.upload_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
                file=mock_file,  # type: ignore[arg-type]
            )


def test_get_shelf_cover_picture_not_found(mock_library: Library) -> None:
    """Test get_shelf_cover_picture returns 404 when shelf not found (covers lines 853-854)."""
    session = DummySession()
    mock_request = MagicMock(spec=Request)

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        result = shelves.get_shelf_cover_picture(
            request=mock_request,
            shelf_id=999,
            session=session,  # type: ignore[arg-type]
            library_id=1,
        )

        assert isinstance(result, Response)
        assert result.status_code == status.HTTP_404_NOT_FOUND


def test_get_shelf_cover_picture_no_cover(
    mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_cover_picture returns 404 when no cover picture (covers lines 856-857)."""
    session = DummySession()
    mock_request = MagicMock(spec=Request)
    mock_shelf.cover_picture = None

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        result = shelves.get_shelf_cover_picture(
            request=mock_request,
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            library_id=1,
        )

        assert isinstance(result, Response)
        assert result.status_code == status.HTTP_404_NOT_FOUND


def test_get_shelf_cover_picture_absolute_path(
    mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_cover_picture handles absolute path (covers lines 861-862)."""
    session = DummySession()
    mock_request = MagicMock(spec=Request)

    with tempfile.TemporaryDirectory() as tmpdir:
        cover_file = Path(tmpdir) / "cover.jpg"
        cover_file.write_bytes(b"image content")
        mock_shelf.cover_picture = str(cover_file)

        with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = mock_shelf
            mock_repo_class.return_value = mock_repo

            result = shelves.get_shelf_cover_picture(
                request=mock_request,
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                library_id=1,
            )

            assert isinstance(result, FileResponse)
            assert result.path == str(cover_file)


def test_get_shelf_cover_picture_relative_path(
    mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_cover_picture handles relative path (covers lines 864-865)."""
    session = DummySession()
    mock_request = MagicMock(spec=Request)

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config = MagicMock()
        mock_config.data_directory = tmpdir
        mock_request.app.state.config = mock_config

        cover_file = Path(tmpdir) / "shelves" / "1" / "cover.jpg"
        cover_file.parent.mkdir(parents=True, exist_ok=True)
        cover_file.write_bytes(b"image content")
        mock_shelf.cover_picture = "shelves/1/cover.jpg"

        with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = mock_shelf
            mock_repo_class.return_value = mock_repo

            result = shelves.get_shelf_cover_picture(
                request=mock_request,
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                library_id=1,
            )

            assert isinstance(result, FileResponse)
            assert result.path == str(cover_file)


def test_get_shelf_cover_picture_file_not_exists(
    mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_cover_picture returns 404 when file doesn't exist (covers lines 867-868)."""
    session = DummySession()
    mock_request = MagicMock(spec=Request)
    mock_shelf.cover_picture = "/nonexistent/cover.jpg"

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        result = shelves.get_shelf_cover_picture(
            request=mock_request,
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            library_id=1,
        )

        assert isinstance(result, Response)
        assert result.status_code == status.HTTP_404_NOT_FOUND


def test_get_shelf_cover_picture_media_types(
    mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test get_shelf_cover_picture sets correct media types (covers lines 870-882)."""
    session = DummySession()
    mock_request = MagicMock(spec=Request)

    media_type_tests = [
        (".jpg", "image/jpeg"),
        (".jpeg", "image/jpeg"),
        (".png", "image/png"),
        (".gif", "image/gif"),
        (".webp", "image/webp"),
        (".svg", "image/svg+xml"),
        (".unknown", "image/jpeg"),  # Default
    ]

    for ext, expected_media_type in media_type_tests:
        with tempfile.TemporaryDirectory() as tmpdir:
            cover_file = Path(tmpdir) / f"cover{ext}"
            cover_file.write_bytes(b"image content")
            mock_shelf.cover_picture = str(cover_file)

            with patch(
                "fundamental.api.routes.shelves.ShelfRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get.return_value = mock_shelf
                mock_repo_class.return_value = mock_repo

                result = shelves.get_shelf_cover_picture(
                    request=mock_request,
                    shelf_id=1,
                    session=session,  # type: ignore[arg-type]
                    library_id=1,
                )

                assert isinstance(result, FileResponse)
                assert result.media_type == expected_media_type


def test_delete_shelf_cover_picture_success(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test delete_shelf_cover_picture succeeds (covers lines 921-959)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.delete_cover_picture_result = mock_shelf

    with (
        patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class,
        patch(
            "fundamental.api.routes.shelves.BookShelfLinkRepository"
        ) as mock_link_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        mock_link_repo = MagicMock()
        mock_link_repo.find_by_shelf.return_value = []
        mock_link_repo_class.return_value = mock_link_repo

        result = shelves.delete_shelf_cover_picture(
            shelf_id=1,
            session=session,  # type: ignore[arg-type]
            current_user=mock_user,
            shelf_service=mock_service,  # type: ignore[arg-type]
            library_id=1,
        )

        assert result.id == 1


def test_delete_shelf_cover_picture_not_found(
    mock_user: User, mock_library: Library
) -> None:
    """Test delete_shelf_cover_picture raises 404 when shelf not found (covers lines 923-927)."""
    session = DummySession()
    mock_service = MockShelfService()

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.delete_shelf_cover_picture(
                shelf_id=999,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]


def test_delete_shelf_cover_picture_value_error_shelf_not_found(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test delete_shelf_cover_picture handles ValueError shelf_not_found (covers lines 962-963)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.delete_cover_picture_exception = ValueError("shelf_not_found")

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.delete_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == 404  # type: ignore[attr-defined]


def test_delete_shelf_cover_picture_permission_error(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test delete_shelf_cover_picture handles PermissionError (covers lines 965-969)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.delete_cover_picture_exception = PermissionError("permission_denied")

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.delete_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN  # type: ignore[attr-defined]


def test_delete_shelf_cover_picture_no_id_after_delete(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test delete_shelf_cover_picture raises 500 when shelf has no ID after delete (covers lines 938-942)."""
    session = DummySession()
    shelf_no_id = Shelf(
        id=None,
        name="Test Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    mock_service = MockShelfService()
    mock_service.delete_cover_picture_result = shelf_no_id

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            shelves.delete_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR  # type: ignore[attr-defined]


def test_delete_shelf_cover_picture_unexpected_value_error(
    mock_user: User, mock_shelf: Shelf, mock_library: Library
) -> None:
    """Test delete_shelf_cover_picture re-raises unexpected ValueError (covers line 964)."""
    session = DummySession()
    mock_service = MockShelfService()
    mock_service.delete_cover_picture_exception = ValueError("unexpected_error")

    with patch("fundamental.api.routes.shelves.ShelfRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_shelf
        mock_repo_class.return_value = mock_repo

        with pytest.raises(ValueError, match="unexpected_error"):
            shelves.delete_shelf_cover_picture(
                shelf_id=1,
                session=session,  # type: ignore[arg-type]
                current_user=mock_user,
                shelf_service=mock_service,  # type: ignore[arg-type]
                library_id=1,
            )
