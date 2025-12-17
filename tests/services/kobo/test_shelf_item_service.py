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

"""Tests for KoboShelfItemService to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.api.schemas.kobo import KoboTagItemRequest
from bookcard.services.kobo.book_lookup_service import KoboBookLookupService
from bookcard.services.kobo.shelf_item_service import KoboShelfItemService

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_book_lookup_service() -> MagicMock:
    """Create a mock KoboBookLookupService.

    Returns
    -------
    MagicMock
        Mock book lookup service instance.
    """
    service = MagicMock(spec=KoboBookLookupService)
    service.find_book_by_uuid = MagicMock(return_value=None)
    return service


@pytest.fixture
def shelf_item_service(
    session: DummySession,
    mock_book_lookup_service: MagicMock,
) -> KoboShelfItemService:
    """Create KoboShelfItemService instance for testing.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.

    Returns
    -------
    KoboShelfItemService
        Service instance.
    """
    return KoboShelfItemService(
        session,  # type: ignore[arg-type]
        mock_book_lookup_service,
    )


@pytest.fixture
def tag_item_request() -> KoboTagItemRequest:
    """Create a test tag item request.

    Returns
    -------
    KoboTagItemRequest
        Tag item request instance.
    """
    return KoboTagItemRequest(
        Items=[
            {
                "Type": "ProductRevisionTagItem",
                "RevisionId": "test-uuid-123",
            }
        ]
    )


# ============================================================================
# Tests for KoboShelfItemService.__init__
# ============================================================================


def test_init(session: DummySession, mock_book_lookup_service: MagicMock) -> None:
    """Test KoboShelfItemService initialization.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    """
    service = KoboShelfItemService(
        session,  # type: ignore[arg-type]
        mock_book_lookup_service,
    )
    assert service._session == session
    assert service._book_lookup_service == mock_book_lookup_service


# ============================================================================
# Tests for KoboShelfItemService.add_items_to_shelf
# ============================================================================


def test_add_items_to_shelf_success(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
    tag_item_request: KoboTagItemRequest,
) -> None:
    """Test adding items to shelf successfully.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    tag_item_request : KoboTagItemRequest
        Tag item request.
    """
    from bookcard.models.core import Book

    book = Book(id=1, title="Test Book", uuid="test-uuid-123")
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)

    # Mock ShelfService to avoid actual database operations
    with patch(
        "bookcard.services.kobo.shelf_item_service.ShelfService"
    ) as mock_shelf_service_class:
        mock_shelf_service = MagicMock()
        mock_shelf_service.add_book_to_shelf = MagicMock()
        mock_shelf_service_class.return_value = mock_shelf_service

        shelf_item_service.add_items_to_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )

        mock_book_lookup_service.find_book_by_uuid.assert_called_once_with(
            "test-uuid-123"
        )
        mock_shelf_service.add_book_to_shelf.assert_called_once_with(
            shelf_id=1, book_id=1, user_id=1
        )


def test_add_items_to_shelf_wrong_type(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
) -> None:
    """Test adding items to shelf with wrong item type.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    """
    tag_item_request = KoboTagItemRequest(
        Items=[{"Type": "WrongType", "RevisionId": "test-uuid-123"}]
    )

    with patch(
        "bookcard.services.kobo.shelf_item_service.ShelfService"
    ) as mock_shelf_service_class:
        mock_shelf_service = MagicMock()
        mock_shelf_service_class.return_value = mock_shelf_service
        shelf_item_service.add_items_to_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )

    mock_book_lookup_service.find_book_by_uuid.assert_not_called()


def test_add_items_to_shelf_no_revision_id(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
) -> None:
    """Test adding items to shelf with no revision ID.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    """
    tag_item_request = KoboTagItemRequest(Items=[{"Type": "ProductRevisionTagItem"}])

    with patch(
        "bookcard.services.kobo.shelf_item_service.ShelfService"
    ) as mock_shelf_service_class:
        mock_shelf_service = MagicMock()
        mock_shelf_service_class.return_value = mock_shelf_service
        shelf_item_service.add_items_to_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )

    mock_book_lookup_service.find_book_by_uuid.assert_not_called()


def test_add_items_to_shelf_book_not_found(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
    tag_item_request: KoboTagItemRequest,
) -> None:
    """Test adding items to shelf when book is not found.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    tag_item_request : KoboTagItemRequest
        Tag item request.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = None

    with patch(
        "bookcard.services.kobo.shelf_item_service.ShelfService"
    ) as mock_shelf_service_class:
        mock_shelf_service = MagicMock()
        mock_shelf_service_class.return_value = mock_shelf_service

        shelf_item_service.add_items_to_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )

        mock_shelf_service.add_book_to_shelf.assert_not_called()


