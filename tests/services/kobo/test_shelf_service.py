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

"""Tests for KoboShelfService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock

import pytest

from bookcard.models.core import Book
from bookcard.models.shelves import BookShelfLink, Shelf
from bookcard.services.kobo.shelf_service import (
    KoboShelfService,
    convert_to_kobo_timestamp_string,
)
from bookcard.services.kobo.sync_token_service import SyncToken

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_shelf_service() -> MagicMock:
    """Create a mock ShelfService.

    Returns
    -------
    MagicMock
        Mock shelf service instance.
    """
    service = MagicMock()
    service.list_user_shelves = MagicMock(return_value=[])
    service.create_shelf = MagicMock()
    return service


@pytest.fixture
def mock_reading_state_repo() -> MagicMock:
    """Create a mock KoboReadingStateRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    return MagicMock()


@pytest.fixture
def shelf_service(
    session: DummySession,
    mock_shelf_service: MagicMock,
    mock_reading_state_repo: MagicMock,
) -> KoboShelfService:
    """Create KoboShelfService instance for testing.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.

    Returns
    -------
    KoboShelfService
        Service instance.
    """
    return KoboShelfService(
        session,  # type: ignore[arg-type]
        mock_shelf_service,
        mock_reading_state_repo,
    )


@pytest.fixture
def shelf() -> Shelf:
    """Create a test shelf.

    Returns
    -------
    Shelf
        Shelf instance.
    """
    shelf = Shelf(
        id=1,
        uuid="shelf-uuid-123",
        name="Test Shelf",
        library_id=1,
        user_id=1,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        last_modified=datetime(2025, 1, 15, tzinfo=UTC),
        book_links=[],
    )
    # Add 'created' attribute for testing (code uses getattr(shelf, "created", None))
    # Use object.__setattr__ to bypass Pydantic validation
    object.__setattr__(shelf, "created", datetime(2025, 1, 1, tzinfo=UTC))
    return shelf


@pytest.fixture
def sync_token() -> SyncToken:
    """Create a test sync token.

    Returns
    -------
    SyncToken
        Sync token instance.
    """
    return SyncToken(
        tags_last_modified=datetime(2025, 1, 10, tzinfo=UTC),
    )


# ============================================================================
# Tests for convert_to_kobo_timestamp_string
# ============================================================================


def test_convert_to_kobo_timestamp_string() -> None:
    """Test converting datetime to Kobo timestamp string."""
    dt = datetime(2025, 1, 15, 12, 30, 45, tzinfo=UTC)
    result = convert_to_kobo_timestamp_string(dt)
    assert result == "2025-01-15T12:30:45Z"


def test_convert_to_kobo_timestamp_string_no_tzinfo() -> None:
    """Test converting datetime without tzinfo to Kobo timestamp string."""
    dt = datetime(2025, 1, 15, 12, 30, 45)  # noqa: DTZ001
    result = convert_to_kobo_timestamp_string(dt)
    assert result.endswith("Z")


# ============================================================================
# Tests for KoboShelfService.__init__
# ============================================================================


def test_init(
    session: DummySession,
    mock_shelf_service: MagicMock,
    mock_reading_state_repo: MagicMock,
) -> None:
    """Test KoboShelfService initialization.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    """
    service = KoboShelfService(
        session,  # type: ignore[arg-type]
        mock_shelf_service,
        mock_reading_state_repo,
    )
    assert service._session == session
    assert service._shelf_service == mock_shelf_service
    assert service._reading_state_repo == mock_reading_state_repo


# ============================================================================
# Tests for KoboShelfService.sync_shelves
# ============================================================================


def test_sync_shelves_new(
    shelf_service: KoboShelfService,
    mock_shelf_service: MagicMock,
    shelf: Shelf,
    sync_token: SyncToken,
) -> None:
    """Test syncing new shelves.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    shelf : Shelf
        Test shelf.
    sync_token : SyncToken
        Sync token.
    """
    object.__setattr__(shelf, "created", datetime(2025, 1, 12, tzinfo=UTC))
    mock_shelf_service.list_user_shelves.return_value = [shelf]

    result = shelf_service.sync_shelves(
        user_id=1, library_id=1, sync_token=sync_token, book_service=None
    )

    assert len(result) == 1
    assert "NewTag" in result[0]
    assert sync_token.tags_last_modified == shelf.last_modified


