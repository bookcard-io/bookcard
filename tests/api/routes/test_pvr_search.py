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

"""Tests for PVR search routes to achieve comprehensive coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException, status

import bookcard.api.routes.pvr_search as pvr_search_routes
from bookcard.api.schemas.pvr_search import (
    PVRDownloadRequest,
    PVRDownloadResponse,
    PVRSearchRequest,
    PVRSearchResponse,
    PVRSearchResultsResponse,
)
from bookcard.models.auth import User
from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.models.pvr import (
    DownloadItem as DBDownloadItem,
)
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.models import IndexerSearchResult

# Rebuild Pydantic models to resolve forward references
PVRSearchResponse.model_rebuild()
PVRSearchResultsResponse.model_rebuild()
PVRDownloadResponse.model_rebuild()

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


@pytest.fixture
def release_info() -> ReleaseInfo:
    """Create a release info for testing.

    Returns
    -------
    ReleaseInfo
        Release info instance.
    """
    return ReleaseInfo(
        indexer_id=1,
        title="Test Book - EPUB",
        download_url="magnet:?xt=urn:btih:test123",
        size_bytes=1024000,
        publish_date=datetime.now(UTC),
        seeders=10,
        leechers=2,
        quality="epub",
        author="Test Author",
        isbn="1234567890",
        description="Test book release",
        category="Books",
    )


@pytest.fixture
def indexer_search_result(release_info: ReleaseInfo) -> IndexerSearchResult:
    """Create an indexer search result for testing.

    Parameters
    ----------
    release_info : ReleaseInfo
        Release info fixture.

    Returns
    -------
    IndexerSearchResult
        Indexer search result instance.
    """
    return IndexerSearchResult(
        release=release_info,
        score=0.95,
        indexer_name="Test Indexer",
        indexer_priority=0,
    )


@pytest.fixture
def download_item() -> DBDownloadItem:
    """Create a download item for testing.

    Returns
    -------
    DBDownloadItem
        Download item instance.
    """
    return DBDownloadItem(
        id=1,
        tracked_book_id=1,
        download_client_id=1,
        indexer_id=1,
        client_item_id="client-123",
        title="Test Book - EPUB",
        download_url="magnet:?xt=urn:btih:test123",
        status=DownloadItemStatus.QUEUED,
        progress=0.0,
        size_bytes=1024000,
        quality="epub",
        started_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def download_client() -> DownloadClientDefinition:
    """Create a download client definition for testing.

    Returns
    -------
    DownloadClientDefinition
        Download client definition instance.
    """
    from bookcard.models.pvr import DownloadClientType

    return DownloadClientDefinition(
        id=1,
        name="Test qBittorrent",
        client_type=DownloadClientType.QBITTORRENT,
        host="localhost",
        port=8080,
        username="admin",
        password="password",
        use_ssl=False,
        enabled=True,
        priority=0,
    )


@pytest.fixture
def valid_fernet_key() -> str:
    """Generate a valid Fernet key.

    Returns
    -------
    str
        Base64-encoded Fernet key.
    """
    return Fernet.generate_key().decode()


class TestGetTrackedBookService:
    """Test _get_tracked_book_service function."""

    def test_get_tracked_book_service(self, session: DummySession) -> None:
        """Test _get_tracked_book_service creates TrackedBookService instance.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = pvr_search_routes._get_tracked_book_service(session)
        assert service is not None
        assert hasattr(service, "_session")
        assert service._session == session


class TestGetIndexerSearchService:
    """Test _get_indexer_search_service function."""

    def test_get_indexer_search_service(
        self, session: DummySession, valid_fernet_key: str
    ) -> None:
        """Test _get_indexer_search_service creates IndexerSearchService instance.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key
        service = pvr_search_routes._get_indexer_search_service(session, request)
        assert service is not None
        assert hasattr(service, "_indexer_service")


class TestGetDownloadService:
    """Test _get_download_service function."""

    def test_get_download_service(
        self, session: DummySession, mock_request: MagicMock
    ) -> None:
        """Test _get_download_service creates DownloadService instance.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        service = pvr_search_routes._get_download_service(session, mock_request)
        assert service is not None
        assert hasattr(service, "_download_item_repo")
        assert hasattr(service, "_client_service")


