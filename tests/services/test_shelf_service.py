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

"""Tests for shelf service."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from bookcard.models.shelves import BookShelfLink, Shelf
from bookcard.repositories.shelf_repository import (
    BookShelfLinkRepository,
    ShelfRepository,
)
from bookcard.services.shelf_service import ShelfService
from tests.conftest import DummySession


def test_shelf_service_init() -> None:
    """Test ShelfService initialization (covers lines 55-66)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        assert service._session is session
        assert service._shelf_repo is shelf_repo
        assert service._link_repo is link_repo
        assert service._data_directory == Path(tmpdir)
        assert (Path(tmpdir) / "shelves").exists()


def test_ensure_data_directory_exists() -> None:
    """Test _ensure_data_directory_exists creates directories (covers lines 68-71)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )
        # Directories should already exist from init
        assert service._data_directory.exists()
        assert (service._data_directory / "shelves").exists()


def test_get_shelf_directory() -> None:
    """Test _get_shelf_directory returns correct path (covers line 86)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )
        shelf_dir = service._get_shelf_directory(123)
        assert shelf_dir == Path(tmpdir) / "shelves" / "123"


def test_create_shelf_success() -> None:
    """Test create_shelf succeeds with valid parameters (covers lines 119-136)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Mock check_name_unique to return True (name is unique)
        with patch.object(shelf_repo, "check_name_unique", return_value=True):
            shelf = service.create_shelf(
                library_id=1,
                user_id=1,
                name="My Shelf",
                is_public=False,
                description="Test description",
            )

            assert shelf.name == "My Shelf"
            assert shelf.description == "Test description"
            assert shelf.is_public is False
            assert shelf.is_active is True
            assert shelf.user_id == 1
            assert shelf.library_id == 1
            assert shelf in session.added
            assert session.flush_count > 0


def test_create_shelf_name_conflict() -> None:
    """Test create_shelf raises ValueError when name already exists (covers lines 119-121)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Mock check_name_unique to return False (name already exists)
        with (
            patch.object(shelf_repo, "check_name_unique", return_value=False),
            pytest.raises(ValueError, match="Shelf name 'My Shelf' already exists"),
        ):
            service.create_shelf(
                library_id=1,
                user_id=1,
                name="My Shelf",
                is_public=False,
            )


def test_update_shelf_success() -> None:
    """Test update_shelf succeeds with valid parameters (covers lines 169-196)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="Original Name",
            description="Original description",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        # Mock check_name_unique to return True
        with patch.object(shelf_repo, "check_name_unique", return_value=True):
            updated = service.update_shelf(
                shelf_id=1,
                user_id=1,
                name="Updated Name",
                description="Updated description",
                is_public=True,
            )

            assert updated.name == "Updated Name"
            assert updated.description == "Updated description"
            assert updated.is_public is True
            assert session.flush_count > 0


def test_update_shelf_not_found() -> None:
    """Test update_shelf raises ValueError when shelf not found (covers lines 169-172)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with pytest.raises(ValueError, match="Shelf 999 not found"):
            service.update_shelf(shelf_id=999, user_id=1, name="New Name")


def test_update_shelf_permission_denied() -> None:
    """Test update_shelf raises ValueError when permission denied (covers lines 174-176)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,  # Owned by user 1
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with pytest.raises(
            ValueError, match="Permission denied: cannot edit this shelf"
        ):
            service.update_shelf(
                shelf_id=1, user_id=2, name="New Name"
            )  # User 2 tries to edit


def test_update_shelf_name_conflict() -> None:
    """Test update_shelf raises ValueError when new name conflicts (covers lines 179-187)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="Original Name",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        # Mock check_name_unique to return False (name conflict)
        with (
            patch.object(shelf_repo, "check_name_unique", return_value=False),
            pytest.raises(
                ValueError, match="Shelf name 'Conflict Name' already exists"
            ),
        ):
            service.update_shelf(shelf_id=1, user_id=1, name="Conflict Name")


