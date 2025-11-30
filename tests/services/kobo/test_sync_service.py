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

"""Tests for KoboSyncService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from fundamental.models.core import Book
from fundamental.models.kobo import (
    KoboArchivedBook,
    KoboReadingState,
    KoboSyncedBook,
)
from fundamental.models.reading import ReadStatus, ReadStatusEnum
from fundamental.repositories.models import BookWithFullRelations, BookWithRelations
from fundamental.services.kobo.metadata_service import KoboMetadataService
from fundamental.services.kobo.sync_service import KoboSyncService
from fundamental.services.kobo.sync_token_service import SyncToken
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session for testing.

    Returns
    -------
    DummySession
        Dummy session instance.
    """
    return DummySession()


@pytest.fixture
def mock_book_service() -> MagicMock:
    """Create a mock BookService.

    Returns
    -------
    MagicMock
        Mock book service instance.
    """
    service = MagicMock()
    service.list_books = MagicMock(return_value=([], 0))
    service.get_book = MagicMock(return_value=None)
    return service


@pytest.fixture
def mock_metadata_service() -> MagicMock:
    """Create a mock KoboMetadataService.

    Returns
    -------
    MagicMock
        Mock metadata service instance.
    """
    return MagicMock(spec=KoboMetadataService)


@pytest.fixture
def mock_reading_state_repo() -> MagicMock:
    """Create a mock KoboReadingStateRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    repo = MagicMock()
    repo.find_by_user_and_book = MagicMock(return_value=None)
    repo.find_by_user = MagicMock(return_value=[])
    return repo


@pytest.fixture
def mock_synced_book_repo() -> MagicMock:
    """Create a mock KoboSyncedBookRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    repo = MagicMock()
    repo.find_book_ids_by_user = MagicMock(return_value=set())
    repo.find_by_user_and_book = MagicMock(return_value=None)
    repo.add = MagicMock()
    return repo


@pytest.fixture
def mock_archived_book_repo() -> MagicMock:
    """Create a mock KoboArchivedBookRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    repo = MagicMock()
    repo.find_by_user_and_book = MagicMock(return_value=None)
    return repo


@pytest.fixture
def mock_read_status_repo() -> MagicMock:
    """Create a mock ReadStatusRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    repo = MagicMock()
    repo.find_by_user_library_book = MagicMock(return_value=None)
    return repo


@pytest.fixture
def mock_shelf_service() -> MagicMock:
    """Create a mock ShelfService.

    Returns
    -------
    MagicMock
        Mock shelf service instance.
    """
    return MagicMock()


@pytest.fixture
def sync_service(
    session: DummySession,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    mock_reading_state_repo: MagicMock,
    mock_synced_book_repo: MagicMock,
    mock_archived_book_repo: MagicMock,
    mock_read_status_repo: MagicMock,
    mock_shelf_service: MagicMock | None,
) -> KoboSyncService:
    """Create KoboSyncService instance for testing.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    mock_synced_book_repo : MagicMock
        Mock synced book repository.
    mock_archived_book_repo : MagicMock
        Mock archived book repository.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    mock_shelf_service : MagicMock | None
        Mock shelf service.

    Returns
    -------
    KoboSyncService
        Service instance.
    """
    return KoboSyncService(
        session,  # type: ignore[arg-type]
        mock_book_service,
        mock_metadata_service,
        mock_reading_state_repo,
        mock_synced_book_repo,
        mock_archived_book_repo,
        mock_read_status_repo,
        mock_shelf_service,
    )


