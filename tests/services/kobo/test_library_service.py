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

"""Tests for KoboLibraryService to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from fundamental.models.core import Book
from fundamental.models.kobo import KoboArchivedBook
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.kobo.book_lookup_service import KoboBookLookupService
from fundamental.services.kobo.library_service import KoboLibraryService
from fundamental.services.kobo.metadata_service import KoboMetadataService
from fundamental.services.kobo.shelf_service import KoboShelfService
from fundamental.services.kobo.store_proxy_service import KoboStoreProxyService
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
    return MagicMock()


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
def mock_sync_service() -> MagicMock:
    """Create a mock KoboSyncService.

    Returns
    -------
    MagicMock
        Mock sync service instance.
    """
    return MagicMock(spec=KoboSyncService)


@pytest.fixture
def mock_shelf_service() -> MagicMock:
    """Create a mock KoboShelfService.

    Returns
    -------
    MagicMock
        Mock shelf service instance.
    """
    return MagicMock(spec=KoboShelfService)


@pytest.fixture
def mock_proxy_service() -> MagicMock:
    """Create a mock KoboStoreProxyService.

    Returns
    -------
    MagicMock
        Mock proxy service instance.
    """
    return MagicMock(spec=KoboStoreProxyService)


@pytest.fixture
def mock_book_lookup_service() -> MagicMock:
    """Create a mock KoboBookLookupService.

    Returns
    -------
    MagicMock
        Mock book lookup service instance.
    """
    return MagicMock(spec=KoboBookLookupService)


@pytest.fixture
def library_service(
    session: DummySession,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    mock_sync_service: MagicMock,
    mock_shelf_service: MagicMock,
    mock_proxy_service: MagicMock,
    mock_book_lookup_service: MagicMock,
) -> KoboLibraryService:
    """Create KoboLibraryService instance for testing.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    mock_sync_service : MagicMock
        Mock sync service.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.

    Returns
    -------
    KoboLibraryService
        Service instance.
    """
    return KoboLibraryService(
        session,  # type: ignore[arg-type]
        mock_book_service,
        mock_metadata_service,
        mock_sync_service,
        mock_shelf_service,
        mock_proxy_service,
        mock_book_lookup_service,
    )


@pytest.fixture
def book() -> Book:
    """Create a test book.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(id=1, title="Test Book", uuid="test-uuid-123")


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
        formats=[],
    )


@pytest.fixture
def mock_request() -> MagicMock:
    """Create a mock FastAPI Request.

    Returns
    -------
    MagicMock
        Mock request instance.
    """
    request = MagicMock(spec=Request)
    request.path_params = {"auth_token": "test_token"}
    request.url.path = "/kobo/test_token/v1/library/sync"
    request.method = "GET"
    request.headers = {}
    return request


# ============================================================================
# Tests for KoboLibraryService.__init__
# ============================================================================


def test_init(
    session: DummySession,
    mock_book_service: MagicMock,
    mock_metadata_service: MagicMock,
    mock_sync_service: MagicMock,
    mock_shelf_service: MagicMock,
    mock_proxy_service: MagicMock,
    mock_book_lookup_service: MagicMock,
) -> None:
    """Test KoboLibraryService initialization.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_book_service : MagicMock
        Mock book service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    mock_sync_service : MagicMock
        Mock sync service.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    """
    service = KoboLibraryService(
        session,  # type: ignore[arg-type]
        mock_book_service,
        mock_metadata_service,
        mock_sync_service,
        mock_shelf_service,
        mock_proxy_service,
        mock_book_lookup_service,
    )
    assert service._session == session
    assert service._book_service == mock_book_service
    assert service._metadata_service == mock_metadata_service
    assert service._sync_service == mock_sync_service
    assert service._shelf_service == mock_shelf_service
    assert service._proxy_service == mock_proxy_service
    assert service._book_lookup_service == mock_book_lookup_service


# ============================================================================
# Tests for KoboLibraryService.get_book_metadata
# ============================================================================


def test_get_book_metadata_success(
    library_service: KoboLibraryService,
    mock_book_lookup_service: MagicMock,
    mock_metadata_service: MagicMock,
    book: Book,
    book_with_rels: BookWithFullRelations,
) -> None:
    """Test getting book metadata successfully.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_metadata_service : MagicMock
        Mock metadata service.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    """
    metadata = {"Title": "Test Book", "Id": "test-uuid-123"}
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)
    mock_book_lookup_service.get_book_with_relations.return_value = book_with_rels
    mock_metadata_service.get_book_metadata.return_value = metadata

    result = library_service.get_book_metadata("test-uuid-123")

    assert result == metadata
    mock_book_lookup_service.find_book_by_uuid.assert_called_once_with("test-uuid-123")
    mock_book_lookup_service.get_book_with_relations.assert_called_once_with(1)
    mock_metadata_service.get_book_metadata.assert_called_once_with(book_with_rels)


