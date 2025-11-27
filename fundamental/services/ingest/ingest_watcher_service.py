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

"""Ingest watcher service.

Watches the ingest directory for new files using watchfiles.
Follows SRP by focusing solely on file watching.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from watchfiles import Change, watch

from fundamental.models.tasks import TaskType
from fundamental.services.ingest.ingest_config_service import (
    IngestConfigService,  # noqa: TC001
)

if TYPE_CHECKING:
    from fundamental.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)


class IngestWatcherService:
    """Service for watching the ingest directory for new files.

    Uses watchfiles to monitor the directory and triggers discovery tasks
    when files are added or modified.

    Parameters
    ----------
    config_service : IngestConfigService
        Configuration service for ingest settings.
    task_runner : TaskRunner | None
        Optional task runner for enqueueing discovery tasks.
    debounce_seconds : float
        Debounce time in seconds to avoid rapid triggers (default: 5.0).
    """

    def __init__(
        self,
        config_service: IngestConfigService,
        task_runner: TaskRunner | None = None,  # type: ignore[name-defined]
        debounce_seconds: float = 5.0,
    ) -> None:
        """Initialize ingest watcher service.

        Parameters
        ----------
        config_service : IngestConfigService
            Configuration service.
        task_runner : TaskRunner | None
            Optional task runner.
        debounce_seconds : float
            Debounce time in seconds.
        """
        self._config_service = config_service
        self._task_runner = task_runner
        self._debounce_seconds = debounce_seconds
        self._watch_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_trigger_time = 0.0
        self._lock = threading.Lock()

    def start_watching(self) -> None:
        """Start watching the ingest directory.

        Starts a background thread that monitors the directory for changes.
        """
        if self._watch_thread is not None and self._watch_thread.is_alive():
            logger.warning("Watcher is already running")
            return

        if not self._task_runner:
            logger.warning("Task runner not available, cannot start watcher")
            return

        config = self._config_service.get_config()
        if not config.enabled:
            logger.info("Ingest service is disabled, not starting watcher")
            return

        ingest_dir = self._config_service.get_ingest_dir()
        if not ingest_dir.exists():
            logger.warning("Ingest directory does not exist: %s", ingest_dir)
            return

        self._stop_event.clear()
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(ingest_dir,),
            daemon=True,
            name="IngestWatcher",
        )
        self._watch_thread.start()
        logger.info("Started ingest watcher for directory: %s", ingest_dir)

    def stop_watching(self) -> None:
        """Stop watching the ingest directory.

        Gracefully stops the watcher thread.
        """
        if self._watch_thread is None:
            return

        logger.info("Stopping ingest watcher")
        self._stop_event.set()

        if self._watch_thread.is_alive():
            self._watch_thread.join(timeout=5.0)
            if self._watch_thread.is_alive():
                logger.warning("Watcher thread did not stop within timeout")

        self._watch_thread = None
        logger.info("Ingest watcher stopped")

    def _watch_loop(self, ingest_dir: Path) -> None:
        """Run main watch loop.

        Monitors the directory for changes and triggers discovery tasks.

        Parameters
        ----------
        ingest_dir : Path
            Directory to watch.
        """
        try:
            for changes in watch(
                str(ingest_dir),
                stop_event=self._stop_event,
                recursive=True,
            ):
                if self._stop_event.is_set():
                    break

                # Filter to only file additions and modifications
                relevant_changes = [
                    change
                    for change in changes
                    if change[0] in (Change.added, Change.modified)
                    and Path(change[1]).is_file()
                ]

                if relevant_changes and self._should_trigger():
                    self._trigger_discovery()

        except Exception:
            logger.exception("Error in watch loop")

    def _should_trigger(self) -> bool:
        """Check if discovery should be triggered (debounce).

        Returns
        -------
        bool
            True if should trigger, False otherwise.
        """
        with self._lock:
            now = time.time()
            time_since_last = now - self._last_trigger_time
            if time_since_last >= self._debounce_seconds:
                self._last_trigger_time = now
                return True
            return False

    def _trigger_discovery(self) -> None:
        """Trigger a discovery task.

        Enqueues an IngestDiscoveryTask via the task runner.
        """
        if not self._task_runner:
            logger.warning("Task runner not available, cannot trigger discovery")
            return

        try:
            # Get system user ID (0 or find system user)
            # For now, use 0 as system user
            system_user_id = 0

            task_id = self._task_runner.enqueue(
                task_type=TaskType.INGEST_DISCOVERY,
                payload={},
                user_id=system_user_id,
                metadata={"task_type": TaskType.INGEST_DISCOVERY.value},
            )

            logger.info("Triggered ingest discovery task: %d", task_id)
        except Exception:
            logger.exception("Failed to trigger discovery task")

    def trigger_manual_scan(self) -> int | None:
        """Manually trigger a discovery scan.

        Returns
        -------
        int | None
            Task ID if successful, None otherwise.
        """
        if not self._task_runner:
            logger.warning("Task runner not available")
            return None

        try:
            system_user_id = 0
            task_id = self._task_runner.enqueue(
                task_type=TaskType.INGEST_DISCOVERY,
                payload={},
                user_id=system_user_id,
                metadata={"task_type": TaskType.INGEST_DISCOVERY.value},
            )
            logger.info("Manually triggered ingest discovery task: %d", task_id)
        except Exception:
            logger.exception("Failed to trigger manual scan")
        else:
            return task_id
        return None
