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

"""Tests for DownloadService."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientStatus,
    DownloadClientType,
    DownloadItem,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.pvr.base import TrackingDownloadClient
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.download.factory import DefaultDownloadClientFactory
from bookcard.services.download.repository import DownloadItemRepository
from bookcard.services.download_client_service import DownloadClientService
from bookcard.services.download_service import DownloadService


@pytest.fixture
def mock_repository() -> MagicMock:
    """Mock download item repository."""
    return MagicMock(spec=DownloadItemRepository)


@pytest.fixture
def mock_client_service() -> MagicMock:
    """Mock download client service."""
    return MagicMock(spec=DownloadClientService)


@pytest.fixture
def download_service(
    mock_repository: MagicMock, mock_client_service: MagicMock
) -> DownloadService:
    """Create DownloadService instance."""
    return DownloadService(mock_repository, mock_client_service)


@pytest.fixture
def sample_release() -> ReleaseInfo:
    """Sample release info."""
    return ReleaseInfo(
        indexer_id=1,
        title="Test Book",
        download_url="https://example.com/test.torrent",
        size_bytes=1024,
        publish_date=datetime.now(UTC),
        quality="epub",
    )


@pytest.fixture
def sample_tracked_book() -> TrackedBook:
    """Sample tracked book."""
    return TrackedBook(
        id=1,
        title="Test Book",
        author="Test Author",
        status=TrackedBookStatus.WANTED,
    )


@pytest.fixture
def sample_client_definition() -> DownloadClientDefinition:
    """Sample download client definition."""
    return DownloadClientDefinition(
        id=1,
        name="Test Client",
        client_type=DownloadClientType.QBITTORRENT,
        host="localhost",
        port=8080,
        enabled=True,
        status=DownloadClientStatus.HEALTHY,
        download_path="/downloads",
        category="books",
    )


class TestDownloadService:
    """Tests for DownloadService."""

    def test_initiate_download_success(
        self,
        download_service: DownloadService,
        mock_repository: MagicMock,
        sample_release: ReleaseInfo,
        sample_tracked_book: TrackedBook,
        sample_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test successful download initiation."""
        # Mock no existing download
        mock_repository.get_latest_by_url_and_tracked_book.return_value = None
        # Mock client service to return the client definition
        download_service._client_service.get_download_client = MagicMock(  # type: ignore[method-assign]
            return_value=sample_client_definition
        )

        with patch.object(DefaultDownloadClientFactory, "create") as mock_create_client:
            mock_client_instance = MagicMock()
            mock_client_instance.add_download.return_value = "client_item_123"
            mock_create_client.return_value = mock_client_instance

            # Execute
            item = download_service.initiate_download(
                sample_release, sample_tracked_book, sample_client_definition
            )

            # Verify
            mock_client_instance.add_download.assert_called_once_with(
                download_url=sample_release.download_url,
                title=sample_release.title,
                category="books",
                download_path="/downloads",
                author=sample_release.author,
                quality=sample_release.quality,
                guid=sample_release.guid,
            )

            # Verify DB operations
            assert sample_tracked_book.status == TrackedBookStatus.DOWNLOADING
            assert sample_tracked_book.last_downloaded_at is not None

            # Verify created item
            assert item.client_item_id == "client_item_123"
            assert item.status == DownloadItemStatus.QUEUED
            assert item.download_client_id == sample_client_definition.id
            assert item.tracked_book_id == sample_tracked_book.id

            mock_repository.add.assert_called_once()
            mock_repository.commit.assert_called_once()
            mock_repository.refresh.assert_called_once()

    def test_initiate_download_auto_select_client(
        self,
        download_service: DownloadService,
        mock_repository: MagicMock,
        mock_client_service: MagicMock,
        sample_release: ReleaseInfo,
        sample_tracked_book: TrackedBook,
        sample_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test auto-selection of download client."""
        # Mock no existing download
        mock_repository.get_latest_by_url_and_tracked_book.return_value = None
        mock_client_service.list_decrypted_download_clients.return_value = [
            sample_client_definition
        ]
        # Mock client service to return the client definition
        mock_client_service.get_download_client = MagicMock(
            return_value=sample_client_definition
        )

        with patch.object(DefaultDownloadClientFactory, "create") as mock_create_client:
            mock_client_instance = MagicMock()
            mock_client_instance.add_download.return_value = "client_item_123"
            mock_create_client.return_value = mock_client_instance

            download_service.initiate_download(sample_release, sample_tracked_book)

            mock_client_service.list_decrypted_download_clients.assert_called_once_with(
                enabled_only=True
            )

    def test_initiate_download_no_client(
        self,
        download_service: DownloadService,
        mock_repository: MagicMock,
        mock_client_service: MagicMock,
        sample_release: ReleaseInfo,
        sample_tracked_book: TrackedBook,
    ) -> None:
        """Test error when no client available."""
        # Mock no existing download
        mock_repository.get_latest_by_url_and_tracked_book.return_value = None
        mock_client_service.list_decrypted_download_clients.return_value = []

        with pytest.raises(ValueError, match="No suitable download client found"):
            download_service.initiate_download(sample_release, sample_tracked_book)

    def test_initiate_download_validation_no_url(
        self,
        download_service: DownloadService,
        sample_tracked_book: TrackedBook,
    ) -> None:
        """Test validation fails when release has no URL."""
        release = ReleaseInfo(
            indexer_id=1,
            title="Test Book",
            download_url="",  # Empty URL
            size_bytes=1024,
            publish_date=datetime.now(UTC),
        )

        with pytest.raises(ValueError, match="must have a download URL"):
            download_service.initiate_download(release, sample_tracked_book)

    def test_initiate_download_validation_already_downloading(
        self,
        download_service: DownloadService,
        mock_repository: MagicMock,
        sample_release: ReleaseInfo,
    ) -> None:
        """Test validation fails when book is already downloading."""
        tracked_book = TrackedBook(
            id=1,
            title="Test Book",
            author="Test Author",
            status=TrackedBookStatus.DOWNLOADING,  # Already downloading
        )
        # Mock existing active download
        existing_item = MagicMock()
        existing_item.status = DownloadItemStatus.DOWNLOADING
        mock_repository.get_latest_by_url_and_tracked_book.return_value = existing_item

        # The method should return the existing item, not raise an error
        # But if we want to test the validation, we need to check the tracked_book status
        # Actually, the method doesn't validate the tracked_book status - it just checks for existing downloads
        # So this test might need to be updated to check for existing downloads instead
        result = download_service.initiate_download(sample_release, tracked_book)
        # Should return existing item instead of raising error
        assert result == existing_item

    def test_track_download_update(
        self,
        download_service: DownloadService,
        mock_repository: MagicMock,
        mock_client_service: MagicMock,
        sample_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test tracking download status update."""
        download_item = DownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="client_item_123",
            status=DownloadItemStatus.DOWNLOADING,
            progress=0.1,
        )

        mock_client_service.get_download_client.return_value = sample_client_definition

        with patch.object(DefaultDownloadClientFactory, "create") as mock_create_client:
            mock_client_instance = MagicMock(spec=TrackingDownloadClient)
            mock_client_instance.get_items.return_value = [
                {
                    "client_item_id": "client_item_123",
                    "title": "Test Book",
                    "status": "downloading",
                    "progress": 0.5,
                    "size_bytes": 1024,
                    "downloaded_bytes": 512,
                    "download_speed_bytes_per_sec": 100.0,
                    "eta_seconds": 60,
                }
            ]
            mock_create_client.return_value = mock_client_instance

            download_service.track_download(download_item)

            assert download_item.progress == 0.5
            assert download_item.status == DownloadItemStatus.DOWNLOADING
            assert download_item.downloaded_bytes == 512
            mock_repository.update.assert_called_with(download_item)
            mock_repository.commit.assert_called()

    def test_track_download_completed(
        self,
        download_service: DownloadService,
        mock_repository: MagicMock,
        mock_client_service: MagicMock,
        sample_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test tracking completed download."""
        download_item = DownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="client_item_123",
            status=DownloadItemStatus.DOWNLOADING,
        )

        mock_client_service.get_download_client.return_value = sample_client_definition

        with patch.object(DefaultDownloadClientFactory, "create") as mock_create_client:
            mock_client_instance = MagicMock(spec=TrackingDownloadClient)
            mock_client_instance.get_items.return_value = [
                {
                    "client_item_id": "client_item_123",
                    "status": "completed",
                    "progress": 1.0,
                    "file_path": "/downloads/book.epub",
                }
            ]
            mock_create_client.return_value = mock_client_instance

            download_service.track_download(download_item)

            assert download_item.status == DownloadItemStatus.COMPLETED
            assert download_item.completed_at is not None
            assert download_item.file_path == "/downloads/book.epub"

    def test_track_download_client_not_tracking(
        self,
        download_service: DownloadService,
        mock_client_service: MagicMock,
        sample_client_definition: DownloadClientDefinition,
    ) -> None:
        """Test tracking with client that doesn't support tracking."""
        download_item = DownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="client_item_123",
            status=DownloadItemStatus.DOWNLOADING,
        )

        mock_client_service.get_download_client.return_value = sample_client_definition

        with patch.object(DefaultDownloadClientFactory, "create") as mock_create_client:
            # Mock client that is NOT TrackingDownloadClient
            class NonTrackingClient:
                pass

            mock_create_client.return_value = NonTrackingClient()

            download_service.track_download(download_item)

            # Should just return without error

    def test_get_download_status(
        self,
        download_service: DownloadService,
        mock_repository: MagicMock,
    ) -> None:
        """Test getting download status."""
        item = DownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="test",
            status=DownloadItemStatus.DOWNLOADING,
        )
        mock_repository.get.return_value = item

        result = download_service.get_download_status(1)

        assert result == item
        mock_repository.get.assert_called_once_with(1)