def test_get_book_metadata_book_not_found(
    library_service: KoboLibraryService,
    mock_book_lookup_service: MagicMock,
) -> None:
    """Test getting book metadata when book is not found.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        library_service.get_book_metadata("non-existent-uuid")

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "book_not_found"


def test_get_book_metadata_book_with_rels_not_found(
    library_service: KoboLibraryService,
    mock_book_lookup_service: MagicMock,
    book: Book,
) -> None:
    """Test getting book metadata when book with relations is not found.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    book : Book
        Test book.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)
    mock_book_lookup_service.get_book_with_relations.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        library_service.get_book_metadata("test-uuid-123")

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "book_not_found"


# ============================================================================
# Tests for KoboLibraryService.archive_book
# ============================================================================


def test_archive_book_new(
    library_service: KoboLibraryService,
    mock_book_lookup_service: MagicMock,
    book: Book,
    session: DummySession,
) -> None:
    """Test archiving a book that hasn't been archived before.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    book : Book
        Test book.
    session : DummySession
        Dummy session instance.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)

    with (
        patch(
            "fundamental.services.kobo.library_service.KoboArchivedBookRepository"
        ) as mock_archived_repo_class,
        patch(
            "fundamental.services.kobo.library_service.KoboSyncedBookRepository"
        ) as mock_synced_repo_class,
    ):
        mock_archived_repo = MagicMock()
        mock_archived_repo.find_by_user_and_book.return_value = None
        mock_archived_repo.add = MagicMock()
        mock_archived_repo_class.return_value = mock_archived_repo

        mock_synced_repo = MagicMock()
        mock_synced_repo.delete_by_user_and_book = MagicMock()
        mock_synced_repo_class.return_value = mock_synced_repo

        library_service.archive_book(user_id=1, book_uuid="test-uuid-123")

        mock_archived_repo.find_by_user_and_book.assert_called_once_with(1, 1)
        mock_archived_repo.add.assert_called_once()
        mock_synced_repo.delete_by_user_and_book.assert_called_once_with(1, 1)


def test_archive_book_existing(
    library_service: KoboLibraryService,
    mock_book_lookup_service: MagicMock,
    book: Book,
) -> None:
    """Test archiving a book that has been archived before.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    book : Book
        Test book.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)
    archived_book = KoboArchivedBook(id=1, user_id=1, book_id=1, is_archived=False)

    with (
        patch(
            "fundamental.services.kobo.library_service.KoboArchivedBookRepository"
        ) as mock_archived_repo_class,
        patch(
            "fundamental.services.kobo.library_service.KoboSyncedBookRepository"
        ) as mock_synced_repo_class,
    ):
        mock_archived_repo = MagicMock()
        mock_archived_repo.find_by_user_and_book.return_value = archived_book
        mock_archived_repo_class.return_value = mock_archived_repo

        mock_synced_repo = MagicMock()
        mock_synced_repo.delete_by_user_and_book = MagicMock()
        mock_synced_repo_class.return_value = mock_synced_repo

        library_service.archive_book(user_id=1, book_uuid="test-uuid-123")

        assert archived_book.is_archived is True
        mock_archived_repo.add.assert_not_called()
        mock_synced_repo.delete_by_user_and_book.assert_called_once_with(1, 1)


