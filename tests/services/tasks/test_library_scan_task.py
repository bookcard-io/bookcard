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

"""Tests for library scan monitoring behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Protocol, cast
from unittest.mock import MagicMock, call

import pytest
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

import bookcard.services.tasks.library_scan.publisher as publisher_module
from bookcard.models.config import Library
from bookcard.services.messaging.base import MessagePublisher
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.library_scan.errors import (
    LibraryNotFoundError,
    RedisUnavailableError,
    ScanDispatchError,
    ScanFailedError,
    ScanStateUnavailableError,
)
from bookcard.services.tasks.library_scan.monitor import ScanProgressMonitor
from bookcard.services.tasks.library_scan.orchestrator import LibraryScanOrchestrator
from bookcard.services.tasks.library_scan.publisher import ScanJob, ScanJobPublisher
from bookcard.services.tasks.library_scan.state_repository import (
    LibraryScanStateRepository,
)
from bookcard.services.tasks.library_scan.task import LibraryScanTask
from bookcard.services.tasks.library_scan.types import DataSourceConfig, ScanStatus

if TYPE_CHECKING:
    from sqlmodel import Session

    from tests.conftest import DummySession


class _LibraryFactory(Protocol):
    def __call__(
        self, *, library_id: int | None = 1, db_path: str = "/tmp/lib"
    ) -> Library: ...


@dataclass
class _State:
    scan_status: str


class TestScanProgressMonitor:
    """Unit tests for ``ScanProgressMonitor``."""

    def test_cancelled_returns_early(self) -> None:
        """Monitor returns immediately when cancelled."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.refresh_view.return_value = None
        repo.get_by_library_id.return_value = _State("running")

        monitor = ScanProgressMonitor(
            repo, sleep=lambda _: None, poll_interval_seconds=0.0
        )
        monitor.wait_for_terminal_state(1, is_cancelled=lambda: True)

        repo.refresh_view.assert_not_called()
        repo.get_by_library_id.assert_not_called()

    def test_non_terminal_state_sleeps_and_retries(self) -> None:
        """Monitor sleeps when scan state is non-terminal."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.refresh_view.return_value = None
        repo.get_by_library_id.side_effect = [_State("running"), _State("completed")]

        sleep_calls: list[float] = []

        def sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        monitor = ScanProgressMonitor(repo, sleep=sleep, poll_interval_seconds=0.25)
        monitor.wait_for_terminal_state(1)

        assert sleep_calls == [0.25]

    def test_missing_state_retry_limit(self) -> None:
        """Monitor raises when state is missing for too long."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.get_by_library_id.return_value = None
        repo.refresh_view.return_value = None

        sleep_calls: list[float] = []

        def sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        monitor = ScanProgressMonitor(
            repo,
            sleep=sleep,
            poll_interval_seconds=0.0,
            max_missing_state_retries=12,
        )

        with pytest.raises(
            ScanStateUnavailableError, match="disappeared or cannot be retrieved"
        ):
            monitor.wait_for_terminal_state(1)

        assert repo.get_by_library_id.call_count >= 13
        assert len(sleep_calls) >= 12

    def test_recovers_after_missing_state(self) -> None:
        """Monitor succeeds when state eventually appears as completed."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.refresh_view.return_value = None
        repo.get_by_library_id.side_effect = [None, None, _State("completed")]

        sleep_calls: list[float] = []

        def sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        progress: list[float] = []

        monitor = ScanProgressMonitor(
            repo,
            sleep=sleep,
            poll_interval_seconds=0.0,
            max_missing_state_retries=12,
        )
        monitor.wait_for_terminal_state(1, on_terminal_progress=progress.append)

        assert repo.get_by_library_id.call_count == 3
        assert len(sleep_calls) == 2
        assert progress == [1.0]

    def test_db_failure_retry_limit(self) -> None:
        """Monitor raises when DB errors persist."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.refresh_view.return_value = None
        repo.get_by_library_id.side_effect = SQLAlchemyError("DB Connection failed")

        sleep_calls: list[float] = []

        def sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        monitor = ScanProgressMonitor(
            repo,
            sleep=sleep,
            poll_interval_seconds=0.0,
            max_missing_state_retries=12,
        )

        with pytest.raises(
            ScanStateUnavailableError, match="disappeared or cannot be retrieved"
        ):
            monitor.wait_for_terminal_state(1)

        assert repo.get_by_library_id.call_count >= 13
        assert len(sleep_calls) >= 12

    def test_failed_state_raises(self) -> None:
        """Monitor raises when scan is marked failed."""
        repo = MagicMock(spec=LibraryScanStateRepository)
        repo.refresh_view.return_value = None
        repo.get_by_library_id.return_value = _State("failed")

        monitor = ScanProgressMonitor(
            repo, sleep=lambda _: None, poll_interval_seconds=0.0
        )

        with pytest.raises(ScanFailedError, match="marked in ScanState"):
            monitor.wait_for_terminal_state(1)