def test_update_shelf_partial_update() -> None:
    """Test update_shelf updates only provided fields (covers lines 189-192)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="Original Name",
            description="Original description",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with patch.object(shelf_repo, "check_name_unique", return_value=True):
            updated = service.update_shelf(
                shelf_id=1,
                user_id=1,
                description="New description",
            )

            assert updated.name == "Original Name"  # Unchanged
            assert updated.description == "New description"  # Changed
            assert updated.is_public is False  # Unchanged


def test_delete_shelf_success() -> None:
    """Test delete_shelf succeeds (covers lines 213-226)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        # Mock delete_by_shelf to avoid actual deletion
        with patch.object(link_repo, "delete_by_shelf"):
            service.delete_shelf(shelf_id=1, user_id=1)

            assert shelf in session.deleted
            assert session.flush_count > 0


def test_delete_shelf_not_found() -> None:
    """Test delete_shelf raises ValueError when shelf not found (covers lines 213-216)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with pytest.raises(ValueError, match="Shelf 999 not found"):
            service.delete_shelf(shelf_id=999, user_id=1)


def test_delete_shelf_permission_denied() -> None:
    """Test delete_shelf raises ValueError when permission denied (covers lines 218-220)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with pytest.raises(
            ValueError, match="Permission denied: cannot delete this shelf"
        ):
            service.delete_shelf(shelf_id=1, user_id=2)  # User 2 tries to delete


def test_add_book_to_shelf_success() -> None:
    """Test add_book_to_shelf succeeds (covers lines 255-283)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        # Mock repository methods
        with (
            patch.object(link_repo, "find_by_shelf_and_book", return_value=None),
            patch.object(link_repo, "get_max_order", return_value=5),
        ):
            link = service.add_book_to_shelf(shelf_id=1, book_id=100, user_id=1)

            assert link.shelf_id == 1
            assert link.book_id == 100
            assert link.order == 6  # max_order + 1
            assert link in session.added
            assert session.flush_count > 0


def test_add_book_to_shelf_not_found() -> None:
    """Test add_book_to_shelf raises ValueError when shelf not found (covers lines 255-258)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with pytest.raises(ValueError, match="Shelf 999 not found"):
            service.add_book_to_shelf(shelf_id=999, book_id=100, user_id=1)


def test_add_book_to_shelf_permission_denied() -> None:
    """Test add_book_to_shelf raises ValueError when permission denied (covers lines 260-262)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with pytest.raises(
            ValueError, match="Permission denied: cannot add books to this shelf"
        ):
            service.add_book_to_shelf(shelf_id=1, book_id=100, user_id=2)


def test_add_book_to_shelf_already_exists() -> None:
    """Test add_book_to_shelf raises ValueError when book already in shelf (covers lines 265-268)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        existing_link = BookShelfLink(
            shelf_id=1,
            book_id=100,
            order=0,
            date_added=datetime.now(UTC),
        )

        with (
            patch.object(
                link_repo, "find_by_shelf_and_book", return_value=existing_link
            ),
            pytest.raises(ValueError, match="Book 100 is already in shelf My Shelf"),
        ):
            service.add_book_to_shelf(shelf_id=1, book_id=100, user_id=1)


def test_remove_book_from_shelf_success() -> None:
    """Test remove_book_from_shelf succeeds (covers lines 307-325)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        link = BookShelfLink(
            id=1,
            shelf_id=1,
            book_id=100,
            order=0,
            date_added=datetime.now(UTC),
        )

        with patch.object(link_repo, "find_by_shelf_and_book", return_value=link):
            service.remove_book_from_shelf(shelf_id=1, book_id=100, user_id=1)

            assert link in session.deleted
            assert session.flush_count > 0


def test_remove_book_from_shelf_not_found() -> None:
    """Test remove_book_from_shelf raises ValueError when shelf not found (covers lines 307-310)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with pytest.raises(ValueError, match="Shelf 999 not found"):
            service.remove_book_from_shelf(shelf_id=999, book_id=100, user_id=1)


