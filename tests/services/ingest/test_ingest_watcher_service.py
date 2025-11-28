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

"""Tests for ingest watcher service to achieve 100% coverage."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

from fundamental.models.ingest import IngestConfig
from fundamental.models.tasks import TaskType
from fundamental.services.ingest.ingest_config_service import IngestConfigService
from fundamental.services.ingest.ingest_watcher_service import IngestWatcherService


@pytest.fixture
def mock_engine() -> MagicMock:
    """Create a mock database engine."""
    return MagicMock()


@pytest.fixture
def mock_task_runner() -> MagicMock:
    """Create a mock TaskRunner."""
    runner = MagicMock()
    runner.enqueue.return_value = 123
    return runner


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock IngestConfig."""
    config = MagicMock(spec=IngestConfig)
    config.enabled = True
    config.ingest_dir = "/tmp/ingest"
    return config


@pytest.fixture
def mock_config_service(mock_config: MagicMock) -> MagicMock:
    """Create a mock IngestConfigService."""
    service = MagicMock(spec=IngestConfigService)
    service.get_config.return_value = mock_config
    service.get_ingest_dir.return_value = Path("/tmp/ingest")
    return service


@pytest.fixture
def temp_ingest_dir(tmp_path: Path) -> Path:
    """Create a temporary ingest directory."""
    ingest_dir = tmp_path / "ingest"
    ingest_dir.mkdir()
    return ingest_dir


@pytest.fixture
def service(
    mock_engine: MagicMock,
    mock_task_runner: MagicMock,
) -> IngestWatcherService:
    """Create IngestWatcherService with mocked dependencies."""
    return IngestWatcherService(
        engine=mock_engine,
        task_runner=mock_task_runner,
        debounce_seconds=0.1,
    )


@pytest.fixture
def service_no_runner(mock_engine: MagicMock) -> IngestWatcherService:
    """Create IngestWatcherService without task runner."""
    return IngestWatcherService(engine=mock_engine, task_runner=None)


class TestInit:
    """Test IngestWatcherService initialization."""

    def test_init_with_all_params(
        self,
        mock_engine: MagicMock,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test initialization with all parameters."""
        service = IngestWatcherService(
            engine=mock_engine,
            task_runner=mock_task_runner,
            debounce_seconds=10.0,
        )
        assert service._engine == mock_engine
        assert service._task_runner == mock_task_runner
        assert service._debounce_seconds == 10.0
        assert service._watch_thread is None
        assert service._poll_thread is None
        assert not service._stop_event.is_set()
        assert service._last_trigger_time == 0.0
        assert service._last_scan_files == set()

    def test_init_default_debounce(
        self,
        mock_engine: MagicMock,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test initialization with default debounce."""
        service = IngestWatcherService(
            engine=mock_engine,
            task_runner=mock_task_runner,
        )
        assert service._debounce_seconds == 5.0


class TestStartWatching:
    """Test start_watching method."""

    def test_start_watching_success(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
        mock_engine: MagicMock,
        mock_config_service: MagicMock,
    ) -> None:
        """Test successful watcher start."""
        mock_config = MagicMock(spec=IngestConfig)
        mock_config.enabled = True
        mock_config_service.get_config.return_value = mock_config
        mock_config_service.get_ingest_dir.return_value = temp_ingest_dir

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.ingest.ingest_watcher_service.IngestConfigService"
            ) as mock_config_class,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_class.return_value = mock_config_service

            service.start_watching()

            assert service._watch_thread is not None
            assert service._watch_thread.is_alive()
            assert service._poll_thread is not None
            assert service._poll_thread.is_alive()

            # Cleanup
            service.stop_watching()

    def test_start_watching_already_running(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
        mock_engine: MagicMock,
        mock_config_service: MagicMock,
    ) -> None:
        """Test starting watcher when already running."""
        mock_config = MagicMock(spec=IngestConfig)
        mock_config.enabled = True
        mock_config_service.get_config.return_value = mock_config
        mock_config_service.get_ingest_dir.return_value = temp_ingest_dir

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.ingest.ingest_watcher_service.IngestConfigService"
            ) as mock_config_class,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_class.return_value = mock_config_service

            service.start_watching()
            # Try to start again
            service.start_watching()

            # Cleanup
            service.stop_watching()

    def test_start_watching_no_task_runner(
        self,
        service_no_runner: IngestWatcherService,
    ) -> None:
        """Test starting watcher without task runner."""
        service_no_runner.start_watching()

        assert service_no_runner._watch_thread is None
        assert service_no_runner._poll_thread is None

    def test_start_watching_disabled(
        self,
        service: IngestWatcherService,
        mock_engine: MagicMock,
        mock_config_service: MagicMock,
    ) -> None:
        """Test starting watcher when service is disabled."""
        mock_config = MagicMock(spec=IngestConfig)
        mock_config.enabled = False
        mock_config_service.get_config.return_value = mock_config

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.ingest.ingest_watcher_service.IngestConfigService"
            ) as mock_config_class,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_class.return_value = mock_config_service

            service.start_watching()

            assert service._watch_thread is None
            assert service._poll_thread is None

    def test_start_watching_dir_not_exists(
        self,
        service: IngestWatcherService,
        mock_engine: MagicMock,
        mock_config_service: MagicMock,
    ) -> None:
        """Test starting watcher when directory doesn't exist."""
        mock_config = MagicMock(spec=IngestConfig)
        mock_config.enabled = True
        mock_config_service.get_config.return_value = mock_config
        mock_config_service.get_ingest_dir.return_value = Path("/nonexistent/dir")

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.ingest.ingest_watcher_service.IngestConfigService"
            ) as mock_config_class,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_class.return_value = mock_config_service

            service.start_watching()

            assert service._watch_thread is None
            assert service._poll_thread is None