class TestDataSourceConfig:
    """Unit tests for ``DataSourceConfig`` parsing/serialization."""

    @pytest.mark.parametrize(
        ("metadata", "expected_name", "expected_kwargs"),
        [
            ({}, "openlibrary", {}),
            ({"data_source_config": None}, "openlibrary", {}),
            ({"data_source_config": "nope"}, "openlibrary", {}),
            ({"data_source_config": {}}, "openlibrary", {}),
            ({"data_source_config": {"name": "", "kwargs": {}}}, "openlibrary", {}),
            ({"data_source_config": {"name": 123, "kwargs": {}}}, "openlibrary", {}),
            ({"data_source_config": {"name": "x", "kwargs": None}}, "x", {}),
            ({"data_source_config": {"name": "x", "kwargs": "nope"}}, "x", {}),
            ({"data_source_config": {"name": "x", "kwargs": {"a": 1}}}, "x", {"a": 1}),
        ],
    )
    def test_from_metadata_defaults(
        self,
        metadata: dict[str, Any],
        expected_name: str,
        expected_kwargs: dict[str, Any],
    ) -> None:
        cfg = DataSourceConfig.from_metadata(metadata)
        assert cfg.name == expected_name
        assert cfg.kwargs == expected_kwargs

    def test_to_payload_returns_copy(self) -> None:
        cfg = DataSourceConfig(name="x", kwargs={"a": 1})
        payload = cfg.to_payload()
        assert payload == {"name": "x", "kwargs": {"a": 1}}
        assert payload["kwargs"] is not cfg.kwargs


@pytest.fixture
def library_factory() -> _LibraryFactory:
    def _make(*, library_id: int | None = 1, db_path: str = "/tmp/lib") -> Library:
        return Library(
            id=library_id,
            name="Test Library",
            calibre_db_path=db_path,
            calibre_db_file="metadata.db",
        )

    return _make


class TestScanJob:
    """Unit tests for ``ScanJob`` payload building."""

    def test_to_payload_defaults_db_filename(
        self, library_factory: _LibraryFactory
    ) -> None:
        library = library_factory(library_id=123)
        library.calibre_db_file = ""  # force default
        job = ScanJob(
            task_id=9, library=library, data_source_config=DataSourceConfig("x", {})
        )
        assert job.to_payload()["calibre_db_file"] == "metadata.db"

    def test_to_payload_includes_expected_fields(
        self, library_factory: _LibraryFactory
    ) -> None:
        library = library_factory(library_id=123, db_path="/data/calibre")
        library.calibre_db_file = "meta.db"
        cfg = DataSourceConfig(name="openlibrary", kwargs={"k": "v"})
        job = ScanJob(task_id=9, library=library, data_source_config=cfg)
        assert job.to_payload() == {
            "task_id": 9,
            "library_id": 123,
            "calibre_db_path": "/data/calibre",
            "calibre_db_file": "meta.db",
            "data_source_config": {"name": "openlibrary", "kwargs": {"k": "v"}},
        }