def test_remove_book_from_shelf_permission_denied() -> None:
    """Test remove_book_from_shelf raises ValueError when permission denied (covers lines 312-314)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with pytest.raises(
            ValueError, match="Permission denied: cannot remove books from this shelf"
        ):
            service.remove_book_from_shelf(shelf_id=1, book_id=100, user_id=2)


def test_remove_book_from_shelf_book_not_in_shelf() -> None:
    """Test remove_book_from_shelf raises ValueError when book not in shelf (covers lines 316-319)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with (
            patch.object(link_repo, "find_by_shelf_and_book", return_value=None),
            pytest.raises(ValueError, match="Book 100 is not in shelf My Shelf"),
        ):
            service.remove_book_from_shelf(shelf_id=1, book_id=100, user_id=1)


def test_reorder_books_success() -> None:
    """Test reorder_books succeeds (covers lines 349-362)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        book_orders = {100: 0, 101: 1, 102: 2}

        with patch.object(link_repo, "reorder_books"):
            service.reorder_books(shelf_id=1, book_orders=book_orders, user_id=1)

            assert session.flush_count > 0


def test_reorder_books_not_found() -> None:
    """Test reorder_books raises ValueError when shelf not found (covers lines 349-352)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with pytest.raises(ValueError, match="Shelf 999 not found"):
            service.reorder_books(shelf_id=999, book_orders={}, user_id=1)


def test_reorder_books_permission_denied() -> None:
    """Test reorder_books raises ValueError when permission denied (covers lines 354-356)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with pytest.raises(
            ValueError, match="Permission denied: cannot reorder books in this shelf"
        ):
            service.reorder_books(shelf_id=1, book_orders={100: 0}, user_id=2)


def test_can_edit_shelf_private_owner() -> None:
    """Test can_edit_shelf returns True for private shelf owner (covers lines 387-388)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )

        assert service.can_edit_shelf(shelf, user_id=1, is_admin=False) is True
        assert service.can_edit_shelf(shelf, user_id=2, is_admin=False) is False


def test_can_edit_shelf_public_owner_or_admin() -> None:
    """Test can_edit_shelf returns True for public shelf owner or admin (covers lines 390-392)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=True,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )

        assert service.can_edit_shelf(shelf, user_id=1, is_admin=False) is True
        assert service.can_edit_shelf(shelf, user_id=1, is_admin=True) is True
        assert service.can_edit_shelf(shelf, user_id=2, is_admin=True) is True
        assert service.can_edit_shelf(shelf, user_id=2, is_admin=False) is False


def test_can_view_shelf_public() -> None:
    """Test can_view_shelf returns True for public shelves (covers lines 414-415)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=True,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )

        assert service.can_view_shelf(shelf, user_id=None) is True
        assert service.can_view_shelf(shelf, user_id=1) is True
        assert service.can_view_shelf(shelf, user_id=2) is True


def test_can_view_shelf_private() -> None:
    """Test can_view_shelf returns True only for private shelf owner (covers lines 417-420)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )

        assert service.can_view_shelf(shelf, user_id=None) is False
        assert service.can_view_shelf(shelf, user_id=1) is True
        assert service.can_view_shelf(shelf, user_id=2) is False


def test_list_user_shelves() -> None:
    """Test list_user_shelves returns shelves (covers line 444)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelves = [
            Shelf(
                id=1,
                name="Shelf 1",
                is_public=False,
                user_id=1,
                library_id=1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                last_modified=datetime.now(UTC),
            ),
        ]

        with patch.object(
            shelf_repo,
            "find_by_library_and_user",
            return_value=shelves,
        ):
            result = service.list_user_shelves(
                library_id=1, user_id=1, include_public=True
            )
            assert result == shelves


