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

from sqlmodel import Session, select
from watchfiles import Change, watch

from bookcard.database import get_session
from bookcard.models.auth import User
from bookcard.models.tasks import TaskType
from bookcard.services.ingest.ingest_config_service import IngestConfigService

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from bookcard.services.tasks.base import TaskRunner

logger = logging.getLogger(__name__)


class IngestWatcherService:
    """Service for watching the ingest directory for new files.

    Uses watchfiles to monitor the directory and triggers discovery tasks
    when files are added or modified.

    Parameters
    ----------
    engine : Engine
        Database engine for creating sessions on demand.
    task_runner : TaskRunner | None
        Optional task runner for enqueueing discovery tasks.
    debounce_seconds : float
        Debounce time in seconds to avoid rapid triggers (default: 5.0).
    """

    def __init__(
        self,
        engine: Engine,
        task_runner: TaskRunner | None = None,
        debounce_seconds: float = 5.0,
    ) -> None:
        """Initialize ingest watcher service.

        Parameters
        ----------
        engine : Engine
            Database engine for creating sessions.
        task_runner : TaskRunner | None
            Optional task runner.
        debounce_seconds : float
            Debounce time in seconds.
        """
        self._engine = engine
        self._task_runner = task_runner
        self._debounce_seconds = debounce_seconds
        self._watch_thread: threading.Thread | None = None
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_trigger_time = 0.0
        self._last_scan_files: set[Path] = set()
        self._lock = threading.Lock()
        self._restart_lock = threading.Lock()

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

        # Create a fresh session to check config
        with get_session(self._engine) as session:
            config_service = IngestConfigService(session)
            config = config_service.get_config()

            if not config.enabled:
                logger.info("Ingest service is disabled, not starting watcher")
                return

            ingest_dir = config_service.get_ingest_dir()
            if not ingest_dir.exists():
                logger.warning("Ingest directory does not exist: %s", ingest_dir)
                return

        self._stop_event.clear()

        # Start watch thread (for inotify-based watching)
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(ingest_dir,),
            daemon=True,
            name="IngestWatcher",
        )
        self._watch_thread.start()

        # Start polling thread as fallback (for network mounts)
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            args=(ingest_dir,),
            daemon=True,
            name="IngestWatcherPoll",
        )
        self._poll_thread.start()

        logger.info("Started ingest watcher for directory: %s", ingest_dir)

        # Trigger initial scan for existing files (bypass debounce)
        logger.info("Triggering initial scan for existing files in ingest directory")
        self._trigger_discovery(bypass_debounce=True)

    def stop_watching(self) -> None:
        """Stop watching the ingest directory.

        Gracefully stops the watcher threads.
        Thread-safe: can be called multiple times safely.
        """
        with self._lock:
            # Check if already stopped
            if self._watch_thread is None and self._poll_thread is None:
                return

            logger.info("Stopping ingest watcher")
            self._stop_event.set()

            # Capture thread references while holding lock
            watch_thread = self._watch_thread
            poll_thread = self._poll_thread

        # Join threads outside the lock to avoid deadlock
        if watch_thread is not None and watch_thread.is_alive():
            watch_thread.join(timeout=5.0)
            if watch_thread.is_alive():
                logger.warning("Watcher thread did not stop within timeout")

        if poll_thread is not None and poll_thread.is_alive():
            poll_thread.join(timeout=5.0)
            if poll_thread.is_alive():
                logger.warning("Poll thread did not stop within timeout")

        # Clear thread references while holding lock
        with self._lock:
            self._watch_thread = None
            self._poll_thread = None

        logger.info("Ingest watcher stopped")

    def restart_watching(self) -> None:
        """Restart watching with current configuration.

        Stops the current watcher, re-reads configuration, and starts
        watching again. Useful when configuration changes (e.g., watch
        directory or enabled flag).

        This method is safe to call even if the watcher is not running.
        Uses a lock to prevent concurrent restarts.
        """
        # Use restart lock to prevent concurrent restarts
        if not self._restart_lock.acquire(blocking=False):
            logger.debug("Restart already in progress, skipping duplicate restart")
            return

        try:
            logger.info("Restarting ingest watcher")
            # Stop current watcher if running
            self.stop_watching()
            # Wait a brief moment to ensure threads are fully stopped
            time.sleep(0.5)
            # Start watching again (will read fresh config)
            self.start_watching()
        finally:
            self._restart_lock.release()

    def _watch_loop(self, ingest_dir: Path) -> None:
        """Run main watch loop.

        Monitors the directory for changes and triggers discovery tasks.
        Uses polling mode for network mounts that don't support inotify.

        Parameters
        ----------
        ingest_dir : Path
            Directory to watch.
        """
        logger.info("Watch loop started for directory: %s", ingest_dir)

        # Note: watchfiles uses inotify which doesn't work on network mounts (NFS/SMB)
        # We have a polling fallback thread that will handle network mounts
        # To force polling in watchfiles, set WATCHFILES_FORCE_POLLING=true environment variable

        try:
            for changes in watch(
                str(ingest_dir),
                stop_event=self._stop_event,
                recursive=True,
            ):
                if self._stop_event.is_set():
                    logger.info("Stop event set, exiting watch loop")
                    break

                logger.debug("Watch detected %d change(s)", len(changes))

                # Filter to only file additions and modifications
                relevant_changes = [
                    change
                    for change in changes
                    if change[0] in (Change.added, Change.modified)
                    and Path(change[1]).is_file()
                ]

                if relevant_changes:
                    logger.info(
                        "Detected %d relevant file change(s): %s",
                        len(relevant_changes),
                        [Path(change[1]).name for change in relevant_changes],
                    )
                    self._trigger_discovery()
                elif changes:
                    logger.debug(
                        "Ignored %d change(s) (not file additions/modifications)",
                        len(changes),
                    )

        except Exception:
            logger.exception("Error in watch loop")

    def _poll_loop(self, ingest_dir: Path) -> None:
        """Run polling loop as fallback for network mounts.

        Periodically scans the directory for new files since inotify
        doesn't work on network filesystems (NFS/SMB).

        Parameters
        ----------
        ingest_dir : Path
            Directory to poll.
        """
        logger.info(
            "Poll loop started for directory: %s (polling every 30s)", ingest_dir
        )
        poll_interval = 30.0  # Poll every 30 seconds

        try:
            while not self._stop_event.is_set():
                # Wait for poll interval or stop event
                if self._stop_event.wait(timeout=poll_interval):
                    break

                if not ingest_dir.exists():
                    logger.debug("Ingest directory does not exist, skipping poll")
                    continue

                # Get current files in directory
                try:
                    current_files = {f for f in ingest_dir.iterdir() if f.is_file()}

                    # Check for new files
                    new_files = current_files - self._last_scan_files
                    if new_files:
                        logger.info(
                            "Poll detected %d new file(s): %s",
                            len(new_files),
                            [f.name for f in new_files],
                        )
                        self._trigger_discovery()

                    self._last_scan_files = current_files
                except Exception:
                    logger.exception("Error during poll scan")

        except Exception:
            logger.exception("Error in poll loop")

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

    @staticmethod
    def _get_system_user_id(session: Session) -> int | None:
        """Get system user ID for system tasks.

        Returns first admin user ID, or first user ID if no admin exists.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        int | None
            System user ID, or None if no users exist.
        """
        stmt = select(User).where(User.is_admin == True).limit(1)  # noqa: E712
        system_user = session.exec(stmt).first()
        if system_user is None:
            # Fallback to first user if no admin exists
            stmt = select(User).limit(1)
            system_user = session.exec(stmt).first()

        if system_user is None or system_user.id is None:
            logger.error("No user found for system tasks")
            return None

        return system_user.id

    def _trigger_discovery(self, bypass_debounce: bool = False) -> None:
        """Trigger a discovery task.

        Enqueues an IngestDiscoveryTask via the task runner.

        Parameters
        ----------
        bypass_debounce : bool
            If True, bypass debounce check (for initial scans).
        """
        if not self._task_runner:
            logger.warning("Task runner not available, cannot trigger discovery")
            return

        # Check debounce unless bypassed
        if not bypass_debounce and not self._should_trigger():
            logger.debug("Discovery trigger skipped due to debounce")
            return

        try:
            # Get system user ID for the task
            with get_session(self._engine) as session:
                system_user_id = self._get_system_user_id(session)
                if system_user_id is None:
                    logger.error("Cannot trigger discovery task: no system user found")
                    return

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

        task_id: int | None = None
        try:
            # Get system user ID for the task
            with get_session(self._engine) as session:
                system_user_id = self._get_system_user_id(session)
                if system_user_id is None:
                    logger.error("Cannot trigger manual scan: no system user found")
                    return None

            task_id = self._task_runner.enqueue(
                task_type=TaskType.INGEST_DISCOVERY,
                payload={},
                user_id=system_user_id,
                metadata={"task_type": TaskType.INGEST_DISCOVERY.value},
            )
            logger.info("Manually triggered ingest discovery task: %d", task_id)
        except Exception:
            logger.exception("Failed to trigger manual scan")
            return None
        else:
            return task_id
