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

"""Tests for shelf repository."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from bookcard.models.shelves import BookShelfLink, Shelf
from bookcard.repositories.shelf_repository import (
    BookShelfLinkRepository,
    ShelfRepository,
)
from tests.conftest import DummySession


def test_shelf_repository_init() -> None:
    """Test ShelfRepository initialization."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]
    assert repo._session is session


def test_shelf_repository_add() -> None:
    """Test ShelfRepository.add adds shelf to session (covers lines 59-60)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

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

    result = repo.add(shelf)
    assert result is shelf
    assert shelf in session.added


def test_shelf_repository_get() -> None:
    """Test ShelfRepository.get retrieves shelf by ID (covers line 75)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

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

    result = repo.get(1)
    assert result is shelf

    result = repo.get(999)
    assert result is None


def test_shelf_repository_find_by_library_and_user_include_public() -> None:
    """Test find_by_library_and_user with include_public=True (covers lines 100-114)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    shelf1 = Shelf(
        id=1,
        name="Private Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    shelf2 = Shelf(
        id=2,
        name="Public Shelf",
        is_public=True,
        user_id=2,
        library_id=1,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([shelf1, shelf2])
    result = repo.find_by_library_and_user(library_id=1, user_id=1, include_public=True)

    assert len(result) == 2
    assert shelf1 in result
    assert shelf2 in result


def test_shelf_repository_find_by_library_and_user_exclude_public() -> None:
    """Test find_by_library_and_user with include_public=False (covers lines 115-125)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    shelf = Shelf(
        id=1,
        name="Private Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([shelf])
    result = repo.find_by_library_and_user(
        library_id=1, user_id=1, include_public=False
    )

    assert len(result) == 1
    assert shelf in result


def test_shelf_repository_find_by_libraries_and_user_include_public() -> None:
    """Test find_by_libraries_and_user returns shelves across multiple libraries."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    shelf1 = Shelf(
        id=1,
        name="Lib1 Private",
        is_public=False,
        user_id=1,
        library_id=1,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    shelf2 = Shelf(
        id=2,
        name="Lib2 Public",
        is_public=True,
        user_id=2,
        library_id=2,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([shelf1, shelf2])
    result = repo.find_by_libraries_and_user(
        library_ids=[1, 2],
        user_id=1,
        include_public=True,
    )

    assert len(result) == 2
    assert shelf1 in result
    assert shelf2 in result


def test_shelf_repository_find_by_libraries_and_user_exclude_public() -> None:
    """Test find_by_libraries_and_user with include_public=False."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    shelf = Shelf(
        id=1,
        name="My Private",
        is_public=False,
        user_id=1,
        library_id=1,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([shelf])
    result = repo.find_by_libraries_and_user(
        library_ids=[1, 2],
        user_id=1,
        include_public=False,
    )

    assert len(result) == 1
    assert shelf in result


def test_shelf_repository_find_by_libraries_and_user_empty_list() -> None:
    """Test find_by_libraries_and_user with empty library_ids returns empty list."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    result = repo.find_by_libraries_and_user(
        library_ids=[],
        user_id=1,
        include_public=True,
    )

    assert result == []


def test_shelf_repository_find_by_library() -> None:
    """Test find_by_library returns all shelves for a library."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    shelf1 = Shelf(
        id=1,
        name="Shelf 1",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    shelf2 = Shelf(
        id=2,
        name="Shelf 2",
        is_public=True,
        user_id=2,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([shelf1, shelf2])
    result = repo.find_by_library(library_id=1)

    assert len(result) == 2
    assert shelf1 in result
    assert shelf2 in result


def test_shelf_repository_sync_active_status_for_library() -> None:
    """Test sync_active_status_for_library updates all shelves (covers lines 160-164)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    shelf1 = Shelf(
        id=1,
        name="Shelf 1",
        is_public=False,
        user_id=1,
        library_id=1,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    shelf2 = Shelf(
        id=2,
        name="Shelf 2",
        is_public=True,
        user_id=2,
        library_id=1,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    # First call: find_by_library
    session.add_exec_result([shelf1, shelf2])

    repo.sync_active_status_for_library(library_id=1, is_active=False)

    assert shelf1.is_active is False
    assert shelf2.is_active is False
    assert shelf1 in session.added
    assert shelf2 in session.added
    assert session.flush_count > 0


def test_shelf_repository_find_public_shelves() -> None:
    """Test find_public_shelves returns only public shelves (covers lines 179-183)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    public_shelf = Shelf(
        id=1,
        name="Public Shelf",
        is_public=True,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([public_shelf])
    result = repo.find_public_shelves(library_id=1)

    assert len(result) == 1
    assert public_shelf in result


def test_shelf_repository_find_by_name_public() -> None:
    """Test find_by_name for public shelves (covers lines 210-214, 217)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    shelf = Shelf(
        id=1,
        name="Public Shelf",
        is_public=True,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([shelf])
    result = repo.find_by_name(
        library_id=1,
        name="Public Shelf",
        user_id=None,
        is_public=True,
    )

    assert result is shelf


def test_shelf_repository_find_by_name_private_with_user() -> None:
    """Test find_by_name for private shelves with user_id (covers lines 210-216)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    shelf = Shelf(
        id=1,
        name="Private Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([shelf])
    result = repo.find_by_name(
        library_id=1,
        name="Private Shelf",
        user_id=1,
        is_public=False,
    )

    assert result is shelf


def test_shelf_repository_find_by_name_private_no_user() -> None:
    """Test find_by_name for private shelves without user_id (covers lines 210-214, 217)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_name(
        library_id=1,
        name="Private Shelf",
        user_id=None,
        is_public=False,
    )

    assert result is None


def test_shelf_repository_check_name_unique_public_unique() -> None:
    """Test check_name_unique returns True for unique public shelf name (covers lines 247-251, 256-257)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])  # No existing shelf
    result = repo.check_name_unique(
        library_id=1,
        name="New Shelf",
        user_id=1,
        is_public=True,
    )

    assert result is True


def test_shelf_repository_check_name_unique_public_not_unique() -> None:
    """Test check_name_unique returns False for non-unique public shelf name (covers lines 247-251, 256-257)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    existing_shelf = Shelf(
        id=1,
        name="Existing Shelf",
        is_public=True,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([existing_shelf])
    result = repo.check_name_unique(
        library_id=1,
        name="Existing Shelf",
        user_id=1,
        is_public=True,
    )

    assert result is False


def test_shelf_repository_check_name_unique_private_unique() -> None:
    """Test check_name_unique returns True for unique private shelf name (covers lines 247-253, 256-257)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])  # No existing shelf
    result = repo.check_name_unique(
        library_id=1,
        name="New Shelf",
        user_id=1,
        is_public=False,
    )

    assert result is True