def test_sync_shelf_status_with_library() -> None:
    """Test sync_shelf_status_with_library updates shelf status (covers line 467)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with patch.object(shelf_repo, "sync_active_status_for_library") as mock_sync:
            service.sync_shelf_status_with_library(library_id=1, is_active=False)
            mock_sync.assert_called_once_with(1, False)


def test_validate_cover_picture_file_valid() -> None:
    """Test _validate_cover_picture_file accepts valid extensions (covers lines 482-487)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Valid extensions should not raise
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
            service._validate_cover_picture_file(f"cover{ext}")


def test_validate_cover_picture_file_invalid() -> None:
    """Test _validate_cover_picture_file raises ValueError for invalid extensions (covers lines 485-487)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with pytest.raises(ValueError, match="invalid_file_type"):
            service._validate_cover_picture_file("cover.txt")

        with pytest.raises(ValueError, match="invalid_file_type"):
            service._validate_cover_picture_file("cover")  # No extension


def test_delete_old_cover_picture_empty_path() -> None:
    """Test _delete_old_cover_picture handles empty path (covers lines 497-498)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Should not raise with empty path
        service._delete_old_cover_picture("")


def test_delete_old_cover_picture_absolute_path() -> None:
    """Test _delete_old_cover_picture handles absolute path (covers lines 501-504)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Create a temporary file
        test_file = Path(tmpdir) / "test.jpg"
        test_file.write_bytes(b"test content")

        # Should delete absolute path
        service._delete_old_cover_picture(str(test_file))
        assert not test_file.exists()


def test_delete_old_cover_picture_relative_path() -> None:
    """Test _delete_old_cover_picture handles relative path (covers lines 506-509)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Create a file in the data directory
        test_file = Path(tmpdir) / "shelves" / "1" / "cover.jpg"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_bytes(b"test content")

        # Should delete relative path
        service._delete_old_cover_picture("shelves/1/cover.jpg")
        assert not test_file.exists()


def test_save_cover_picture_file_success() -> None:
    """Test _save_cover_picture_file succeeds (covers lines 538-572)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf_dir = Path(tmpdir) / "shelves" / "1"
        shelf_dir.mkdir(parents=True, exist_ok=True)

        file_content = b"test image content"
        filename = "cover.jpg"

        result_path = service._save_cover_picture_file(
            shelf_dir, filename, file_content
        )

        assert result_path.exists()
        assert result_path.read_bytes() == file_content
        assert result_path.name == filename


def test_save_cover_picture_file_write_error() -> None:
    """Test _save_cover_picture_file raises ValueError on write error (covers lines 545-550)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf_dir = Path(tmpdir) / "shelves" / "1"
        shelf_dir.mkdir(parents=True, exist_ok=True)

        # Mock write_bytes to raise OSError
        with (
            patch.object(Path, "write_bytes", side_effect=OSError("Permission denied")),
            pytest.raises(ValueError, match="failed_to_save_file"),
        ):
            service._save_cover_picture_file(shelf_dir, "cover.jpg", b"content")


def test_save_cover_picture_file_not_exists_after_write() -> None:
    """Test _save_cover_picture_file raises ValueError if file doesn't exist after write (covers lines 553-563)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf_dir = Path(tmpdir) / "shelves" / "1"
        shelf_dir.mkdir(parents=True, exist_ok=True)

        # Mock exists to return False after write
        with (
            patch.object(Path, "write_bytes"),
            patch.object(Path, "exists", return_value=False),
            pytest.raises(ValueError, match="failed_to_save_file"),
        ):
            service._save_cover_picture_file(shelf_dir, "cover.jpg", b"content")


def test_upload_cover_picture_success() -> None:
    """Test upload_cover_picture succeeds (covers lines 612-643)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            cover_picture=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        file_content = b"test image content"
        filename = "cover.jpg"

        result = service.upload_cover_picture(
            shelf_id=1,
            user_id=1,
            file_content=file_content,
            filename=filename,
        )

        assert result.cover_picture is not None
        # On Windows, paths use backslashes, so normalize for comparison
        cover_picture_str = result.cover_picture.replace("\\", "/")
        assert "shelves/1/cover.jpg" in cover_picture_str
        assert session.flush_count > 0


