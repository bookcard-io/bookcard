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

"""Tests for Direct HTTP state management module."""

import time

from bookcard.pvr.download_clients.direct_http.state import (
    DownloadState,
    DownloadStateManager,
)
from bookcard.pvr.utils.status import DownloadStatus


class TestDownloadState:
    """Test DownloadState dataclass."""

    def test_init(self) -> None:
        """Test initialization."""
        state = DownloadState(
            id="test-id",
            url="https://example.com",
            title="Test Download",
            status=DownloadStatus.QUEUED,
        )
        assert state.id == "test-id"
        assert state.url == "https://example.com"
        assert state.title == "Test Download"
        assert state.status == DownloadStatus.QUEUED
        assert state.progress == 0.0
        assert state.size_bytes == 0
        assert state.downloaded_bytes == 0
        assert state.speed == 0.0
        assert state.path == ""
        assert state.error is None
        assert state.completed_at is None
        assert state.eta is None

    def test_init_with_all_fields(self) -> None:
        """Test initialization with all fields."""
        state = DownloadState(
            id="test-id",
            url="https://example.com",
            title="Test Download",
            status=DownloadStatus.DOWNLOADING,
            progress=0.5,
            size_bytes=1000,
            downloaded_bytes=500,
            speed=100.0,
            path="/path/to/file",
            error="No error",
            completed_at=1000.0,
            eta=5,
        )
        assert state.progress == 0.5
        assert state.size_bytes == 1000
        assert state.downloaded_bytes == 500
        assert state.speed == 100.0
        assert state.path == "/path/to/file"
        assert state.error == "No error"
        assert state.completed_at == 1000.0
        assert state.eta == 5


class TestDownloadStateManager:
    """Test DownloadStateManager class."""

    def test_init(self) -> None:
        """Test initialization."""
        manager = DownloadStateManager()
        assert manager._downloads == {}
        assert manager._lock is not None

    def test_create(self) -> None:
        """Test creating a download state."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        assert "test-id" in manager._downloads
        state = manager._downloads["test-id"]
        assert state.id == "test-id"
        assert state.url == "https://example.com"
        assert state.title == "Test"
        assert state.path == "/path"
        assert state.status == DownloadStatus.QUEUED

    def test_update_status(self) -> None:
        """Test updating download status."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        manager.update_status("test-id", DownloadStatus.DOWNLOADING)
        state = manager._downloads["test-id"]
        assert state.status == DownloadStatus.DOWNLOADING

    def test_update_status_with_error(self) -> None:
        """Test updating status with error message."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        manager.update_status("test-id", DownloadStatus.FAILED, "Connection error")
        state = manager._downloads["test-id"]
        assert state.status == DownloadStatus.FAILED
        assert state.error == "Connection error"

    def test_update_status_sets_completed_at(self) -> None:
        """Test that completed_at is set for completed/failed status."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        manager.update_status("test-id", DownloadStatus.COMPLETED)
        state = manager._downloads["test-id"]
        assert state.completed_at is not None
        assert isinstance(state.completed_at, float)

    def test_update_status_sets_completed_at_for_failed(self) -> None:
        """Test that completed_at is set for failed status."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        manager.update_status("test-id", DownloadStatus.FAILED)
        state = manager._downloads["test-id"]
        assert state.completed_at is not None

    def test_update_status_does_not_set_completed_at_for_other_statuses(
        self,
    ) -> None:
        """Test that completed_at is not set for non-terminal statuses."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        manager.update_status("test-id", DownloadStatus.DOWNLOADING)
        state = manager._downloads["test-id"]
        assert state.completed_at is None

    def test_update_info(self) -> None:
        """Test updating download info."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        manager.update_info("test-id", 1000, "/new/path")
        state = manager._downloads["test-id"]
        assert state.size_bytes == 1000
        assert state.path == "/new/path"

    def test_update_progress(self) -> None:
        """Test updating download progress."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        manager.update_progress("test-id", 500, 0.5, 100.0)
        state = manager._downloads["test-id"]
        assert state.downloaded_bytes == 500
        assert state.progress == 0.5
        assert state.speed == 100.0

    def test_get_all(self) -> None:
        """Test getting all download states."""
        manager = DownloadStateManager()
        manager.create("id1", "https://example.com/1", "Test 1", "/path1")
        manager.create("id2", "https://example.com/2", "Test 2", "/path2")
        states = manager.get_all()
        assert len(states) == 2
        assert all(isinstance(s, DownloadState) for s in states)
        ids = {s.id for s in states}
        assert ids == {"id1", "id2"}

    def test_get_all_returns_copies(self) -> None:
        """Test that get_all returns copies, not references."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        states1 = manager.get_all()
        states2 = manager.get_all()
        assert states1[0] is not states2[0]

    def test_remove(self) -> None:
        """Test removing a download state."""
        manager = DownloadStateManager()
        manager.create("test-id", "https://example.com", "Test", "/path")
        result = manager.remove("test-id")
        assert result is True
        assert "test-id" not in manager._downloads

    def test_remove_nonexistent(self) -> None:
        """Test removing a non-existent download state."""
        manager = DownloadStateManager()
        result = manager.remove("nonexistent")
        assert result is False

    def test_cleanup_old(self) -> None:
        """Test cleaning up old completed downloads."""
        manager = DownloadStateManager()
        manager.create("completed-id", "https://example.com", "Test", "/path")
        manager.update_status("completed-id", DownloadStatus.COMPLETED)
        # Set completed_at to past
        state = manager._downloads["completed-id"]
        state.completed_at = time.time() - 100000  # Old enough
        manager.cleanup_old(86400)  # 24 hours retention
        assert "completed-id" not in manager._downloads

    def test_cleanup_old_keeps_recent(self) -> None:
        """Test that recent completed downloads are kept."""
        manager = DownloadStateManager()
        manager.create("recent-id", "https://example.com", "Test", "/path")
        manager.update_status("recent-id", DownloadStatus.COMPLETED)
        # completed_at is set to current time by update_status
        manager.cleanup_old(86400)  # 24 hours retention
        assert "recent-id" in manager._downloads

    def test_cleanup_old_keeps_active(self) -> None:
        """Test that active downloads are not cleaned up."""
        manager = DownloadStateManager()
        manager.create("active-id", "https://example.com", "Test", "/path")
        manager.update_status("active-id", DownloadStatus.DOWNLOADING)
        manager.cleanup_old(86400)
        assert "active-id" in manager._downloads

    def test_cleanup_old_removes_failed(self) -> None:
        """Test that old failed downloads are removed."""
        manager = DownloadStateManager()
        manager.create("failed-id", "https://example.com", "Test", "/path")
        manager.update_status("failed-id", DownloadStatus.FAILED)
        state = manager._downloads["failed-id"]
        state.completed_at = time.time() - 100000
        manager.cleanup_old(86400)
        assert "failed-id" not in manager._downloads

    def test_thread_safety(self) -> None:
        """Test thread safety of operations."""
        import threading

        manager = DownloadStateManager()
        results = []

        def worker(worker_id: int) -> None:
            for i in range(10):
                download_id = f"id-{worker_id}-{i}"
                manager.create(download_id, "https://example.com", "Test", "/path")
                manager.update_status(download_id, DownloadStatus.DOWNLOADING)
                manager.update_progress(download_id, i * 100, i * 0.1, 10.0)
                results.append(download_id)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(manager.get_all()) == 50
        assert len(results) == 50