def test_shelf_repository_check_name_unique_private_not_unique() -> None:
    """Test check_name_unique returns False for non-unique private shelf name (covers lines 247-253, 256-257)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    existing_shelf = Shelf(
        id=1,
        name="Existing Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    session.add_exec_result([existing_shelf])
    result = repo.check_name_unique(
        library_id=1,
        name="Existing Shelf",
        user_id=1,
        is_public=False,
    )

    assert result is False


def test_shelf_repository_check_name_unique_with_exclude_id() -> None:
    """Test check_name_unique with exclude_id (covers lines 254-257)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

    existing_shelf = Shelf(
        id=1,
        name="Existing Shelf",
        is_public=False,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )

    # When exclude_id matches, should return True (unique)
    session.add_exec_result([])  # No other shelf with same name
    result = repo.check_name_unique(
        library_id=1,
        name="Existing Shelf",
        user_id=1,
        is_public=False,
        exclude_id=1,
    )

    assert result is True

    # When exclude_id doesn't match, should return False (not unique)
    session.add_exec_result([existing_shelf])
    result = repo.check_name_unique(
        library_id=1,
        name="Existing Shelf",
        user_id=1,
        is_public=False,
        exclude_id=2,  # Different ID
    )

    assert result is False


def test_shelf_repository_delete() -> None:
    """Test ShelfRepository.delete deletes shelf (covers line 267)."""
    session = DummySession()
    repo = ShelfRepository(session)  # type: ignore[arg-type]

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

    repo.delete(shelf)
    assert shelf in session.deleted


def test_book_shelf_link_repository_init() -> None:
    """Test BookShelfLinkRepository initialization (covers line 284)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]
    assert repo._session is session


def test_book_shelf_link_repository_add() -> None:
    """Test BookShelfLinkRepository.add adds link to session (covers lines 299-300)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link = BookShelfLink(
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )

    result = repo.add(link)
    assert result is link
    assert link in session.added


def test_book_shelf_link_repository_get() -> None:
    """Test BookShelfLinkRepository.get retrieves link by ID (covers line 315)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )
    session.add(link)

    result = repo.get(1)
    assert result is link

    result = repo.get(999)
    assert result is None


def test_book_shelf_link_repository_find_by_shelf() -> None:
    """Test find_by_shelf returns all links for a shelf (covers lines 330-335)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link1 = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )
    link2 = BookShelfLink(
        id=2,
        shelf_id=1,
        book_id=101,
        library_id=1,
        order=1,
        date_added=datetime.now(UTC),
    )

    session.add_exec_result([link1, link2])
    result = repo.find_by_shelf(shelf_id=1)

    assert len(result) == 2
    assert link1 in result
    assert link2 in result