class TestStopWatching:
    """Test stop_watching method."""

    def test_stop_watching_success(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
        mock_engine: MagicMock,
        mock_config_service: MagicMock,
    ) -> None:
        """Test successful watcher stop."""
        mock_config = MagicMock(spec=IngestConfig)
        mock_config.enabled = True
        mock_config_service.get_config.return_value = mock_config
        mock_config_service.get_ingest_dir.return_value = temp_ingest_dir

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.ingest.ingest_watcher_service.IngestConfigService"
            ) as mock_config_class,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_class.return_value = mock_config_service

            service.start_watching()
            time.sleep(0.1)  # Give threads time to start
            service.stop_watching()

            assert service._watch_thread is None
            assert service._poll_thread is None
            assert service._stop_event.is_set()

    def test_stop_watching_not_running(
        self,
        service: IngestWatcherService,
    ) -> None:
        """Test stopping watcher when not running."""
        service.stop_watching()

        assert service._watch_thread is None
        assert service._poll_thread is None

    def test_stop_watching_multiple_calls(
        self,
        service: IngestWatcherService,
    ) -> None:
        """Test stopping watcher multiple times."""
        service.stop_watching()
        service.stop_watching()  # Should be safe to call multiple times

        assert service._watch_thread is None
        assert service._poll_thread is None


class TestRestartWatching:
    """Test restart_watching method."""

    def test_restart_watching_success(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
        mock_engine: MagicMock,
        mock_config_service: MagicMock,
    ) -> None:
        """Test successful watcher restart."""
        mock_config = MagicMock(spec=IngestConfig)
        mock_config.enabled = True
        mock_config_service.get_config.return_value = mock_config
        mock_config_service.get_ingest_dir.return_value = temp_ingest_dir

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.ingest.ingest_watcher_service.IngestConfigService"
            ) as mock_config_class,
            patch("time.sleep") as mock_sleep,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_class.return_value = mock_config_service

            service.restart_watching()

            mock_sleep.assert_called_once_with(0.5)
            # Cleanup
            service.stop_watching()

    def test_restart_watching_concurrent(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
        mock_engine: MagicMock,
        mock_config_service: MagicMock,
    ) -> None:
        """Test concurrent restart attempts."""
        mock_config = MagicMock(spec=IngestConfig)
        mock_config.enabled = True
        mock_config_service.get_config.return_value = mock_config
        mock_config_service.get_ingest_dir.return_value = temp_ingest_dir

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.get_session"
            ) as mock_get_session,
            patch(
                "fundamental.services.ingest.ingest_watcher_service.IngestConfigService"
            ) as mock_config_class,
            patch("time.sleep"),
        ):
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_config_class.return_value = mock_config_service

            # Simulate concurrent restart
            if not service._restart_lock.acquire(blocking=False):
                # Lock already held, should skip
                pass

            service.restart_watching()

            # Cleanup
            service.stop_watching()