def test_archive_book_not_found(
    library_service: KoboLibraryService,
    mock_book_lookup_service: MagicMock,
) -> None:
    """Test archiving a book when book is not found.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        library_service.archive_book(user_id=1, book_uuid="non-existent-uuid")

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "book_not_found"


# ============================================================================
# Tests for KoboLibraryService.sync_library
# ============================================================================


@pytest.mark.asyncio
async def test_sync_library_success(
    library_service: KoboLibraryService,
    mock_sync_service: MagicMock,
    mock_shelf_service: MagicMock,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
    session: DummySession,
) -> None:
    """Test successful library sync.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_sync_service : MagicMock
        Mock sync service.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    session : DummySession
        Dummy session instance.
    """
    sync_results = [{"NewEntitlement": {"Id": "book1"}}]
    shelf_results = [{"NewTag": {"Id": "tag1"}}]
    sync_token = SyncToken()

    mock_sync_service.sync_library.return_value = (sync_results, False)
    mock_shelf_service.sync_shelves.return_value = shelf_results
    mock_proxy_service.should_proxy.return_value = False

    result = await library_service.sync_library(
        request=mock_request, user_id=1, library_id=1, sync_token=sync_token
    )

    assert isinstance(result, JSONResponse)
    assert result.status_code == 200
    assert session.commit_count == 1
    mock_sync_service.sync_library.assert_called_once_with(
        user_id=1, library_id=1, sync_token=sync_token, only_shelves=False
    )
    mock_shelf_service.sync_shelves.assert_called_once_with(
        user_id=1,
        library_id=1,
        sync_token=sync_token,
        book_service=library_service._book_service,
    )


@pytest.mark.asyncio
async def test_sync_library_with_continue(
    library_service: KoboLibraryService,
    mock_sync_service: MagicMock,
    mock_shelf_service: MagicMock,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test library sync with continue flag.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_sync_service : MagicMock
        Mock sync service.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    sync_results = [{"NewEntitlement": {"Id": "book1"}}]
    sync_token = SyncToken()

    mock_sync_service.sync_library.return_value = (sync_results, True)
    mock_shelf_service.sync_shelves.return_value = []
    mock_proxy_service.should_proxy.return_value = False

    result = await library_service.sync_library(
        request=mock_request, user_id=1, library_id=1, sync_token=sync_token
    )

    assert isinstance(result, JSONResponse)
    assert result.headers.get("x-kobo-sync") == "continue"


@pytest.mark.asyncio
async def test_sync_library_with_proxy(
    library_service: KoboLibraryService,
    mock_sync_service: MagicMock,
    mock_shelf_service: MagicMock,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test library sync with proxy enabled.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_sync_service : MagicMock
        Mock sync service.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    sync_results = [{"NewEntitlement": {"Id": "book1"}}]
    sync_token = SyncToken()

    mock_sync_service.sync_library.return_value = (sync_results, False)
    mock_shelf_service.sync_shelves.return_value = []
    mock_proxy_service.should_proxy.return_value = True

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(
        return_value=[{"StoreEntitlement": {"Id": "store1"}}]
    )
    mock_response.headers = {}
    mock_proxy_service.proxy_request = AsyncMock(return_value=mock_response)
    merged_results = [*sync_results, {"StoreEntitlement": {"Id": "store1"}}]
    mock_proxy_service.merge_sync_responses = MagicMock(return_value=merged_results)

    result = await library_service.sync_library(
        request=mock_request, user_id=1, library_id=1, sync_token=sync_token
    )

    assert isinstance(result, JSONResponse)
    mock_proxy_service.proxy_request.assert_called_once()


@pytest.mark.asyncio
async def test_sync_library_proxy_error(
    library_service: KoboLibraryService,
    mock_sync_service: MagicMock,
    mock_shelf_service: MagicMock,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test library sync when proxy request fails.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_sync_service : MagicMock
        Mock sync service.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    sync_results = [{"NewEntitlement": {"Id": "book1"}}]
    sync_token = SyncToken()

    mock_sync_service.sync_library.return_value = (sync_results, False)
    mock_shelf_service.sync_shelves.return_value = []
    mock_proxy_service.should_proxy.return_value = True
    mock_proxy_service.proxy_request = AsyncMock(side_effect=httpx.HTTPError("Error"))

    result = await library_service.sync_library(
        request=mock_request, user_id=1, library_id=1, sync_token=sync_token
    )

    assert isinstance(result, JSONResponse)
    # Should return local results even if proxy fails
    assert len(result.body) > 0


@pytest.mark.asyncio
async def test_sync_library_proxy_non_200(
    library_service: KoboLibraryService,
    mock_sync_service: MagicMock,
    mock_shelf_service: MagicMock,
    mock_proxy_service: MagicMock,
    mock_request: MagicMock,
) -> None:
    """Test library sync when proxy returns non-200 status.

    Parameters
    ----------
    library_service : KoboLibraryService
        Service instance.
    mock_sync_service : MagicMock
        Mock sync service.
    mock_shelf_service : MagicMock
        Mock shelf service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    mock_request : MagicMock
        Mock request.
    """
    sync_results = [{"NewEntitlement": {"Id": "book1"}}]
    sync_token = SyncToken()

    mock_sync_service.sync_library.return_value = (sync_results, False)
    mock_shelf_service.sync_shelves.return_value = []
    mock_proxy_service.should_proxy.return_value = True

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_proxy_service.proxy_request = AsyncMock(return_value=mock_response)

    result = await library_service.sync_library(
        request=mock_request, user_id=1, library_id=1, sync_token=sync_token
    )

    assert isinstance(result, JSONResponse)
    # Should return local results even if proxy returns error
    assert len(result.body) > 0