@pytest.fixture
def book() -> Book:
    """Create a test book.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(
        id=1,
        title="Test Book",
        uuid="test-uuid-123",
        timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        last_modified=datetime(2025, 1, 15, tzinfo=UTC),
    )


@pytest.fixture
def book_with_rels(book: Book) -> BookWithFullRelations:
    """Create a test book with relations.

    Parameters
    ----------
    book : Book
        Test book.

    Returns
    -------
    BookWithFullRelations
        Book with relations instance.
    """
    return BookWithFullRelations(
        book=book,
        authors=["Author One"],
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
        formats=[{"format": "EPUB", "name": "test.epub", "size": 1000}],
    )


@pytest.fixture
def sync_token() -> SyncToken:
    """Create a test sync token.

    Returns
    -------
    SyncToken
        Sync token instance.
    """
    return SyncToken(
        books_last_modified=datetime(2025, 1, 10, tzinfo=UTC),
        books_last_created=datetime(2025, 1, 5, tzinfo=UTC),
        reading_state_last_modified=datetime(2025, 1, 10, tzinfo=UTC),
    )


# ============================================================================
# Tests for KoboSyncService.__init__
# ============================================================================


def test_init(
    session: DummySession,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    mock_reading_state_repo: MagicMock,
    mock_synced_book_repo: MagicMock,
    mock_archived_book_repo: MagicMock,
    mock_read_status_repo: MagicMock,
) -> None:
    """Test KoboSyncService initialization.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    mock_synced_book_repo : MagicMock
        Mock synced book repository.
    mock_archived_book_repo : MagicMock
        Mock archived book repository.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    """
    service = KoboSyncService(
        session,  # type: ignore[arg-type]
        mock_book_service,
        mock_metadata_service,
        mock_reading_state_repo,
        mock_synced_book_repo,
        mock_archived_book_repo,
        mock_read_status_repo,
        None,
    )
    assert service._session == session
    assert service._book_service == mock_book_service
    assert service._metadata_service == mock_metadata_service
    assert service._shelf_service is None


# ============================================================================
# Tests for KoboSyncService.sync_library
# ============================================================================


def test_sync_library_new_book(
    sync_service: KoboSyncService,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    mock_synced_book_repo: MagicMock,
    mock_archived_book_repo: MagicMock,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test syncing library with new book.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    mock_synced_book_repo : MagicMock
        Mock synced book repository.
    mock_archived_book_repo : MagicMock
        Mock archived book repository.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    # Set book timestamp after last_created to make it "new"
    book_with_rels.book.timestamp = datetime(2025, 1, 12, tzinfo=UTC)
    mock_book_service.list_books.return_value = ([book_with_rels], 1)
    mock_metadata_service.create_book_entitlement.return_value = {"Id": "test-uuid-123"}
    mock_metadata_service.get_book_metadata.return_value = {"Title": "Test Book"}

    results, continue_sync = sync_service.sync_library(
        user_id=1, library_id=1, sync_token=sync_token, only_shelves=False
    )

    assert len(results) == 1
    assert "NewEntitlement" in results[0]
    assert continue_sync is False
    mock_synced_book_repo.find_by_user_and_book.assert_called()


def test_sync_library_changed_book(
    sync_service: KoboSyncService,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test syncing library with changed book.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    # Set book timestamp to before last_created
    book_with_rels.book.timestamp = datetime(2025, 1, 1, tzinfo=UTC)
    mock_book_service.list_books.return_value = ([book_with_rels], 1)
    mock_metadata_service.create_book_entitlement.return_value = {"Id": "test-uuid-123"}
    mock_metadata_service.get_book_metadata.return_value = {"Title": "Test Book"}

    results, _continue_sync = sync_service.sync_library(
        user_id=1, library_id=1, sync_token=sync_token, only_shelves=False
    )

    assert len(results) == 1
    assert "ChangedEntitlement" in results[0]


def test_sync_library_with_archived_book(
    sync_service: KoboSyncService,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    mock_archived_book_repo: MagicMock,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test syncing library with archived book.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    mock_archived_book_repo : MagicMock
        Mock archived book repository.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    archived_book = KoboArchivedBook(id=1, user_id=1, book_id=1, is_archived=True)
    mock_archived_book_repo.find_by_user_and_book.return_value = archived_book
    # Set book timestamp after last_created to make it "new"
    book_with_rels.book.timestamp = datetime(2025, 1, 12, tzinfo=UTC)
    mock_book_service.list_books.return_value = ([book_with_rels], 1)
    mock_metadata_service.create_book_entitlement.return_value = {"Id": "test-uuid-123"}
    mock_metadata_service.get_book_metadata.return_value = {"Title": "Test Book"}

    results, _ = sync_service.sync_library(
        user_id=1, library_id=1, sync_token=sync_token, only_shelves=False
    )

    assert len(results) == 1
    # Check that create_book_entitlement was called with archived=True
    calls = mock_metadata_service.create_book_entitlement.call_args_list
    assert len(calls) > 0
    assert calls[0][0][0] == book_with_rels.book
    assert calls[0][1].get("archived") is True or calls[0][0][1] is True


def test_sync_library_with_reading_state(
    sync_service: KoboSyncService,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    mock_reading_state_repo: MagicMock,
    mock_read_status_repo: MagicMock,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test syncing library with reading state.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    reading_state = KoboReadingState(
        id=1,
        user_id=1,
        book_id=1,
        last_modified=datetime(2025, 1, 15, tzinfo=UTC),
    )
    mock_reading_state_repo.find_by_user_and_book.return_value = reading_state
    read_status = ReadStatus(
        id=1, user_id=1, library_id=1, book_id=1, status=ReadStatusEnum.READING
    )
    mock_read_status_repo.find_by_user_library_book.return_value = read_status
    # Set book timestamp after last_created to make it "new"
    book_with_rels.book.timestamp = datetime(2025, 1, 12, tzinfo=UTC)
    mock_book_service.list_books.return_value = ([book_with_rels], 1)
    mock_metadata_service.create_book_entitlement.return_value = {"Id": "test-uuid-123"}
    mock_metadata_service.get_book_metadata.return_value = {"Title": "Test Book"}
    mock_metadata_service.get_reading_state_response.return_value = {
        "EntitlementId": "test-uuid-123"
    }

    results, _ = sync_service.sync_library(
        user_id=1, library_id=1, sync_token=sync_token, only_shelves=False
    )

    assert len(results) == 1
    new_entitlement = results[0].get("NewEntitlement", {})
    assert isinstance(new_entitlement, dict)
    assert "ReadingState" in new_entitlement


def test_sync_library_continue_sync(
    sync_service: KoboSyncService,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test syncing library with continue flag.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    # Create 150 books to exceed SYNC_ITEM_LIMIT (100)
    books = [book_with_rels] * 150
    mock_book_service.list_books.return_value = (books, 150)
    mock_metadata_service.create_book_entitlement.return_value = {"Id": "test-uuid-123"}
    mock_metadata_service.get_book_metadata.return_value = {"Title": "Test Book"}

    results, continue_sync = sync_service.sync_library(
        user_id=1, library_id=1, sync_token=sync_token, only_shelves=False
    )

    assert len(results) == 100  # Limited to SYNC_ITEM_LIMIT
    assert continue_sync is True


def test_sync_library_changed_reading_states(
    sync_service: KoboSyncService,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    mock_reading_state_repo: MagicMock,
    mock_read_status_repo: MagicMock,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test syncing library with changed reading states.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    reading_state = KoboReadingState(
        id=1,
        user_id=1,
        book_id=2,
        last_modified=datetime(2025, 1, 15, tzinfo=UTC),
    )
    mock_reading_state_repo.find_by_user.return_value = [reading_state]
    mock_book_service.list_books.return_value = ([book_with_rels], 1)
    mock_book_service.get_book.return_value = book_with_rels
    mock_metadata_service.create_book_entitlement.return_value = {"Id": "test-uuid-123"}
    mock_metadata_service.get_book_metadata.return_value = {"Title": "Test Book"}
    mock_metadata_service.get_reading_state_response.return_value = {
        "EntitlementId": "test-uuid-123"
    }

    results, _ = sync_service.sync_library(
        user_id=1, library_id=1, sync_token=sync_token, only_shelves=False
    )

    # Should include changed reading state
    assert any("ChangedReadingState" in r for r in results)


# ============================================================================
# Tests for KoboSyncService._get_books_to_sync
# ============================================================================


def test_get_books_to_sync(
    sync_service: KoboSyncService,
    mock_book_service: MagicMock,
    mock_synced_book_repo: MagicMock,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test getting books to sync.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_synced_book_repo : MagicMock
        Mock synced book repository.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    mock_book_service.list_books.return_value = ([book_with_rels], 1)

    results = sync_service._get_books_to_sync(
        user_id=1, library_id=1, sync_token=sync_token, only_shelves=False
    )

    assert len(results) == 1
    mock_book_service.list_books.assert_called_once_with(
        page=1, page_size=1000, full=True
    )


# ============================================================================
# Tests for KoboSyncService._get_shelf_book_ids
# ============================================================================


def test_get_shelf_book_ids_disabled(
    sync_service: KoboSyncService,
) -> None:
    """Test getting shelf book IDs when disabled.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    """
    result = sync_service._get_shelf_book_ids(
        user_id=1, library_id=1, only_shelves=False
    )
    assert result is None


def test_get_shelf_book_ids_no_shelf_service(
    sync_service: KoboSyncService,
) -> None:
    """Test getting shelf book IDs when shelf service is None.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    """
    sync_service._shelf_service = None
    result = sync_service._get_shelf_book_ids(
        user_id=1, library_id=1, only_shelves=True
    )
    assert result is None


def test_get_shelf_book_ids_with_shelves(
    sync_service: KoboSyncService,
    mock_shelf_service: MagicMock,
) -> None:
    """Test getting shelf book IDs with shelves.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_shelf_service : MagicMock
        Mock shelf service.
    """
    from fundamental.models.shelves import BookShelfLink, Shelf

    shelf = Shelf(
        id=1,
        uuid="shelf-uuid",
        name="Test Shelf",
        library_id=1,
        user_id=1,
    )
    book_link = BookShelfLink(id=1, shelf_id=1, book_id=1)
    shelf.book_links = [book_link]
    mock_shelf_service.list_user_shelves.return_value = [shelf]
    sync_service._shelf_service = mock_shelf_service

    result = sync_service._get_shelf_book_ids(
        user_id=1, library_id=1, only_shelves=True
    )

    assert result == {1}


# ============================================================================
# Tests for KoboSyncService._filter_books_for_sync
# ============================================================================


def test_filter_books_for_sync(
    sync_service: KoboSyncService,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test filtering books for sync.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    books = [book_with_rels]
    synced_book_ids: set[int] = set()
    shelf_book_ids: set[int] | None = None

    results = sync_service._filter_books_for_sync(
        books, synced_book_ids, shelf_book_ids, sync_token
    )

    assert len(results) == 1


def test_filter_books_for_sync_no_id(
    sync_service: KoboSyncService,
    book: Book,
    sync_token: SyncToken,
) -> None:
    """Test filtering books for sync when book has no ID.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    book : Book
        Test book.
    sync_token : SyncToken
        Sync token.
    """
    book.id = None
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)
    books = [book_with_rels]
    synced_book_ids: set[int] = set()
    shelf_book_ids: set[int] | None = None

    results = sync_service._filter_books_for_sync(
        books, synced_book_ids, shelf_book_ids, sync_token
    )

    assert len(results) == 0


# ============================================================================
# Tests for KoboSyncService._should_sync_book
# ============================================================================


def test_should_sync_book_new(
    sync_service: KoboSyncService,
    book: Book,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test should sync book when new.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    synced_book_ids: set[int] = set()
    shelf_book_ids: set[int] | None = None

    result = sync_service._should_sync_book(
        book, book_with_rels, synced_book_ids, shelf_book_ids, sync_token
    )

    assert result is True


def test_should_sync_book_already_synced_not_modified(
    sync_service: KoboSyncService,
    book: Book,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test should sync book when already synced and not modified.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    book.last_modified = datetime(2025, 1, 5, tzinfo=UTC)
    synced_book_ids: set[int] = {1}
    shelf_book_ids: set[int] | None = None

    result = sync_service._should_sync_book(
        book, book_with_rels, synced_book_ids, shelf_book_ids, sync_token
    )

    assert result is False


def test_should_sync_book_already_synced_modified(
    sync_service: KoboSyncService,
    book: Book,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test should sync book when already synced but modified.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    book.last_modified = datetime(2025, 1, 15, tzinfo=UTC)
    synced_book_ids: set[int] = {1}
    shelf_book_ids: set[int] | None = None

    result = sync_service._should_sync_book(
        book, book_with_rels, synced_book_ids, shelf_book_ids, sync_token
    )

    assert result is True


def test_should_sync_book_not_in_shelf(
    sync_service: KoboSyncService,
    book: Book,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test should sync book when not in shelf.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    synced_book_ids: set[int] = set()
    shelf_book_ids: set[int] = {2}  # Different book ID

    result = sync_service._should_sync_book(
        book, book_with_rels, synced_book_ids, shelf_book_ids, sync_token
    )

    assert result is False


def test_should_sync_book_no_epub_format(
    sync_service: KoboSyncService,
    book: Book,
    sync_token: SyncToken,
) -> None:
    """Test should sync book when no EPUB format.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    book : Book
        Test book.
    sync_token : SyncToken
        Sync token.
    """
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
        formats=[{"format": "MOBI", "name": "test.mobi", "size": 1000}],
    )
    synced_book_ids: set[int] = set()
    shelf_book_ids: set[int] | None = None

    result = sync_service._should_sync_book(
        book, book_with_rels, synced_book_ids, shelf_book_ids, sync_token
    )

    assert result is False


def test_should_sync_book_no_id(
    sync_service: KoboSyncService,
    book: Book,
    book_with_rels: BookWithFullRelations,
    sync_token: SyncToken,
) -> None:
    """Test should sync book when book has no ID.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    sync_token : SyncToken
        Sync token.
    """
    book.id = None
    synced_book_ids: set[int] = set()
    shelf_book_ids: set[int] | None = None

    result = sync_service._should_sync_book(
        book, book_with_rels, synced_book_ids, shelf_book_ids, sync_token
    )

    assert result is False


# ============================================================================
# Tests for KoboSyncService._get_reading_states_to_sync
# ============================================================================


def test_get_reading_states_to_sync(
    sync_service: KoboSyncService,
    mock_reading_state_repo: MagicMock,
    sync_token: SyncToken,
) -> None:
    """Test getting reading states to sync.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    sync_token : SyncToken
        Sync token.
    """
    reading_state1 = KoboReadingState(
        id=1, user_id=1, book_id=1, last_modified=datetime(2025, 1, 15, tzinfo=UTC)
    )
    reading_state2 = KoboReadingState(
        id=2, user_id=1, book_id=2, last_modified=datetime(2025, 1, 15, tzinfo=UTC)
    )
    mock_reading_state_repo.find_by_user.return_value = [reading_state1, reading_state2]

    results = sync_service._get_reading_states_to_sync(
        user_id=1, sync_token=sync_token, exclude_book_ids=[1]
    )

    assert len(results) == 1
    assert results[0].book_id == 2


# ============================================================================
# Tests for KoboSyncService._mark_book_synced
# ============================================================================


def test_mark_book_synced_new(
    sync_service: KoboSyncService,
    mock_synced_book_repo: MagicMock,
    session: DummySession,
) -> None:
    """Test marking book as synced when new.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_synced_book_repo : MagicMock
        Mock synced book repository.
    session : DummySession
        Dummy session instance.
    """
    mock_synced_book_repo.find_by_user_and_book.return_value = None

    sync_service._mark_book_synced(user_id=1, book_id=1)

    mock_synced_book_repo.add.assert_called_once()
    assert session.flush_count > 0


def test_mark_book_synced_existing(
    sync_service: KoboSyncService,
    mock_synced_book_repo: MagicMock,
    session: DummySession,
) -> None:
    """Test marking book as synced when existing.

    Parameters
    ----------
    sync_service : KoboSyncService
        Service instance.
    mock_synced_book_repo : MagicMock
        Mock synced book repository.
    session : DummySession
        Dummy session instance.
    """
    synced_book = KoboSyncedBook(
        id=1, user_id=1, book_id=1, synced_at=datetime(2025, 1, 1, tzinfo=UTC)
    )
    mock_synced_book_repo.find_by_user_and_book.return_value = synced_book

    sync_service._mark_book_synced(user_id=1, book_id=1)

    mock_synced_book_repo.add.assert_not_called()
    assert synced_book.synced_at > datetime(2025, 1, 1, tzinfo=UTC)
    assert session.flush_count > 0