class TestWatchLoop:
    """Test _watch_loop method."""

    def test_watch_loop_stop_event(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
    ) -> None:
        """Test watch loop stops on stop event."""
        service._stop_event.set()

        with patch(
            "fundamental.services.ingest.ingest_watcher_service.watch"
        ) as mock_watch:
            mock_watch.return_value = iter([])
            service._watch_loop(temp_ingest_dir)

            mock_watch.assert_called_once()

    def test_watch_loop_file_changes(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
    ) -> None:
        """Test watch loop handles file changes."""
        from watchfiles import Change

        # Create actual files so is_file() returns True
        new_file = temp_ingest_dir / "new_file.epub"
        new_file.touch()
        modified_file = temp_ingest_dir / "modified_file.epub"
        modified_file.touch()

        changes = [
            (Change.added, str(new_file)),
            (Change.modified, str(modified_file)),
        ]

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.watch"
            ) as mock_watch,
            patch.object(service, "_trigger_discovery") as mock_trigger,
        ):
            # Make watch return an iterator that yields changes then stops
            def watch_generator() -> Iterator[list]:
                yield changes
                service._stop_event.set()  # Stop after first iteration

            mock_watch.return_value = watch_generator()
            service._watch_loop(temp_ingest_dir)

            mock_trigger.assert_called_once()

    def test_watch_loop_ignores_non_files(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
    ) -> None:
        """Test watch loop ignores non-file changes."""
        from watchfiles import Change

        changes = [
            (Change.deleted, str(temp_ingest_dir / "deleted_file.epub")),
        ]

        with (
            patch(
                "fundamental.services.ingest.ingest_watcher_service.watch"
            ) as mock_watch,
            patch.object(service, "_trigger_discovery") as mock_trigger,
        ):
            mock_watch.return_value = iter([changes])
            service._watch_loop(temp_ingest_dir)

            mock_trigger.assert_not_called()

    def test_watch_loop_exception(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
    ) -> None:
        """Test watch loop handles exceptions."""
        with patch(
            "fundamental.services.ingest.ingest_watcher_service.watch"
        ) as mock_watch:
            mock_watch.side_effect = Exception("Watch error")
            # Should not raise
            service._watch_loop(temp_ingest_dir)


class TestPollLoop:
    """Test _poll_loop method."""

    def test_poll_loop_stop_event(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
    ) -> None:
        """Test poll loop stops on stop event."""
        service._stop_event.set()

        with patch.object(service, "_trigger_discovery") as mock_trigger:
            service._poll_loop(temp_ingest_dir)

            mock_trigger.assert_not_called()

    def test_poll_loop_new_files(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
    ) -> None:
        """Test poll loop detects new files."""
        test_file = temp_ingest_dir / "new_file.epub"
        test_file.touch()

        with (
            patch.object(service, "_trigger_discovery") as mock_trigger,
            patch.object(service._stop_event, "wait") as mock_wait,
        ):
            # First call returns False (timeout), second returns True (stop event)
            mock_wait.side_effect = [False, True]

            service._poll_loop(temp_ingest_dir)

            mock_trigger.assert_called_once()

    def test_poll_loop_dir_not_exists(
        self,
        service: IngestWatcherService,
    ) -> None:
        """Test poll loop handles non-existent directory."""
        nonexistent_dir = Path("/nonexistent/dir")

        with (
            patch.object(service, "_trigger_discovery") as mock_trigger,
            patch.object(service._stop_event, "wait") as mock_wait,
        ):
            mock_wait.side_effect = [False, True]

            service._poll_loop(nonexistent_dir)

            mock_trigger.assert_not_called()

    def test_poll_loop_exception(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
    ) -> None:
        """Test poll loop handles exceptions."""
        with (
            patch.object(service._stop_event, "wait") as mock_wait,
            patch("pathlib.Path.iterdir") as mock_iterdir,
        ):
            mock_wait.side_effect = [False, True]
            mock_iterdir.side_effect = Exception("Iteration error")

            # Should not raise
            service._poll_loop(temp_ingest_dir)

    def test_poll_loop_no_new_files(
        self,
        service: IngestWatcherService,
        temp_ingest_dir: Path,
    ) -> None:
        """Test poll loop with no new files."""
        # Set last scan files to match current
        test_file = temp_ingest_dir / "existing_file.epub"
        test_file.touch()
        service._last_scan_files = {test_file}

        with (
            patch.object(service, "_trigger_discovery") as mock_trigger,
            patch.object(service._stop_event, "wait") as mock_wait,
        ):
            mock_wait.side_effect = [False, True]

            service._poll_loop(temp_ingest_dir)

            mock_trigger.assert_not_called()