def test_sync_shelves_changed(
    shelf_service: KoboShelfService,
    mock_shelf_service: MagicMock,
    shelf: Shelf,
    sync_token: SyncToken,
) -> None:
    """Test syncing changed shelves.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    shelf : Shelf
        Test shelf.
    sync_token : SyncToken
        Sync token.
    """
    object.__setattr__(shelf, "created", datetime(2025, 1, 5, tzinfo=UTC))
    mock_shelf_service.list_user_shelves.return_value = [shelf]

    result = shelf_service.sync_shelves(
        user_id=1, library_id=1, sync_token=sync_token, book_service=None
    )

    assert len(result) == 1
    assert "ChangedTag" in result[0]


def test_sync_shelves_not_modified(
    shelf_service: KoboShelfService,
    mock_shelf_service: MagicMock,
    shelf: Shelf,
    sync_token: SyncToken,
) -> None:
    """Test syncing shelves that haven't been modified.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    shelf : Shelf
        Test shelf.
    sync_token : SyncToken
        Sync token.
    """
    shelf.last_modified = datetime(2025, 1, 5, tzinfo=UTC)
    mock_shelf_service.list_user_shelves.return_value = [shelf]

    result = shelf_service.sync_shelves(
        user_id=1, library_id=1, sync_token=sync_token, book_service=None
    )

    assert len(result) == 0


def test_sync_shelves_no_created(
    shelf_service: KoboShelfService,
    mock_shelf_service: MagicMock,
    shelf: Shelf,
    sync_token: SyncToken,
) -> None:
    """Test syncing shelves without created attribute.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    shelf : Shelf
        Test shelf.
    sync_token : SyncToken
        Sync token.
    """
    # Create a new shelf without the 'created' attribute
    shelf = Shelf(
        id=1,
        uuid="shelf-uuid-123",
        name="Test Shelf",
        library_id=1,
        user_id=1,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        last_modified=datetime(2025, 1, 15, tzinfo=UTC),
        book_links=[],
    )
    mock_shelf_service.list_user_shelves.return_value = [shelf]

    result = shelf_service.sync_shelves(
        user_id=1, library_id=1, sync_token=sync_token, book_service=None
    )

    assert len(result) == 0


# ============================================================================
# Tests for KoboShelfService._create_kobo_tag
# ============================================================================


def test_create_kobo_tag(
    shelf_service: KoboShelfService,
    shelf: Shelf,
) -> None:
    """Test creating Kobo tag from shelf.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    shelf : Shelf
        Test shelf.
    """
    result = shelf_service._create_kobo_tag(shelf, book_service=None)

    assert result is not None
    assert "Tag" in result
    tag = result["Tag"]
    assert isinstance(tag, dict)
    assert tag["Name"] == "Test Shelf"  # type: ignore[index]
    assert tag["Id"] == "shelf-uuid-123"  # type: ignore[index]


def test_create_kobo_tag_with_book_links(
    shelf_service: KoboShelfService,
    shelf: Shelf,
) -> None:
    """Test creating Kobo tag with book links.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    shelf : Shelf
        Test shelf.
    """
    book_link = BookShelfLink(id=1, shelf_id=1, book_id=1)
    shelf.book_links = [book_link]

    result = shelf_service._create_kobo_tag(shelf, book_service=None)

    assert result is not None
    tag = result["Tag"]
    assert isinstance(tag, dict)
    items = tag["Items"]  # type: ignore[index]
    assert isinstance(items, list)
    assert len(items) == 1
    assert isinstance(items[0], dict)
    assert items[0]["RevisionId"] == "1"  # type: ignore[index]


def test_create_kobo_tag_with_book_service(
    shelf_service: KoboShelfService,
    shelf: Shelf,
) -> None:
    """Test creating Kobo tag with book service.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    shelf : Shelf
        Test shelf.
    """
    book_link = BookShelfLink(id=1, shelf_id=1, book_id=1)
    shelf.book_links = [book_link]

    mock_book_service = MagicMock()
    mock_book_repo = MagicMock()
    mock_session = Mock()
    mock_result = Mock()
    book = Book(id=1, title="Test Book", uuid="book-uuid-123")
    mock_result.first = Mock(return_value=book)
    mock_session.exec = Mock(return_value=mock_result)
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    mock_book_repo.get_session = Mock(return_value=mock_session)
    mock_book_service._book_repo = mock_book_repo

    result = shelf_service._create_kobo_tag(shelf, book_service=mock_book_service)

    assert result is not None
    tag = result["Tag"]
    assert isinstance(tag, dict)
    items = tag["Items"]  # type: ignore[index]
    assert isinstance(items, list)
    assert len(items) > 0
    assert isinstance(items[0], dict)
    assert items[0]["RevisionId"] == "book-uuid-123"  # type: ignore[index]


