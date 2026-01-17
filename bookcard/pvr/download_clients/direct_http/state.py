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

"""State management for Direct HTTP download client."""

import threading
import time
from dataclasses import dataclass
from typing import Any

from bookcard.pvr.utils.status import DownloadStatus


@dataclass
class DownloadState:
    """Represents the state of a download."""

    id: str
    url: str
    title: str
    status: str
    progress: float = 0.0
    size_bytes: int = 0
    downloaded_bytes: int = 0
    speed: float = 0.0
    path: str = ""
    error: str | None = None
    completed_at: float | None = None
    eta: int | None = None
    extra: dict[str, Any] | None = None


class DownloadStateManager:
    """Thread-safe download state management."""

    def __init__(self) -> None:
        self._downloads: dict[str, DownloadState] = {}
        self._lock = threading.Lock()

    def create(
        self,
        download_id: str,
        url: str,
        title: str,
        path: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Create new download entry."""
        with self._lock:
            self._downloads[download_id] = DownloadState(
                id=download_id,
                url=url,
                title=title,
                status=DownloadStatus.QUEUED,
                path=path,
                extra=extra,
            )

    def update_status(
        self, download_id: str, status: str, error: str | None = None
    ) -> None:
        """Update download status."""
        with self._lock:
            if download_id in self._downloads:
                state = self._downloads[download_id]
                state.status = status
                if status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED):
                    state.completed_at = time.time()
                if error:
                    state.error = error

    def update_info(self, download_id: str, size_bytes: int, file_path: str) -> None:
        """Update download metadata."""
        with self._lock:
            if download_id in self._downloads:
                state = self._downloads[download_id]
                state.size_bytes = size_bytes
                state.path = file_path

    def update_progress(
        self, download_id: str, downloaded: int, progress: float, speed: float
    ) -> None:
        """Update download progress."""
        with self._lock:
            if download_id in self._downloads:
                state = self._downloads[download_id]
                state.downloaded_bytes = downloaded
                state.progress = progress
                state.speed = speed

    def get_all(self) -> list[DownloadState]:
        """Get all download states."""
        with self._lock:
            # Return copies to avoid modification issues
            return [
                DownloadState(
                    id=d.id,
                    url=d.url,
                    title=d.title,
                    status=d.status,
                    progress=d.progress,
                    size_bytes=d.size_bytes,
                    downloaded_bytes=d.downloaded_bytes,
                    speed=d.speed,
                    path=d.path,
                    error=d.error,
                    completed_at=d.completed_at,
                    eta=d.eta,
                    extra=d.extra,
                )
                for d in self._downloads.values()
            ]

    def remove(self, download_id: str) -> bool:
        """Remove download entry."""
        with self._lock:
            if download_id in self._downloads:
                del self._downloads[download_id]
                return True
        return False

    def cleanup_old(self, retention_seconds: int) -> None:
        """Cleanup old completed/failed downloads."""
        now = time.time()
        with self._lock:
            to_remove = []
            for download_id, data in self._downloads.items():
                if data.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED):
                    completed_at = data.completed_at
                    if completed_at and (now - completed_at > retention_seconds):
                        to_remove.append(download_id)

            for download_id in to_remove:
                del self._downloads[download_id]