class TestGetPermissionHelper:
    """Test _get_permission_helper function."""

    def test_get_permission_helper(self, session: DummySession) -> None:
        """Test _get_permission_helper creates BookPermissionHelper instance.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        helper = pvr_search_routes._get_permission_helper(session)
        assert helper is not None
        assert hasattr(helper, "_permission_service")


class TestRaiseNotFound:
    """Test _raise_not_found function."""

    @pytest.mark.parametrize("book_id", [1, 42, 999])
    def test_raise_not_found(self, book_id: int) -> None:
        """Test _raise_not_found raises HTTPException with 404.

        Parameters
        ----------
        book_id : int
            Tracked book ID to test.
        """
        with pytest.raises(HTTPException) as exc_info:
            pvr_search_routes._raise_not_found(book_id)

        exc = exc_info.value
        assert isinstance(exc, HTTPException)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == f"Tracked book {book_id} not found"


class TestRaiseDownloadClientNotFound:
    """Test _raise_download_client_not_found function."""

    @pytest.mark.parametrize("client_id", [1, 42, 999])
    def test_raise_download_client_not_found(self, client_id: int) -> None:
        """Test _raise_download_client_not_found raises HTTPException with 404.

        Parameters
        ----------
        client_id : int
            Download client ID to test.
        """
        with pytest.raises(HTTPException) as exc_info:
            pvr_search_routes._raise_download_client_not_found(client_id)

        exc = exc_info.value
        assert isinstance(exc, HTTPException)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == f"Download client {client_id} not found"


class TestSearchTrackedBook:
    """Test search_tracked_book endpoint."""

    def test_search_tracked_book_success(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        valid_fernet_key: str,
    ) -> None:
        """Test search_tracked_book initiates search successfully.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request_data = PVRSearchRequest(
            tracked_book_id=1,
            max_results_per_indexer=100,
        )
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with (
            patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_class,
            patch(
                "bookcard.api.routes.pvr_search.TrackedBookService"
            ) as mock_service_class,
            patch(
                "bookcard.api.routes.pvr_search.IndexerSearchService"
            ) as mock_search_class,
        ):
            # Mock permission helper
            mock_permission_helper = MagicMock()
            mock_permission_helper.check_read_permission.return_value = None
            mock_helper_class.return_value = mock_permission_helper

            # Mock tracked book service
            mock_tracked_service = MagicMock()
            mock_tracked_service.get_tracked_book.return_value = tracked_book
            mock_service_class.return_value = mock_tracked_service

            # Mock search service
            mock_search_service = MagicMock()
            mock_search_service.search_all_indexers.return_value = [
                indexer_search_result
            ]
            mock_search_class.return_value = mock_search_service

            result = pvr_search_routes.search_tracked_book(
                request=request_data,
                session=session,
                current_user=user,
                permission_helper=mock_permission_helper,
                fastapi_request=request,
            )

            assert isinstance(result, PVRSearchResponse)
            assert result.tracked_book_id == 1
            assert result.search_initiated is True
            assert "results found" in result.message
            mock_permission_helper.check_read_permission.assert_called_once_with(user)
            mock_tracked_service.get_tracked_book.assert_called_once_with(1)
            mock_search_service.search_all_indexers.assert_called_once()

    def test_search_tracked_book_not_found(
        self,
        session: DummySession,
        user: User,
        valid_fernet_key: str,
    ) -> None:
        """Test search_tracked_book raises 404 when tracked book not found.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request_data = PVRSearchRequest(
            tracked_book_id=999,
            max_results_per_indexer=100,
        )
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with (
            patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_class,
            patch(
                "bookcard.api.routes.pvr_search.TrackedBookService"
            ) as mock_service_class,
        ):
            # Mock permission helper
            mock_permission_helper = MagicMock()
            mock_permission_helper.check_read_permission.return_value = None
            mock_helper_class.return_value = mock_permission_helper

            # Mock tracked book service
            mock_tracked_service = MagicMock()
            mock_tracked_service.get_tracked_book.return_value = None
            mock_service_class.return_value = mock_tracked_service

            with pytest.raises(HTTPException) as exc_info:
                pvr_search_routes.search_tracked_book(
                    request=request_data,
                    session=session,
                    current_user=user,
                    permission_helper=mock_permission_helper,
                    fastapi_request=request,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_search_tracked_book_empty_query(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        valid_fernet_key: str,
    ) -> None:
        """Test search_tracked_book raises 400 when book has no title or author.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        # Create tracked book with empty title and author
        empty_book = TrackedBook(
            id=2,
            title="",
            author="",
            status=TrackedBookStatus.WANTED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        request_data = PVRSearchRequest(
            tracked_book_id=2,
            max_results_per_indexer=100,
        )
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with (
            patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_class,
            patch(
                "bookcard.api.routes.pvr_search.TrackedBookService"
            ) as mock_service_class,
        ):
            # Mock permission helper
            mock_permission_helper = MagicMock()
            mock_permission_helper.check_read_permission.return_value = None
            mock_helper_class.return_value = mock_permission_helper

            # Mock tracked book service
            mock_tracked_service = MagicMock()
            mock_tracked_service.get_tracked_book.return_value = empty_book
            mock_service_class.return_value = mock_tracked_service

            with pytest.raises(HTTPException) as exc_info:
                pvr_search_routes.search_tracked_book(
                    request=request_data,
                    session=session,
                    current_user=user,
                    permission_helper=mock_permission_helper,
                    fastapi_request=request,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "title or author" in exc_info.value.detail

    def test_search_tracked_book_search_exception(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        valid_fernet_key: str,
    ) -> None:
        """Test search_tracked_book handles search exceptions.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        valid_fernet_key : str
            Valid Fernet key fixture.
        """
        request_data = PVRSearchRequest(
            tracked_book_id=1,
            max_results_per_indexer=100,
        )
        request = MagicMock()
        request.app.state.config.encryption_key = valid_fernet_key

        with (
            patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_class,
            patch(
                "bookcard.api.routes.pvr_search.TrackedBookService"
            ) as mock_service_class,
            patch(
                "bookcard.api.routes.pvr_search.IndexerSearchService"
            ) as mock_search_class,
        ):
            # Mock permission helper
            mock_permission_helper = MagicMock()
            mock_permission_helper.check_read_permission.return_value = None
            mock_helper_class.return_value = mock_permission_helper

            # Mock tracked book service
            mock_tracked_service = MagicMock()
            mock_tracked_service.get_tracked_book.return_value = tracked_book
            mock_service_class.return_value = mock_tracked_service

            # Mock search service to raise exception
            mock_search_service = MagicMock()
            mock_search_service.search_all_indexers.side_effect = RuntimeError(
                "Search failed"
            )
            mock_search_class.return_value = mock_search_service

            with pytest.raises(HTTPException) as exc_info:
                pvr_search_routes.search_tracked_book(
                    request=request_data,
                    session=session,
                    current_user=user,
                    permission_helper=mock_permission_helper,
                    fastapi_request=request,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Search failed" in exc_info.value.detail


class TestGetSearchResults:
    """Test get_search_results endpoint."""

    def test_get_search_results_success(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
    ) -> None:
        """Test get_search_results returns cached results successfully.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        """
        # Populate cache
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache[1] = [indexer_search_result]

        try:
            with (
                patch(
                    "bookcard.api.routes.pvr_search.BookPermissionHelper"
                ) as mock_helper_class,
                patch(
                    "bookcard.api.routes.pvr_search.TrackedBookService"
                ) as mock_service_class,
            ):
                # Mock permission helper
                mock_permission_helper = MagicMock()
                mock_permission_helper.check_read_permission.return_value = None
                mock_helper_class.return_value = mock_permission_helper

                # Mock tracked book service
                mock_tracked_service = MagicMock()
                mock_tracked_service.get_tracked_book.return_value = tracked_book
                mock_service_class.return_value = mock_tracked_service

                result = pvr_search_routes.get_search_results(
                    tracked_book_id=1,
                    session=session,
                    current_user=user,
                    permission_helper=mock_permission_helper,
                )

                assert isinstance(result, PVRSearchResultsResponse)
                assert result.tracked_book_id == 1
                assert result.total == 1
                assert len(result.results) == 1
                assert result.results[0].score == indexer_search_result.score
                mock_permission_helper.check_read_permission.assert_called_once_with(
                    user
                )
        finally:
            # Clean up cache
            with pvr_search_routes._cache_lock:
                pvr_search_routes._search_results_cache.pop(1, None)

    def test_get_search_results_not_found(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
    ) -> None:
        """Test get_search_results raises 404 when tracked book not found.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        with (
            patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_class,
            patch(
                "bookcard.api.routes.pvr_search.TrackedBookService"
            ) as mock_service_class,
        ):
            # Mock permission helper
            mock_permission_helper = MagicMock()
            mock_permission_helper.check_read_permission.return_value = None
            mock_helper_class.return_value = mock_permission_helper

            # Mock tracked book service
            mock_tracked_service = MagicMock()
            mock_tracked_service.get_tracked_book.return_value = None
            mock_service_class.return_value = mock_tracked_service

            with pytest.raises(HTTPException) as exc_info:
                pvr_search_routes.get_search_results(
                    tracked_book_id=999,
                    session=session,
                    current_user=user,
                    permission_helper=mock_permission_helper,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_search_results_no_cache(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
    ) -> None:
        """Test get_search_results raises 404 when no cached results available.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        # Ensure cache is empty
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache.pop(1, None)

        with (
            patch(
                "bookcard.api.routes.pvr_search.BookPermissionHelper"
            ) as mock_helper_class,
            patch(
                "bookcard.api.routes.pvr_search.TrackedBookService"
            ) as mock_service_class,
        ):
            # Mock permission helper
            mock_permission_helper = MagicMock()
            mock_permission_helper.check_read_permission.return_value = None
            mock_helper_class.return_value = mock_permission_helper

            # Mock tracked book service
            mock_tracked_service = MagicMock()
            mock_tracked_service.get_tracked_book.return_value = tracked_book
            mock_service_class.return_value = mock_tracked_service

            with pytest.raises(HTTPException) as exc_info:
                pvr_search_routes.get_search_results(
                    tracked_book_id=1,
                    session=session,
                    current_user=user,
                    permission_helper=mock_permission_helper,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "No search results available" in exc_info.value.detail


class TestTriggerDownload:
    """Test trigger_download endpoint."""

    def test_trigger_download_success(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        download_item: DBDownloadItem,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download initiates download successfully.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        download_item : DBDownloadItem
            Download item fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=0)

        # Populate cache
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache[1] = [indexer_search_result]

        try:
            with (
                patch(
                    "bookcard.api.routes.pvr_search.PermissionService"
                ) as mock_perm_class,
                patch(
                    "bookcard.api.routes.pvr_search.TrackedBookService"
                ) as mock_tracked_class,
                patch(
                    "bookcard.api.routes.pvr_search.DownloadService"
                ) as mock_download_class,
            ):
                # Mock permission service
                mock_permission_service = MagicMock()
                mock_permission_service.check_permission.return_value = None
                mock_perm_class.return_value = mock_permission_service

                # Mock tracked book service
                mock_tracked_service = MagicMock()
                mock_tracked_service.get_tracked_book.return_value = tracked_book
                mock_tracked_class.return_value = mock_tracked_service

                # Mock download service
                mock_download_service = MagicMock()
                mock_download_service.initiate_download.return_value = download_item
                mock_download_class.return_value = mock_download_service

                result = pvr_search_routes.trigger_download(
                    tracked_book_id=1,
                    request=request,
                    session=session,
                    current_user=user,
                    fastapi_request=mock_request,
                )

                assert isinstance(result, PVRDownloadResponse)
                assert result.tracked_book_id == 1
                assert result.download_item_id == download_item.id
                assert result.release_title == indexer_search_result.release.title
                mock_permission_service.check_permission.assert_called_once_with(
                    user, "books", "create"
                )
                mock_download_service.initiate_download.assert_called_once()
        finally:
            # Clean up cache
            with pvr_search_routes._cache_lock:
                pvr_search_routes._search_results_cache.pop(1, None)

    def test_trigger_download_with_client_id(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        download_item: DBDownloadItem,
        download_client: DownloadClientDefinition,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download with specific download client ID.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        download_item : DBDownloadItem
            Download item fixture.
        download_client : DownloadClientDefinition
            Download client fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=0, download_client_id=1)

        # Populate cache
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache[1] = [indexer_search_result]

        try:
            with (
                patch(
                    "bookcard.api.routes.pvr_search.PermissionService"
                ) as mock_perm_class,
                patch(
                    "bookcard.api.routes.pvr_search.TrackedBookService"
                ) as mock_tracked_class,
                patch(
                    "bookcard.api.routes.pvr_search.DownloadClientService"
                ) as mock_client_class,
                patch(
                    "bookcard.api.routes.pvr_search.DownloadService"
                ) as mock_download_class,
            ):
                # Mock permission service
                mock_permission_service = MagicMock()
                mock_permission_service.check_permission.return_value = None
                mock_perm_class.return_value = mock_permission_service

                # Mock tracked book service
                mock_tracked_service = MagicMock()
                mock_tracked_service.get_tracked_book.return_value = tracked_book
                mock_tracked_class.return_value = mock_tracked_service

                # Mock download client service
                mock_client_service = MagicMock()
                mock_client_service.get_decrypted_download_client.return_value = (
                    download_client
                )
                mock_client_class.return_value = mock_client_service

                # Mock download service
                mock_download_service = MagicMock()
                mock_download_service.initiate_download.return_value = download_item
                mock_download_class.return_value = mock_download_service

                result = pvr_search_routes.trigger_download(
                    tracked_book_id=1,
                    request=request,
                    session=session,
                    current_user=user,
                    fastapi_request=mock_request,
                )

                assert isinstance(result, PVRDownloadResponse)
                mock_client_service.get_decrypted_download_client.assert_called_once_with(
                    1
                )
                mock_download_service.initiate_download.assert_called_once()
        finally:
            # Clean up cache
            with pvr_search_routes._cache_lock:
                pvr_search_routes._search_results_cache.pop(1, None)

    def test_trigger_download_not_found(
        self,
        session: DummySession,
        user: User,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download raises 404 when tracked book not found.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=0)

        with (
            patch(
                "bookcard.api.routes.pvr_search.PermissionService"
            ) as mock_perm_class,
            patch(
                "bookcard.api.routes.pvr_search.TrackedBookService"
            ) as mock_tracked_class,
        ):
            # Mock permission service
            mock_permission_service = MagicMock()
            mock_permission_service.check_permission.return_value = None
            mock_perm_class.return_value = mock_permission_service

            # Mock tracked book service
            mock_tracked_service = MagicMock()
            mock_tracked_service.get_tracked_book.return_value = None
            mock_tracked_class.return_value = mock_tracked_service

            with pytest.raises(HTTPException) as exc_info:
                pvr_search_routes.trigger_download(
                    tracked_book_id=999,
                    request=request,
                    session=session,
                    current_user=user,
                    fastapi_request=mock_request,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_trigger_download_no_results(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download raises 404 when no cached results available.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=0)

        # Ensure cache is empty
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache.pop(1, None)

        with (
            patch(
                "bookcard.api.routes.pvr_search.PermissionService"
            ) as mock_perm_class,
            patch(
                "bookcard.api.routes.pvr_search.TrackedBookService"
            ) as mock_tracked_class,
        ):
            # Mock permission service
            mock_permission_service = MagicMock()
            mock_permission_service.check_permission.return_value = None
            mock_perm_class.return_value = mock_permission_service

            # Mock tracked book service
            mock_tracked_service = MagicMock()
            mock_tracked_service.get_tracked_book.return_value = tracked_book
            mock_tracked_class.return_value = mock_tracked_service

            with pytest.raises(HTTPException) as exc_info:
                pvr_search_routes.trigger_download(
                    tracked_book_id=1,
                    request=request,
                    session=session,
                    current_user=user,
                    fastapi_request=mock_request,
                )

            assert isinstance(exc_info.value, HTTPException)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "No search results available" in exc_info.value.detail

    def test_trigger_download_invalid_index(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download raises 400 when release index is invalid.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=999)  # Invalid index

        # Populate cache with one result
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache[1] = [indexer_search_result]

        try:
            with (
                patch(
                    "bookcard.api.routes.pvr_search.PermissionService"
                ) as mock_perm_class,
                patch(
                    "bookcard.api.routes.pvr_search.TrackedBookService"
                ) as mock_tracked_class,
            ):
                # Mock permission service
                mock_permission_service = MagicMock()
                mock_permission_service.check_permission.return_value = None
                mock_perm_class.return_value = mock_permission_service

                # Mock tracked book service
                mock_tracked_service = MagicMock()
                mock_tracked_service.get_tracked_book.return_value = tracked_book
                mock_tracked_class.return_value = mock_tracked_service

                with pytest.raises(HTTPException) as exc_info:
                    pvr_search_routes.trigger_download(
                        tracked_book_id=1,
                        request=request,
                        session=session,
                        current_user=user,
                        fastapi_request=mock_request,
                    )

                assert isinstance(exc_info.value, HTTPException)
                assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
                assert "Invalid release index" in exc_info.value.detail
        finally:
            # Clean up cache
            with pvr_search_routes._cache_lock:
                pvr_search_routes._search_results_cache.pop(1, None)

    def test_trigger_download_client_not_found(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download raises 404 when download client not found.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=0, download_client_id=999)

        # Populate cache
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache[1] = [indexer_search_result]

        try:
            with (
                patch(
                    "bookcard.api.routes.pvr_search.PermissionService"
                ) as mock_perm_class,
                patch(
                    "bookcard.api.routes.pvr_search.TrackedBookService"
                ) as mock_tracked_class,
                patch(
                    "bookcard.api.routes.pvr_search.DownloadClientService"
                ) as mock_client_class,
            ):
                # Mock permission service
                mock_permission_service = MagicMock()
                mock_permission_service.check_permission.return_value = None
                mock_perm_class.return_value = mock_permission_service

                # Mock tracked book service
                mock_tracked_service = MagicMock()
                mock_tracked_service.get_tracked_book.return_value = tracked_book
                mock_tracked_class.return_value = mock_tracked_service

                # Mock download client service to return None
                mock_client_service = MagicMock()
                mock_client_service.get_decrypted_download_client.return_value = None
                mock_client_class.return_value = mock_client_service

                with pytest.raises(HTTPException) as exc_info:
                    pvr_search_routes.trigger_download(
                        tracked_book_id=1,
                        request=request,
                        session=session,
                        current_user=user,
                        fastapi_request=mock_request,
                    )

                assert isinstance(exc_info.value, HTTPException)
                assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
                assert "Download client" in exc_info.value.detail
        finally:
            # Clean up cache
            with pvr_search_routes._cache_lock:
                pvr_search_routes._search_results_cache.pop(1, None)

    def test_trigger_download_value_error(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download handles ValueError from download service.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=0)

        # Populate cache
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache[1] = [indexer_search_result]

        try:
            with (
                patch(
                    "bookcard.api.routes.pvr_search.PermissionService"
                ) as mock_perm_class,
                patch(
                    "bookcard.api.routes.pvr_search.TrackedBookService"
                ) as mock_tracked_class,
                patch(
                    "bookcard.api.routes.pvr_search.DownloadService"
                ) as mock_download_class,
            ):
                # Mock permission service
                mock_permission_service = MagicMock()
                mock_permission_service.check_permission.return_value = None
                mock_perm_class.return_value = mock_permission_service

                # Mock tracked book service
                mock_tracked_service = MagicMock()
                mock_tracked_service.get_tracked_book.return_value = tracked_book
                mock_tracked_class.return_value = mock_tracked_service

                # Mock download service to raise ValueError
                mock_download_service = MagicMock()
                mock_download_service.initiate_download.side_effect = ValueError(
                    "No suitable client"
                )
                mock_download_class.return_value = mock_download_service

                with pytest.raises(HTTPException) as exc_info:
                    pvr_search_routes.trigger_download(
                        tracked_book_id=1,
                        request=request,
                        session=session,
                        current_user=user,
                        fastapi_request=mock_request,
                    )

                assert isinstance(exc_info.value, HTTPException)
                assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
                assert "No suitable client" in exc_info.value.detail
        finally:
            # Clean up cache
            with pvr_search_routes._cache_lock:
                pvr_search_routes._search_results_cache.pop(1, None)

    def test_trigger_download_pvr_provider_error(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download handles PVRProviderError from download service.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=0)

        # Populate cache
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache[1] = [indexer_search_result]

        try:
            with (
                patch(
                    "bookcard.api.routes.pvr_search.PermissionService"
                ) as mock_perm_class,
                patch(
                    "bookcard.api.routes.pvr_search.TrackedBookService"
                ) as mock_tracked_class,
                patch(
                    "bookcard.api.routes.pvr_search.DownloadService"
                ) as mock_download_class,
            ):
                # Mock permission service
                mock_permission_service = MagicMock()
                mock_permission_service.check_permission.return_value = None
                mock_perm_class.return_value = mock_permission_service

                # Mock tracked book service
                mock_tracked_service = MagicMock()
                mock_tracked_service.get_tracked_book.return_value = tracked_book
                mock_tracked_class.return_value = mock_tracked_service

                # Mock download service to raise PVRProviderError
                mock_download_service = MagicMock()
                mock_download_service.initiate_download.side_effect = PVRProviderError(
                    "Download failed"
                )
                mock_download_class.return_value = mock_download_service

                with pytest.raises(HTTPException) as exc_info:
                    pvr_search_routes.trigger_download(
                        tracked_book_id=1,
                        request=request,
                        session=session,
                        current_user=user,
                        fastapi_request=mock_request,
                    )

                assert isinstance(exc_info.value, HTTPException)
                assert (
                    exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                assert "Download failed" in exc_info.value.detail
        finally:
            # Clean up cache
            with pvr_search_routes._cache_lock:
                pvr_search_routes._search_results_cache.pop(1, None)

    def test_trigger_download_generic_exception(
        self,
        session: DummySession,
        user: User,
        tracked_book: TrackedBook,
        indexer_search_result: IndexerSearchResult,
        mock_request: MagicMock,
    ) -> None:
        """Test trigger_download handles generic exceptions.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        user : User
            User fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        indexer_search_result : IndexerSearchResult
            Indexer search result fixture.
        mock_request : MagicMock
            Mocked request fixture.
        """
        request = PVRDownloadRequest(release_index=0)

        # Populate cache
        with pvr_search_routes._cache_lock:
            pvr_search_routes._search_results_cache[1] = [indexer_search_result]

        try:
            with (
                patch(
                    "bookcard.api.routes.pvr_search.PermissionService"
                ) as mock_perm_class,
                patch(
                    "bookcard.api.routes.pvr_search.TrackedBookService"
                ) as mock_tracked_class,
                patch(
                    "bookcard.api.routes.pvr_search.DownloadService"
                ) as mock_download_class,
            ):
                # Mock permission service
                mock_permission_service = MagicMock()
                mock_permission_service.check_permission.return_value = None
                mock_perm_class.return_value = mock_permission_service

                # Mock tracked book service
                mock_tracked_service = MagicMock()
                mock_tracked_service.get_tracked_book.return_value = tracked_book
                mock_tracked_class.return_value = mock_tracked_service

                # Mock download service to raise generic exception
                mock_download_service = MagicMock()
                mock_download_service.initiate_download.side_effect = RuntimeError(
                    "Unexpected error"
                )
                mock_download_class.return_value = mock_download_service

                with pytest.raises(HTTPException) as exc_info:
                    pvr_search_routes.trigger_download(
                        tracked_book_id=1,
                        request=request,
                        session=session,
                        current_user=user,
                        fastapi_request=mock_request,
                    )

                assert isinstance(exc_info.value, HTTPException)
                assert (
                    exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                assert "Download failed" in exc_info.value.detail
        finally:
            # Clean up cache
            with pvr_search_routes._cache_lock:
                pvr_search_routes._search_results_cache.pop(1, None)