def test_create_kobo_tag_book_link_no_id(
    shelf_service: KoboShelfService,
    shelf: Shelf,
) -> None:
    """Test creating Kobo tag with book link without ID.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    shelf : Shelf
        Test shelf.
    """
    book_link = BookShelfLink(id=1, shelf_id=1, book_id=None)
    shelf.book_links = [book_link]

    result = shelf_service._create_kobo_tag(shelf, book_service=None)

    assert result is not None
    tag = result["Tag"]
    assert isinstance(tag, dict)
    items = tag["Items"]  # type: ignore[index]
    assert isinstance(items, list)
    assert len(items) == 0


# ============================================================================
# Tests for KoboShelfService.create_shelf_from_kobo
# ============================================================================


def test_create_shelf_from_kobo(
    shelf_service: KoboShelfService,
    mock_shelf_service: MagicMock,
) -> None:
    """Test creating shelf from Kobo tag data.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    """
    tag_data = {"Name": "New Shelf", "Items": []}
    mock_shelf = Shelf(
        id=1,
        uuid="new-shelf-uuid",
        name="New Shelf",
        library_id=1,
        user_id=1,
    )
    mock_shelf_service.create_shelf.return_value = mock_shelf

    result = shelf_service.create_shelf_from_kobo(
        user_id=1, library_id=1, tag_data=tag_data
    )

    assert result == mock_shelf
    mock_shelf_service.create_shelf.assert_called_once_with(
        library_id=1,
        user_id=1,
        name="New Shelf",
        description=None,
        is_public=False,
    )


def test_create_shelf_from_kobo_no_name(
    shelf_service: KoboShelfService,
) -> None:
    """Test creating shelf from Kobo tag data without name.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    """
    tag_data = {"Items": []}

    with pytest.raises(ValueError, match="Tag name is required"):
        shelf_service.create_shelf_from_kobo(user_id=1, library_id=1, tag_data=tag_data)


def test_create_shelf_from_kobo_non_string_name(
    shelf_service: KoboShelfService,
    mock_shelf_service: MagicMock,
) -> None:
    """Test creating shelf from Kobo tag data with non-string name.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    """
    tag_data = {"Name": 123, "Items": []}
    mock_shelf = Shelf(
        id=1,
        uuid="new-shelf-uuid",
        name="123",
        library_id=1,
        user_id=1,
    )
    mock_shelf_service.create_shelf.return_value = mock_shelf

    result = shelf_service.create_shelf_from_kobo(
        user_id=1, library_id=1, tag_data=tag_data
    )

    assert result == mock_shelf


# ============================================================================
# Tests for KoboShelfService.update_shelf_from_kobo
# ============================================================================


def test_update_shelf_from_kobo(
    shelf_service: KoboShelfService,
    shelf: Shelf,
    session: DummySession,
) -> None:
    """Test updating shelf from Kobo tag data.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    shelf : Shelf
        Test shelf.
    session : DummySession
        Dummy session instance.
    """
    tag_data = {"Name": "Updated Shelf Name", "Items": []}

    shelf_service.update_shelf_from_kobo(shelf, tag_data)

    assert shelf.name == "Updated Shelf Name"
    assert session.flush_count > 0


def test_update_shelf_from_kobo_no_name(
    shelf_service: KoboShelfService,
    shelf: Shelf,
    session: DummySession,
) -> None:
    """Test updating shelf from Kobo tag data without name.

    Parameters
    ----------
    shelf_service : KoboShelfService
        Service instance.
    shelf : Shelf
        Test shelf.
    session : DummySession
        Dummy session instance.
    """
    original_name = shelf.name
    tag_data = {"Items": []}

    shelf_service.update_shelf_from_kobo(shelf, tag_data)

    assert shelf.name == original_name
    assert session.flush_count > 0