def test_book_shelf_link_repository_find_by_book() -> None:
    """Test find_by_book returns all links for a book (covers lines 350-351)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link1 = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )
    link2 = BookShelfLink(
        id=2,
        shelf_id=2,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )

    session.add_exec_result([link1, link2])
    result = repo.find_by_book(book_id=100, library_id=1)

    assert len(result) == 2
    assert link1 in result
    assert link2 in result


def test_book_shelf_link_repository_find_by_book_filters_by_library() -> None:
    """Test find_by_book filters by library_id."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link_lib1 = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )

    # Only return link for library 1
    session.add_exec_result([link_lib1])
    result = repo.find_by_book(book_id=100, library_id=1)
    assert len(result) == 1
    assert result[0] is link_lib1

    # No links for library 2
    session.add_exec_result([])
    result = repo.find_by_book(book_id=100, library_id=2)
    assert len(result) == 0


def test_book_shelf_link_repository_find_by_shelf_and_book() -> None:
    """Test find_by_shelf_and_book returns specific link (covers lines 372-376)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )

    session.add_exec_result([link])
    result = repo.find_by_shelf_and_book(shelf_id=1, book_id=100)

    assert result is link

    session.add_exec_result([])
    result = repo.find_by_shelf_and_book(shelf_id=1, book_id=999)
    assert result is None


def test_book_shelf_link_repository_find_by_shelf_and_book_with_library_id() -> None:
    """Test find_by_shelf_and_book with explicit library_id."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )

    session.add_exec_result([link])
    result = repo.find_by_shelf_and_book(shelf_id=1, book_id=100, library_id=1)
    assert result is link

    session.add_exec_result([])
    result = repo.find_by_shelf_and_book(shelf_id=1, book_id=100, library_id=2)
    assert result is None


def test_book_shelf_link_repository_get_max_order_with_result() -> None:
    """Test get_max_order returns max order when books exist (covers lines 391-397)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([5])  # Max order is 5
    result = repo.get_max_order(shelf_id=1)

    assert result == 5


def test_book_shelf_link_repository_get_max_order_no_result() -> None:
    """Test get_max_order returns 0 when no books exist (covers lines 391-397)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([None])  # No books in shelf
    result = repo.get_max_order(shelf_id=1)

    assert result == 0


def test_book_shelf_link_repository_reorder_books() -> None:
    """Test reorder_books updates order for multiple books (covers lines 413-417)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link1 = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )
    link2 = BookShelfLink(
        id=2,
        shelf_id=1,
        book_id=101,
        library_id=1,
        order=1,
        date_added=datetime.now(UTC),
    )

    book_orders: list[tuple[int, int, int]] = [(100, 1, 2), (101, 1, 0)]

    # Mock find_by_shelf_and_book to return links
    def mock_find(
        shelf_id: int,
        book_id: int,
        library_id: int | None = None,
    ) -> BookShelfLink | None:
        if shelf_id == 1 and book_id == 100 and library_id == 1:
            return link1
        if shelf_id == 1 and book_id == 101 and library_id == 1:
            return link2
        return None

    with patch.object(repo, "find_by_shelf_and_book", side_effect=mock_find):
        repo.reorder_books(shelf_id=1, book_orders=book_orders)

        assert link1.order == 2
        assert link2.order == 0
        assert link1 in session.added
        assert link2 in session.added


def test_book_shelf_link_repository_reorder_books_missing_link() -> None:
    """Test reorder_books handles missing links gracefully (covers lines 413-417)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    # book_id 999 in library 1 doesn't exist
    book_orders: list[tuple[int, int, int]] = [(100, 1, 2), (999, 1, 0)]

    # Mock find_by_shelf_and_book to return None for missing book
    def mock_find(
        shelf_id: int,
        book_id: int,
        library_id: int | None = None,
    ) -> BookShelfLink | None:
        if shelf_id == 1 and book_id == 100 and library_id == 1:
            return BookShelfLink(
                id=1,
                shelf_id=1,
                book_id=100,
                library_id=1,
                order=0,
                date_added=datetime.now(UTC),
            )
        return None

    with patch.object(repo, "find_by_shelf_and_book", side_effect=mock_find):
        repo.reorder_books(shelf_id=1, book_orders=book_orders)

        # Should not raise, just skip missing links


def test_book_shelf_link_repository_delete() -> None:
    """Test BookShelfLinkRepository.delete deletes link (covers line 427)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )

    repo.delete(link)
    assert link in session.deleted


def test_book_shelf_link_repository_delete_by_shelf() -> None:
    """Test delete_by_shelf deletes all links for a shelf (covers lines 437-439)."""
    session = DummySession()
    repo = BookShelfLinkRepository(session)  # type: ignore[arg-type]

    link1 = BookShelfLink(
        id=1,
        shelf_id=1,
        book_id=100,
        library_id=1,
        order=0,
        date_added=datetime.now(UTC),
    )
    link2 = BookShelfLink(
        id=2,
        shelf_id=1,
        book_id=101,
        library_id=1,
        order=1,
        date_added=datetime.now(UTC),
    )

    # Mock find_by_shelf to return links
    session.add_exec_result([link1, link2])
    repo.delete_by_shelf(shelf_id=1)

    assert link1 in session.deleted
    assert link2 in session.deleted