class TestShouldTrigger:
    """Test _should_trigger method."""

    def test_should_trigger_debounce_passed(
        self,
        service: IngestWatcherService,
    ) -> None:
        """Test trigger when debounce time has passed."""
        service._last_trigger_time = time.time() - 1.0  # 1 second ago

        result = service._should_trigger()

        assert result is True
        assert service._last_trigger_time > 0

    def test_should_trigger_debounce_not_passed(
        self,
        service: IngestWatcherService,
    ) -> None:
        """Test trigger when debounce time hasn't passed."""
        service._last_trigger_time = time.time()  # Just now

        result = service._should_trigger()

        assert result is False


class TestTriggerDiscovery:
    """Test _trigger_discovery method."""

    def test_trigger_discovery_success(
        self,
        service: IngestWatcherService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test successful discovery trigger."""
        service._last_trigger_time = 0.0  # Reset to allow trigger

        service._trigger_discovery()

        mock_task_runner.enqueue.assert_called_once()
        call_args = mock_task_runner.enqueue.call_args
        assert call_args.kwargs["task_type"] == TaskType.INGEST_DISCOVERY
        assert call_args.kwargs["user_id"] == 0

    def test_trigger_discovery_no_runner(
        self,
        service_no_runner: IngestWatcherService,
    ) -> None:
        """Test trigger without task runner."""
        service_no_runner._trigger_discovery()

        # Should not raise

    def test_trigger_discovery_debounce(
        self,
        service: IngestWatcherService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test trigger respects debounce."""
        service._last_trigger_time = time.time()  # Just triggered

        service._trigger_discovery()

        mock_task_runner.enqueue.assert_not_called()

    def test_trigger_discovery_bypass_debounce(
        self,
        service: IngestWatcherService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test trigger with bypass debounce."""
        service._last_trigger_time = time.time()  # Just triggered

        service._trigger_discovery(bypass_debounce=True)

        mock_task_runner.enqueue.assert_called_once()

    def test_trigger_discovery_exception(
        self,
        service: IngestWatcherService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test trigger handles exceptions."""
        service._last_trigger_time = 0.0
        mock_task_runner.enqueue.side_effect = Exception("Enqueue error")

        # Should not raise
        service._trigger_discovery()


class TestTriggerManualScan:
    """Test trigger_manual_scan method."""

    def test_trigger_manual_scan_success(
        self,
        service: IngestWatcherService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test successful manual scan trigger."""
        task_id = service.trigger_manual_scan()

        assert task_id == 123
        mock_task_runner.enqueue.assert_called_once()
        call_args = mock_task_runner.enqueue.call_args
        assert call_args.kwargs["task_type"] == TaskType.INGEST_DISCOVERY

    def test_trigger_manual_scan_no_runner(
        self,
        service_no_runner: IngestWatcherService,
    ) -> None:
        """Test manual scan without task runner."""
        result = service_no_runner.trigger_manual_scan()

        assert result is None

    def test_trigger_manual_scan_exception(
        self,
        service: IngestWatcherService,
        mock_task_runner: MagicMock,
    ) -> None:
        """Test manual scan handles exceptions."""
        mock_task_runner.enqueue.side_effect = Exception("Enqueue error")

        result = service.trigger_manual_scan()

        assert result is None