def test_upload_cover_picture_not_found() -> None:
    """Test upload_cover_picture raises ValueError when shelf not found (covers lines 612-615)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with pytest.raises(ValueError, match="shelf_not_found"):
            service.upload_cover_picture(
                shelf_id=999,
                user_id=1,
                file_content=b"content",
                filename="cover.jpg",
            )


def test_upload_cover_picture_permission_denied() -> None:
    """Test upload_cover_picture raises PermissionError when user doesn't own shelf (covers lines 617-619)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with pytest.raises(PermissionError, match="permission_denied"):
            service.upload_cover_picture(
                shelf_id=1,
                user_id=2,  # Different user
                file_content=b"content",
                filename="cover.jpg",
            )


def test_upload_cover_picture_deletes_old() -> None:
    """Test upload_cover_picture deletes old cover picture (covers lines 625-626)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Create old cover picture
        old_cover_path = Path(tmpdir) / "shelves" / "1" / "old_cover.jpg"
        old_cover_path.parent.mkdir(parents=True, exist_ok=True)
        old_cover_path.write_bytes(b"old content")

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            cover_picture="shelves/1/old_cover.jpg",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        result = service.upload_cover_picture(
            shelf_id=1,
            user_id=1,
            file_content=b"new content",
            filename="new_cover.jpg",
        )

        # Old file should be deleted
        assert not old_cover_path.exists()
        assert result.cover_picture is not None


def test_delete_cover_picture_success() -> None:
    """Test delete_cover_picture succeeds (covers lines 673-699)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Create cover picture file
        cover_path = Path(tmpdir) / "shelves" / "1" / "cover.jpg"
        cover_path.parent.mkdir(parents=True, exist_ok=True)
        cover_path.write_bytes(b"test content")

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            cover_picture="shelves/1/cover.jpg",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        result = service.delete_cover_picture(shelf_id=1, user_id=1)

        assert result.cover_picture is None
        assert not cover_path.exists()
        assert session.flush_count > 0


def test_delete_cover_picture_not_found() -> None:
    """Test delete_cover_picture raises ValueError when shelf not found (covers lines 673-676)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        with pytest.raises(ValueError, match="shelf_not_found"):
            service.delete_cover_picture(shelf_id=999, user_id=1)


def test_delete_cover_picture_permission_denied() -> None:
    """Test delete_cover_picture raises PermissionError when user doesn't own shelf (covers lines 678-680)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        with pytest.raises(PermissionError, match="permission_denied"):
            service.delete_cover_picture(shelf_id=1, user_id=2)


def test_delete_cover_picture_absolute_path() -> None:
    """Test delete_cover_picture handles absolute path (covers lines 685-687)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        # Create cover picture with absolute path
        cover_path = Path(tmpdir) / "absolute_cover.jpg"
        cover_path.write_bytes(b"test content")

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            cover_picture=str(cover_path),  # Absolute path
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        result = service.delete_cover_picture(shelf_id=1, user_id=1)

        assert result.cover_picture is None
        assert not cover_path.exists()


def test_delete_cover_picture_no_cover() -> None:
    """Test delete_cover_picture handles shelf with no cover picture (covers lines 696-698)."""
    session = DummySession()
    shelf_repo = ShelfRepository(session)  # type: ignore[arg-type]
    link_repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        service = ShelfService(
            session,  # type: ignore[arg-type]
            shelf_repo,
            link_repo,
            data_directory=tmpdir,
        )

        shelf = Shelf(
            id=1,
            name="My Shelf",
            is_public=False,
            user_id=1,
            library_id=1,
            cover_picture=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        session.add(shelf)

        result = service.delete_cover_picture(shelf_id=1, user_id=1)

        assert result.cover_picture is None
        assert session.flush_count > 0