def test_add_items_to_shelf_already_in_shelf(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
    tag_item_request: KoboTagItemRequest,
) -> None:
    """Test adding items to shelf when book is already in shelf.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    tag_item_request : KoboTagItemRequest
        Tag item request.
    """
    from bookcard.models.core import Book

    book = Book(id=1, title="Test Book", uuid="test-uuid-123")
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)

    with patch(
        "bookcard.services.kobo.shelf_item_service.ShelfService"
    ) as mock_shelf_service_class:
        mock_shelf_service = MagicMock()
        mock_shelf_service.add_book_to_shelf = MagicMock(
            side_effect=ValueError("Already in shelf")
        )
        mock_shelf_service_class.return_value = mock_shelf_service

        # Should not raise, just suppress the error
        shelf_item_service.add_items_to_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )


# ============================================================================
# Tests for KoboShelfItemService.remove_items_from_shelf
# ============================================================================


def test_remove_items_from_shelf_success(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
    tag_item_request: KoboTagItemRequest,
) -> None:
    """Test removing items from shelf successfully.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    tag_item_request : KoboTagItemRequest
        Tag item request.
    """
    from bookcard.models.core import Book

    book = Book(id=1, title="Test Book", uuid="test-uuid-123")
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)

    with patch(
        "bookcard.services.kobo.shelf_item_service.ShelfService"
    ) as mock_shelf_service_class:
        mock_shelf_service = MagicMock()
        mock_shelf_service.remove_book_from_shelf = MagicMock()
        mock_shelf_service_class.return_value = mock_shelf_service

        shelf_item_service.remove_items_from_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )

        mock_book_lookup_service.find_book_by_uuid.assert_called_once_with(
            "test-uuid-123"
        )
        mock_shelf_service.remove_book_from_shelf.assert_called_once_with(
            shelf_id=1, book_id=1, user_id=1
        )


def test_remove_items_from_shelf_wrong_type(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
) -> None:
    """Test removing items from shelf with wrong item type.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    """
    tag_item_request = KoboTagItemRequest(
        Items=[{"Type": "WrongType", "RevisionId": "test-uuid-123"}]
    )

    with (
        patch("bookcard.services.kobo.shelf_item_service.ShelfRepository"),
        patch("bookcard.services.kobo.shelf_item_service.BookShelfLinkRepository"),
        patch("bookcard.services.kobo.shelf_item_service.ShelfService"),
    ):
        shelf_item_service.remove_items_from_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )

    mock_book_lookup_service.find_book_by_uuid.assert_not_called()


def test_remove_items_from_shelf_no_revision_id(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
) -> None:
    """Test removing items from shelf with no revision ID.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    """
    tag_item_request = KoboTagItemRequest(Items=[{"Type": "ProductRevisionTagItem"}])

    with (
        patch("bookcard.services.kobo.shelf_item_service.ShelfRepository"),
        patch("bookcard.services.kobo.shelf_item_service.BookShelfLinkRepository"),
        patch("bookcard.services.kobo.shelf_item_service.ShelfService"),
    ):
        shelf_item_service.remove_items_from_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )

    mock_book_lookup_service.find_book_by_uuid.assert_not_called()


def test_remove_items_from_shelf_book_not_found(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
    tag_item_request: KoboTagItemRequest,
) -> None:
    """Test removing items from shelf when book is not found.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    tag_item_request : KoboTagItemRequest
        Tag item request.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = None

    with patch(
        "bookcard.services.kobo.shelf_item_service.ShelfService"
    ) as mock_shelf_service_class:
        mock_shelf_service = MagicMock()
        mock_shelf_service_class.return_value = mock_shelf_service

        shelf_item_service.remove_items_from_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )

        mock_shelf_service.remove_book_from_shelf.assert_not_called()


def test_remove_items_from_shelf_not_in_shelf(
    shelf_item_service: KoboShelfItemService,
    mock_book_lookup_service: MagicMock,
    tag_item_request: KoboTagItemRequest,
) -> None:
    """Test removing items from shelf when book is not in shelf.

    Parameters
    ----------
    shelf_item_service : KoboShelfItemService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    tag_item_request : KoboTagItemRequest
        Tag item request.
    """
    from bookcard.models.core import Book

    book = Book(id=1, title="Test Book", uuid="test-uuid-123")
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)

    with patch(
        "bookcard.services.kobo.shelf_item_service.ShelfService"
    ) as mock_shelf_service_class:
        mock_shelf_service = MagicMock()
        mock_shelf_service.remove_book_from_shelf = MagicMock(
            side_effect=ValueError("Not in shelf")
        )
        mock_shelf_service_class.return_value = mock_shelf_service

        # Should not raise, just suppress the error
        shelf_item_service.remove_items_from_shelf(
            shelf_id=1, user_id=1, item_data=tag_item_request
        )