class TestScanJobPublisher:
    """Unit tests for ``ScanJobPublisher``."""

    def test_clear_previous_progress_noop_for_non_redis_broker(self) -> None:
        pub = ScanJobPublisher(object())  # type: ignore[arg-type]
        pub.clear_previous_progress(1)  # should not raise

    def test_clear_previous_progress_clears_when_redis_broker(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[tuple[str, object]] = []

        class FakeRedisBroker:
            pass

        class FakeTracker:
            def __init__(self, broker: object) -> None:
                calls.append(("init", broker))

            def clear_job(self, library_id: int) -> None:
                calls.append(("clear_job", library_id))

        monkeypatch.setattr(publisher_module, "RedisBroker", FakeRedisBroker)
        monkeypatch.setattr(publisher_module, "JobProgressTracker", FakeTracker)

        broker = FakeRedisBroker()
        pub = ScanJobPublisher(broker)  # type: ignore[arg-type]
        pub.clear_previous_progress(42)

        assert calls == [("init", broker), ("clear_job", 42)]

    @pytest.mark.parametrize(
        ("exc", "expected_msg"),
        [
            (RedisError("redis down"), "redis down"),
            (ValueError("bad payload"), "bad payload"),
        ],
    )
    def test_publish_translates_errors(self, exc: Exception, expected_msg: str) -> None:
        class FailingPublisher:
            def publish(self, topic: str, message: dict[str, Any]) -> None:
                raise exc

        pub = ScanJobPublisher(FailingPublisher())  # type: ignore[arg-type]
        job = MagicMock(spec=ScanJob)
        job.to_payload.return_value = {"k": "v"}

        with pytest.raises(ScanDispatchError, match=expected_msg):
            pub.publish(job)


class TestLibraryScanStateRepository:
    """Unit tests for ``LibraryScanStateRepository`` without a real DB."""

    class _Result:
        def __init__(self, items: list[Any]) -> None:
            self._items = items

        def first(self) -> Any | None:  # noqa: ANN401
            return self._items[0] if self._items else None

    class _Session:
        def __init__(self, exec_results: list[list[Any]]) -> None:
            self._exec_results = list(exec_results)
            self.added: list[Any] = []
            self.commit_count = 0
            self.expire_all_count = 0

        def exec(self, stmt: Any) -> TestLibraryScanStateRepository._Result:  # noqa: ANN401
            items = self._exec_results.pop(0) if self._exec_results else []
            return TestLibraryScanStateRepository._Result(items)

        def add(self, entity: Any) -> None:  # noqa: ANN401
            self.added.append(entity)

        def commit(self) -> None:
            self.commit_count += 1

        def expire_all(self) -> None:
            self.expire_all_count += 1

    def test_upsert_creates_when_missing(self) -> None:
        session = self._Session(exec_results=[[]])
        repo = LibraryScanStateRepository(session)  # type: ignore[arg-type]

        state = repo.upsert_status(10, ScanStatus.PENDING)
        assert state.library_id == 10
        assert state.scan_status == ScanStatus.PENDING.value
        assert session.added == [state]
        assert session.commit_count == 1

    def test_upsert_updates_and_sets_last_scan_at_on_completed(self) -> None:
        existing = MagicMock()
        existing.library_id = 10
        existing.scan_status = ScanStatus.PENDING.value
        existing.last_scan_at = None
        existing.updated_at = datetime.now(UTC) - timedelta(days=1)

        session = self._Session(exec_results=[[existing]])
        repo = LibraryScanStateRepository(session)  # type: ignore[arg-type]

        state = repo.upsert_status(10, ScanStatus.COMPLETED)
        assert state is existing
        assert existing.scan_status == ScanStatus.COMPLETED.value
        assert existing.last_scan_at is not None
        assert existing.updated_at > datetime.now(UTC) - timedelta(hours=1)
        assert session.added == []
        assert session.commit_count == 1

    def test_refresh_view_expires_all(self) -> None:
        session = self._Session(exec_results=[[]])
        repo = LibraryScanStateRepository(session)  # type: ignore[arg-type]
        repo.refresh_view()
        assert session.expire_all_count == 1


class TestLibraryScanOrchestrator:
    """Unit tests for ``LibraryScanOrchestrator``."""

    def test_resolve_libraries_all(
        self, session: DummySession, library_factory: _LibraryFactory
    ) -> None:
        libraries = [library_factory(library_id=1), library_factory(library_id=2)]
        session.add_exec_result(libraries)

        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=MagicMock(spec=ScanJobPublisher),
            state_repo=MagicMock(spec=LibraryScanStateRepository),
            monitor=MagicMock(spec=ScanProgressMonitor),
        )
        assert orchestrator.resolve_libraries(None) == libraries

    def test_resolve_libraries_by_id_not_found(self, session: DummySession) -> None:
        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=MagicMock(spec=ScanJobPublisher),
            state_repo=MagicMock(spec=LibraryScanStateRepository),
            monitor=MagicMock(spec=ScanProgressMonitor),
        )
        with pytest.raises(LibraryNotFoundError, match="Library 999 not found"):
            orchestrator.resolve_libraries(999)

    def test_resolve_libraries_by_id_found(
        self, session: DummySession, library_factory: _LibraryFactory
    ) -> None:
        library = library_factory(library_id=123)
        session.set_get_result(Library, library)

        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=MagicMock(spec=ScanJobPublisher),
            state_repo=MagicMock(spec=LibraryScanStateRepository),
            monitor=MagicMock(spec=ScanProgressMonitor),
        )
        assert orchestrator.resolve_libraries(123) == [library]

    def test_scan_no_libraries_updates_progress_and_returns(
        self, session: DummySession
    ) -> None:
        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=MagicMock(spec=ScanJobPublisher),
            state_repo=MagicMock(spec=LibraryScanStateRepository),
            monitor=MagicMock(spec=ScanProgressMonitor),
        )
        orchestrator.resolve_libraries = MagicMock(return_value=[])  # type: ignore[method-assign]
        progress = MagicMock()

        orchestrator.scan(
            task_id=1,
            library_id=None,
            data_source_config=DataSourceConfig("x", {}),
            update_overall_progress=progress,
        )

        progress.assert_called_once_with(1.0)

    def test_scan_cancellation_stops_early(
        self, session: DummySession, library_factory: _LibraryFactory
    ) -> None:
        libs = [library_factory(library_id=1), library_factory(library_id=2)]

        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=MagicMock(spec=ScanJobPublisher),
            state_repo=MagicMock(spec=LibraryScanStateRepository),
            monitor=MagicMock(spec=ScanProgressMonitor),
        )
        orchestrator.resolve_libraries = MagicMock(return_value=libs)  # type: ignore[method-assign]
        scan_one = MagicMock()
        orchestrator._scan_one = scan_one  # type: ignore[method-assign]

        calls = 0

        def is_cancelled() -> bool:
            nonlocal calls
            calls += 1
            return calls >= 2

        progress = MagicMock()
        orchestrator.scan(
            task_id=1,
            library_id=None,
            data_source_config=DataSourceConfig("x", {}),
            is_cancelled=is_cancelled,
            update_overall_progress=progress,
        )

        assert scan_one.call_count == 1
        progress.assert_called_once_with(0.5)

    def test_scan_aggregates_failures_and_updates_progress(
        self, session: DummySession, library_factory: _LibraryFactory
    ) -> None:
        lib_ok = library_factory(library_id=1)
        lib_skip = library_factory(library_id=None)
        lib_fail = library_factory(library_id=3)
        libs = [lib_ok, lib_skip, lib_fail]

        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=MagicMock(spec=ScanJobPublisher),
            state_repo=MagicMock(spec=LibraryScanStateRepository),
            monitor=MagicMock(spec=ScanProgressMonitor),
        )
        orchestrator.resolve_libraries = MagicMock(return_value=libs)  # type: ignore[method-assign]

        def scan_one_side_effect(*_: object, **kwargs: object) -> None:
            library = cast("Library", kwargs["library"])
            if library.id == 3:
                raise ValueError("boom")

        orchestrator._scan_one = MagicMock(side_effect=scan_one_side_effect)  # type: ignore[method-assign]
        progress = MagicMock()

        with pytest.raises(RuntimeError, match=r"Scans failed for libraries: \[3\]"):
            orchestrator.scan(
                task_id=1,
                library_id=None,
                data_source_config=DataSourceConfig("x", {}),
                update_overall_progress=progress,
            )

        # Note: library.id None is skipped and does not emit a progress update.
        assert progress.call_args_list == [call(1 / 3), call(1.0)]

    def test_scan_one_sets_failed_when_dispatch_fails(
        self, session: DummySession, library_factory: _LibraryFactory
    ) -> None:
        library = library_factory(library_id=10)
        publisher = MagicMock(spec=ScanJobPublisher)
        publisher.publish.side_effect = ScanDispatchError("no redis")
        state_repo = MagicMock(spec=LibraryScanStateRepository)
        monitor = MagicMock(spec=ScanProgressMonitor)

        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=publisher,
            state_repo=state_repo,
            monitor=monitor,
        )

        with pytest.raises(ScanDispatchError, match="no redis"):
            orchestrator._scan_one(
                task_id=1,
                library=library,
                data_source_config=DataSourceConfig("x", {}),
                is_cancelled=None,
                update_task_progress=None,
            )

        state_repo.upsert_status.assert_any_call(10, ScanStatus.PENDING)
        state_repo.upsert_status.assert_any_call(10, ScanStatus.FAILED)
        monitor.wait_for_terminal_state.assert_not_called()

    def test_scan_one_returns_when_library_id_missing(
        self, session: DummySession, library_factory: _LibraryFactory
    ) -> None:
        library = library_factory(library_id=None)
        publisher = MagicMock(spec=ScanJobPublisher)
        state_repo = MagicMock(spec=LibraryScanStateRepository)
        monitor = MagicMock(spec=ScanProgressMonitor)

        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=publisher,
            state_repo=state_repo,
            monitor=monitor,
        )
        orchestrator._scan_one(
            task_id=1,
            library=library,
            data_source_config=DataSourceConfig("x", {}),
            is_cancelled=None,
            update_task_progress=None,
        )

        publisher.publish.assert_not_called()
        monitor.wait_for_terminal_state.assert_not_called()

    def test_scan_one_success_publishes_and_monitors(
        self, session: DummySession, library_factory: _LibraryFactory
    ) -> None:
        library = library_factory(library_id=10)
        publisher = MagicMock(spec=ScanJobPublisher)
        state_repo = MagicMock(spec=LibraryScanStateRepository)
        monitor = MagicMock(spec=ScanProgressMonitor)
        progress = MagicMock()

        orchestrator = LibraryScanOrchestrator(
            cast("Session", session),
            job_publisher=publisher,
            state_repo=state_repo,
            monitor=monitor,
        )

        orchestrator._scan_one(
            task_id=123,
            library=library,
            data_source_config=DataSourceConfig("x", {}),
            is_cancelled=lambda: False,
            update_task_progress=progress,
        )

        publisher.clear_previous_progress.assert_called_once_with(10)
        state_repo.upsert_status.assert_called_once_with(10, ScanStatus.PENDING)
        publisher.publish.assert_called_once()
        args, kwargs = monitor.wait_for_terminal_state.call_args
        assert args == (10,)
        assert kwargs["on_terminal_progress"] is progress
        assert callable(kwargs["is_cancelled"])


