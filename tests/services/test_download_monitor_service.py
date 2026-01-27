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

"""Unit tests for DownloadMonitorService."""

from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientStatus,
    DownloadClientType,
    DownloadItem,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.services.download_monitor_service import DownloadMonitorService


@pytest.fixture
def mock_session() -> MagicMock:
    """Mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def download_monitor_service(mock_session: MagicMock) -> DownloadMonitorService:
    """Create service instance."""
    return DownloadMonitorService(mock_session)


@pytest.fixture
def sample_client_def() -> DownloadClientDefinition:
    """Create sample download client definition."""
    return DownloadClientDefinition(
        id=1,
        name="Test Client",
        client_type=DownloadClientType.QBITTORRENT,
        host="localhost",
        enabled=True,
        status=DownloadClientStatus.HEALTHY,
    )


@pytest.fixture
def sample_download_item() -> DownloadItem:
    """Create sample download item."""
    return DownloadItem(
        id=100,
        tracked_book_id=1,
        download_client_id=1,
        client_item_id="hash123",
        title="Test Book",
        download_url="magnet:...",
        status=DownloadItemStatus.DOWNLOADING,
        progress=0.5,
    )


class TestDownloadMonitorService:
    """Test suite for DownloadMonitorService."""

    def test_update_download_item_completion_logic(
        self,
        download_monitor_service: DownloadMonitorService,
        mock_session: MagicMock,
        sample_download_item: DownloadItem,
    ) -> None:
        """Test that completion updates item but NOT tracked book."""
        # Setup
        tracked_book = TrackedBook(
            id=1,
            title="Test Book",
            author="Author",
            status=TrackedBookStatus.DOWNLOADING,
        )
        sample_download_item.tracked_book = tracked_book

        # Client data indicating completion
        client_item = {
            "client_item_id": "hash123",
            "status": "completed",
            "progress": 1.0,
            "file_path": "/downloads/completed/book",
        }

        # Execute
        download_monitor_service._update_item(sample_download_item, client_item)  # type: ignore[invalid-argument-type]

        # Verify DownloadItem updated
        assert sample_download_item.status == DownloadItemStatus.COMPLETED
        assert sample_download_item.progress == 1.0
        assert sample_download_item.completed_at is not None

        # Verify TrackedBook NOT updated (handled by import service now)
        assert tracked_book.status == TrackedBookStatus.DOWNLOADING
        assert tracked_book.last_downloaded_at is None

        # Session calls
        # Should add download item, but NOT tracked book explicitly for status change
        # (Though adding item might cascade, but logic check is what matters)
        # The code no longer does session.add(db_item.tracked_book)

        # We can verify by checking what was passed to session.add
        # It's tricky with mocks if same object ref, but we can check calls.

        # In the modified code:
        # self.session.add(db_item) is called.
        # self.session.add(db_item.tracked_book) is removed.

        # Let's check that we didn't accidentally update tracked book status in memory
        assert tracked_book.status == TrackedBookStatus.DOWNLOADING

    def test_update_download_item_failure_logic(
        self,
        download_monitor_service: DownloadMonitorService,
        mock_session: MagicMock,
        sample_download_item: DownloadItem,
    ) -> None:
        """Test that failure updates both item and tracked book."""
        # Setup
        tracked_book = TrackedBook(
            id=1,
            title="Test Book",
            author="Author",
            status=TrackedBookStatus.DOWNLOADING,
        )
        sample_download_item.tracked_book = tracked_book

        # Client data indicating failure
        client_item = {
            "client_item_id": "hash123",
            "status": "failed",
            "progress": 0.1,
        }

        # Execute
        download_monitor_service._update_item(sample_download_item, client_item)  # type: ignore[invalid-argument-type]

        # Verify DownloadItem updated
        assert sample_download_item.status == DownloadItemStatus.FAILED
        assert (
            sample_download_item.error_message == "Download failed reported by client"
        )

        # Verify TrackedBook IS updated for failure (we still want to know if download failed)
        assert tracked_book.status == TrackedBookStatus.FAILED
        assert tracked_book.error_message == "Download failed reported by client"

        # Verify session calls
        mock_session.add.assert_any_call(tracked_book)
        mock_session.add.assert_any_call(sample_download_item)
