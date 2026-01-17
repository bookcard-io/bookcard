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

import contextlib
import json
import logging
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from bookcard.pvr.utils.status import DownloadStatus

logger = logging.getLogger(__name__)


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
    """Thread-safe download state management with persistence."""

    def __init__(self, state_file: Path | str | None = None) -> None:
        self._downloads: dict[str, DownloadState] = {}
        self._lock = threading.Lock()
        self._state_file = Path(state_file) if state_file else None
        self._last_load_time = 0.0

        # Load initial state
        self._load()

    def _load(self) -> None:
        """Load state from file."""
        if not self._state_file or not self._state_file.exists():
            return

        try:
            # Check modification time to avoid unnecessary reads
            mtime = self._state_file.stat().st_mtime
            if mtime <= self._last_load_time:
                return

            with self._lock:
                content = self._state_file.read_text(encoding="utf-8")
                if not content:
                    return

                data = json.loads(content)
                self._downloads.clear()
                for item in data:
                    self._downloads[item["id"]] = DownloadState(**item)

            self._last_load_time = mtime
        except Exception:
            logger.exception("Failed to load download state from %s", self._state_file)

    def _save(self) -> None:
        """Save state to file using atomic write."""
        if not self._state_file:
            return

        temp_path = None
        try:
            # Convert to dicts
            with self._lock:
                data = [asdict(d) for d in self._downloads.values()]

            # Ensure directory exists
            self._state_file.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write: write to temp file then rename
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=self._state_file.parent,
                delete=False,
                encoding="utf-8",
            ) as tf:
                json.dump(data, tf, indent=2)
                temp_path = Path(tf.name)

            temp_path.replace(self._state_file)

            # Update last load time so we don't reload our own changes immediately
            self._last_load_time = self._state_file.stat().st_mtime

        except Exception:
            logger.exception("Failed to save download state to %s", self._state_file)
            if temp_path and temp_path.exists():
                with contextlib.suppress(OSError):
                    temp_path.unlink()

    def create(
        self,
        download_id: str,
        url: str,
        title: str,
        path: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Create new download entry."""
        self._load()  # Refresh before adding
        with self._lock:
            self._downloads[download_id] = DownloadState(
                id=download_id,
                url=url,
                title=title,
                status=DownloadStatus.QUEUED,
                path=path,
                extra=extra,
            )
        self._save()

    def update_status(
        self, download_id: str, status: str, error: str | None = None
    ) -> None:
        """Update download status."""
        # Note: We don't load here because this is called by the worker thread
        # which owns this state update.
        with self._lock:
            if download_id in self._downloads:
                state = self._downloads[download_id]
                state.status = status
                if status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED):
                    state.completed_at = time.time()
                if error:
                    state.error = error
        self._save()

    def update_info(self, download_id: str, size_bytes: int, file_path: str) -> None:
        """Update download metadata."""
        with self._lock:
            if download_id in self._downloads:
                state = self._downloads[download_id]
                state.size_bytes = size_bytes
                state.path = file_path
        self._save()

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
        self._save()

    def get_all(self) -> list[DownloadState]:
        """Get all download states."""
        self._load()  # Refresh from disk to get updates from other processes
        with self._lock:
            # Return copies to avoid modification issues
            return [DownloadState(**asdict(d)) for d in self._downloads.values()]

    def remove(self, download_id: str) -> bool:
        """Remove download entry."""
        self._load()
        with self._lock:
            if download_id in self._downloads:
                del self._downloads[download_id]
                removed = True
            else:
                removed = False

        if removed:
            self._save()
        return removed

    def cleanup_old(self, retention_seconds: int) -> None:
        """Cleanup old completed/failed downloads."""
        self._load()
        now = time.time()
        modified = False
        with self._lock:
            to_remove = []
            for download_id, data in self._downloads.items():
                if data.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED):
                    completed_at = data.completed_at
                    if completed_at and (now - completed_at > retention_seconds):
                        to_remove.append(download_id)

            for download_id in to_remove:
                del self._downloads[download_id]
                modified = True

        if modified:
            self._save()