class TestLibraryScanTask:
    """Unit tests for the task adapter ``LibraryScanTask``."""

    class _Publisher(MessagePublisher):
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        def publish(self, topic: str, message: dict[str, Any]) -> None:
            self.calls.append((topic, message))

    def test_run_requires_message_publisher(self, session: DummySession) -> None:
        task = LibraryScanTask(task_id=1, user_id=1, metadata={})
        with pytest.raises(RedisUnavailableError, match="requires a MessagePublisher"):
            task.run({
                "session": cast("Session", session),
                "update_progress": lambda *_: None,
            })

    @pytest.mark.parametrize("bad_library_id", ["1", 1.2, object()])
    def test_run_rejects_non_int_library_id(
        self, session: DummySession, bad_library_id: object
    ) -> None:
        task = LibraryScanTask(
            task_id=1, user_id=1, metadata={"library_id": bad_library_id}
        )
        with pytest.raises(ValueError, match="library_id must be an integer"):
            task.run({
                "session": cast("Session", session),
                "update_progress": lambda *_: None,
                "message_broker": self._Publisher(),
            })

    def test_run_delegates_to_orchestrator(
        self, monkeypatch: pytest.MonkeyPatch, session: DummySession
    ) -> None:
        calls: dict[str, Any] = {}

        class FakeOrchestrator:
            def __init__(
                self, session_arg: object, *, job_publisher: object, **_: object
            ) -> None:
                calls["session"] = session_arg
                calls["job_publisher"] = job_publisher

            def scan(self, **kwargs: object) -> None:
                calls["scan_kwargs"] = kwargs

        monkeypatch.setattr(
            "bookcard.services.tasks.library_scan.task.LibraryScanOrchestrator",
            FakeOrchestrator,
        )

        progress_calls: list[tuple[float, dict[str, Any] | None]] = []

        def update_progress(p: float, meta: dict[str, Any] | None) -> None:
            progress_calls.append((p, meta))

        task = LibraryScanTask(task_id=9, user_id=1, metadata={"library_id": 123})
        task.run({
            "session": cast("Session", session),
            "update_progress": update_progress,
            "message_broker": self._Publisher(),
        })

        assert calls["session"] is session
        assert "scan_kwargs" in calls
        assert calls["scan_kwargs"]["task_id"] == 9
        assert calls["scan_kwargs"]["library_id"] == 123
        assert isinstance(calls["scan_kwargs"]["data_source_config"], DataSourceConfig)
        # smoke-check the callback signature bridging
        calls["scan_kwargs"]["update_overall_progress"](0.5)
        assert progress_calls == [(0.5, None)]

    def test_coerce_context_from_worker_context(self, session: DummySession) -> None:
        publisher = self._Publisher()

        ctx = WorkerContext(
            session=cast("Session", session),
            update_progress=lambda *_: None,
            task_service=MagicMock(),
            enqueue_task=None,
        )
        # WorkerContext doesn't define message_broker yet; task adapter reads via getattr.
        ctx.message_broker = publisher  # type: ignore[attr-defined]

        coerced = LibraryScanTask._coerce_context(ctx)
        assert coerced["session"] is session
        assert coerced["message_broker"] is publisher
