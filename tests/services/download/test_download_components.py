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

"""Unit tests for download service components.

These tests target the small, SRP-focused modules in `bookcard.services.download`
and aim to fully exercise their branching logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, cast
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientStatus,
    DownloadClientType,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.models.pvr import (
    DownloadItem as DBDownloadItem,
)
from bookcard.pvr.models import DownloadItem as ClientDownloadItem
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.download.book_updater import TrackedBookStatusUpdater
from bookcard.services.download.client_health_manager import ClientHealthManager
from bookcard.services.download.client_repository import (
    SQLModelDownloadClientRepository,
)
from bookcard.services.download.client_selector import (
    DownloadClientSelector,
    FirstEnabledSelector,
    ProtocolBasedSelector,
)
from bookcard.services.download.factory import (
    DefaultDownloadClientFactory,
    DownloadClientFactory,
)
from bookcard.services.download.item_updater import DownloadItemUpdater
from bookcard.services.download.reconciler import DownloadReconciler
from bookcard.services.download.repository import (
    SQLModelDownloadItemRepository,
)
from bookcard.services.download.status_mapper import (
    DefaultStatusMapper,
    DownloadStatusMapper,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.pvr.base import BaseDownloadClient
    from tests.conftest import DummySession


@dataclass
class _SequenceClock:
    """Clock test double returning a deterministic sequence of timestamps."""

    times: list[datetime]
    _idx: int = 0

    def now(self) -> datetime:
        """Return next timestamp in the configured sequence."""
        t = self.times[self._idx]
        self._idx += 1
        return t


class _ReleaseFactory(Protocol):
    """Callable factory for building `ReleaseInfo` instances."""

    def __call__(
        self,
        download_url: str,
        *,
        seeders: int | None = None,
        leechers: int | None = None,
    ) -> ReleaseInfo: ...


class _ClientDefFactory(Protocol):
    """Callable factory for building `DownloadClientDefinition` instances."""

    def __call__(
        self,
        client_type: DownloadClientType,
        *,
        client_id: int = 1,
        enabled: bool = True,
    ) -> DownloadClientDefinition: ...


class _DBItemFactory(Protocol):
    """Callable factory for building `DBDownloadItem` instances."""

    def __call__(
        self,
        *,
        client_item_id: str = "hash",
        status: DownloadItemStatus = DownloadItemStatus.QUEUED,
        progress: float = 0.0,
        completed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> DBDownloadItem: ...


@pytest.fixture
def fixed_time() -> datetime:
    """Return a stable timestamp for deterministic assertions."""
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def make_release() -> _ReleaseFactory:
    """Factory for creating ReleaseInfo with varying protocol hints."""

    def _make(
        download_url: str,
        *,
        seeders: int | None = None,
        leechers: int | None = None,
    ) -> ReleaseInfo:
        return ReleaseInfo(
            title="Some Release",
            download_url=download_url,
            seeders=seeders,
            leechers=leechers,
        )

    return _make


@pytest.fixture
def make_client_def() -> _ClientDefFactory:
    """Factory for creating DownloadClientDefinition instances."""

    def _make(
        client_type: DownloadClientType,
        *,
        client_id: int = 1,
        enabled: bool = True,
    ) -> DownloadClientDefinition:
        return DownloadClientDefinition(
            id=client_id,
            name=f"Client {client_id}",
            client_type=client_type,
            host="localhost",
            enabled=enabled,
            status=DownloadClientStatus.HEALTHY,
        )

    return _make


@pytest.fixture
def make_db_item() -> _DBItemFactory:
    """Factory for creating DB DownloadItem with required fields populated."""

    def _make(
        *,
        client_item_id: str = "hash",
        status: DownloadItemStatus = DownloadItemStatus.QUEUED,
        progress: float = 0.0,
        completed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> DBDownloadItem:
        return DBDownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id=client_item_id,
            title="Title",
            download_url="magnet:...",
            status=status,
            progress=progress,
            completed_at=completed_at,
            error_message=error_message,
        )

    return _make


class TestTrackedBookStatusUpdater:
    """Tests for `TrackedBookStatusUpdater`."""

    @pytest.mark.parametrize(
        "terminal_status",
        [TrackedBookStatus.COMPLETED, TrackedBookStatus.IGNORED],
    )
    def test_update_from_download_terminal_book_status_noop(
        self, terminal_status: TrackedBookStatus
    ) -> None:
        """Terminal tracked book statuses are not changed."""
        updater = TrackedBookStatusUpdater()
        tracked = TrackedBook(title="T", author="A", status=terminal_status)

        changed = updater.update_from_download(
            tracked,
            DownloadItemStatus.DOWNLOADING,
            error_message="should not be set",
        )

        assert changed is False
        assert tracked.status == terminal_status
        assert tracked.error_message is None

    @pytest.mark.parametrize(
        ("download_status", "expected_book_status"),
        [
            (DownloadItemStatus.PAUSED, TrackedBookStatus.PAUSED),
            (DownloadItemStatus.STALLED, TrackedBookStatus.STALLED),
            (DownloadItemStatus.SEEDING, TrackedBookStatus.SEEDING),
            (DownloadItemStatus.DOWNLOADING, TrackedBookStatus.DOWNLOADING),
            (DownloadItemStatus.QUEUED, TrackedBookStatus.DOWNLOADING),
            (DownloadItemStatus.FAILED, TrackedBookStatus.FAILED),
        ],
    )
    def test_update_from_download_maps_status_and_updates(
        self,
        download_status: DownloadItemStatus,
        expected_book_status: TrackedBookStatus,
    ) -> None:
        """Download status is mapped and applied to the tracked book."""
        updater = TrackedBookStatusUpdater()
        tracked = TrackedBook(title="T", author="A", status=TrackedBookStatus.WANTED)

        changed = updater.update_from_download(
            tracked,
            download_status,
            error_message="boom",
        )

        assert changed is True
        assert tracked.status == expected_book_status
        if expected_book_status == TrackedBookStatus.FAILED:
            assert tracked.error_message == "boom"
        else:
            assert tracked.error_message is None

    @pytest.mark.parametrize(
        "download_status",
        [DownloadItemStatus.COMPLETED, DownloadItemStatus.REMOVED],
    )
    def test_update_from_download_unmapped_status_noop(
        self, download_status: DownloadItemStatus
    ) -> None:
        """Statuses that don't map to book state do not change the tracked book."""
        updater = TrackedBookStatusUpdater()
        tracked = TrackedBook(
            title="T",
            author="A",
            status=TrackedBookStatus.WANTED,
            error_message="x",
        )

        changed = updater.update_from_download(tracked, download_status)

        assert changed is False
        assert tracked.status == TrackedBookStatus.WANTED
        assert tracked.error_message == "x"

    def test_update_from_download_same_status_noop(self) -> None:
        """No change is reported when status would remain the same."""
        updater = TrackedBookStatusUpdater()
        tracked = TrackedBook(
            title="T", author="A", status=TrackedBookStatus.DOWNLOADING
        )

        changed = updater.update_from_download(tracked, DownloadItemStatus.QUEUED)

        assert changed is False
        assert tracked.status == TrackedBookStatus.DOWNLOADING


class TestClientHealthManager:
    """Tests for `ClientHealthManager`."""

    def test_update_status_healthy_resets_errors_and_sets_success_time(
        self, fixed_time: datetime
    ) -> None:
        """Healthy updates reset error state and set timestamps."""
        later = fixed_time.replace(minute=fixed_time.minute + 1)
        clock = _SequenceClock([fixed_time, later])
        session = MagicMock()
        manager = ClientHealthManager(session=session, clock=clock)

        client = DownloadClientDefinition(
            id=1,
            name="Client",
            client_type=DownloadClientType.QBITTORRENT,
            host="localhost",
            enabled=True,
            status=DownloadClientStatus.UNHEALTHY,
            error_count=2,
            error_message="bad",
        )

        manager.update_status(
            client=client,
            status=DownloadClientStatus.HEALTHY,
            error_message="ignored",
        )

        assert client.status == DownloadClientStatus.HEALTHY
        assert client.last_checked_at == fixed_time
        assert client.last_successful_connection_at == later
        assert client.error_count == 0
        assert client.error_message is None
        session.add.assert_called_once_with(client)

    def test_update_status_unhealthy_increments_errors_and_sets_message(
        self, fixed_time: datetime
    ) -> None:
        """Unhealthy updates increment errors and retain last successful timestamp."""
        clock = _SequenceClock([fixed_time])
        session = MagicMock()
        manager = ClientHealthManager(session=session, clock=clock)

        existing_success = fixed_time - timedelta(days=1)
        client = DownloadClientDefinition(
            id=1,
            name="Client",
            client_type=DownloadClientType.QBITTORRENT,
            host="localhost",
            enabled=True,
            status=DownloadClientStatus.HEALTHY,
            error_count=1,
            error_message=None,
            last_successful_connection_at=existing_success,
        )

        manager.update_status(
            client=client,
            status=DownloadClientStatus.UNHEALTHY,
            error_message="boom",
        )

        assert client.status == DownloadClientStatus.UNHEALTHY
        assert client.last_checked_at == fixed_time
        assert client.last_successful_connection_at == existing_success
        assert client.error_count == 2
        assert client.error_message == "boom"
        session.add.assert_called_once_with(client)


class TestSQLModelDownloadClientRepository:
    """Tests for `SQLModelDownloadClientRepository`."""

    def test_get_enabled_clients_returns_exec_results(
        self, session: DummySession, make_client_def: _ClientDefFactory
    ) -> None:
        """Repository returns enabled clients from session.exec()."""
        repo = SQLModelDownloadClientRepository(cast("Session", session))
        session.add_exec_result([make_client_def(DownloadClientType.QBITTORRENT)])

        result = repo.get_enabled_clients()

        assert len(result) == 1
        assert isinstance(result[0], DownloadClientDefinition)

    def test_get_enabled_clients_empty(self, session: DummySession) -> None:
        """Repository returns empty list when no results exist."""
        repo = SQLModelDownloadClientRepository(cast("Session", session))
        session.add_exec_result([])

        assert repo.get_enabled_clients() == []


class TestDownloadClientSelectorStrategies:
    """Tests for client selection strategies."""

    def test_abstract_selector_raises(self, make_release: _ReleaseFactory) -> None:
        """Abstract base selector raises by default."""

        class _ConcreteBaseSelector(DownloadClientSelector):
            def select(
                self,
                release: ReleaseInfo,
                clients: list[DownloadClientDefinition],
            ) -> DownloadClientDefinition | None:
                return super().select(release, clients)

        selector = _ConcreteBaseSelector()
        with pytest.raises(NotImplementedError):
            selector.select(make_release("magnet:..."), [])

    def test_first_enabled_selector_empty(self, make_release: _ReleaseFactory) -> None:
        """No clients yields no selection."""
        selector = FirstEnabledSelector()
        assert selector.select(make_release("magnet:..."), []) is None

    def test_first_enabled_selector_returns_first(
        self, make_release: _ReleaseFactory
    ) -> None:
        """FirstEnabledSelector returns the first list entry."""
        selector = FirstEnabledSelector()
        clients = [
            DownloadClientDefinition(
                id=1,
                name="First",
                client_type=DownloadClientType.TRANSMISSION,
                host="localhost",
                enabled=False,
                status=DownloadClientStatus.DISABLED,
            ),
            DownloadClientDefinition(
                id=2,
                name="Second",
                client_type=DownloadClientType.QBITTORRENT,
                host="localhost",
                enabled=True,
                status=DownloadClientStatus.HEALTHY,
            ),
        ]
        assert selector.select(make_release("magnet:..."), clients) == clients[0]

    @pytest.mark.parametrize(
        ("client_type", "expected"),
        [
            (DownloadClientType.DOWNLOAD_STATION, {"torrent", "usenet"}),
            (DownloadClientType.SABNZBD, {"usenet"}),
            (DownloadClientType.NZBGET, {"usenet"}),
            (DownloadClientType.PNEUMATIC, {"usenet"}),
            (DownloadClientType.USENET_BLACKHOLE, {"usenet"}),
            (DownloadClientType.DIRECT_HTTP, {"http"}),
            (DownloadClientType.QBITTORRENT, {"torrent"}),
        ],
    )
    def test_protocol_based_selector_get_client_protocols(
        self, client_type: DownloadClientType, expected: set[str]
    ) -> None:
        """Protocol mapping for client types is deterministic."""
        assert ProtocolBasedSelector._get_client_protocols(client_type) == expected

    @pytest.mark.parametrize(
        ("download_url", "seeders", "leechers", "expected"),
        [
            ("magnet:?xt=urn:btih:abc", None, None, "torrent"),
            ("http://example.com/file.nzb", None, None, "usenet"),
            ("http://example.com/file.nzb?token=abc", None, None, "usenet"),
            ("http://example.com/file", 1, None, "torrent"),
            ("HTTP://example.com/file.torrent", None, None, "torrent"),
            ("https://example.com/book.epub", None, None, "http"),
            ("ftp://example.com/book.epub", None, None, None),
        ],
    )
    def test_protocol_based_selector_determine_protocol(
        self,
        make_release: _ReleaseFactory,
        download_url: str,
        seeders: int | None,
        leechers: int | None,
        expected: str | None,
    ) -> None:
        """Protocol is inferred from url/fields."""
        selector = ProtocolBasedSelector()
        release = make_release(download_url, seeders=seeders, leechers=leechers)
        assert selector._determine_protocol(release) == expected

    def test_protocol_based_selector_select_none_when_no_clients(
        self, make_release: _ReleaseFactory
    ) -> None:
        """No clients yields no selection."""
        selector = ProtocolBasedSelector()
        assert selector.select(make_release("magnet:..."), []) is None

    def test_protocol_based_selector_select_fallback_when_protocol_unknown(
        self, make_release: _ReleaseFactory, make_client_def: _ClientDefFactory
    ) -> None:
        """When protocol can't be determined, fall back to the first client."""
        selector = ProtocolBasedSelector()
        clients = [
            make_client_def(DownloadClientType.QBITTORRENT, client_id=1),
            make_client_def(DownloadClientType.SABNZBD, client_id=2),
        ]
        # ftp doesn't match any heuristic => None => fall back to clients[0]
        assert (
            selector.select(make_release("ftp://example.com/file"), clients)
            == clients[0]
        )

    def test_protocol_based_selector_select_compatible_client(
        self, make_release: _ReleaseFactory, make_client_def: _ClientDefFactory
    ) -> None:
        """Select first compatible client for inferred protocol."""
        selector = ProtocolBasedSelector()
        torrent_client = make_client_def(DownloadClientType.QBITTORRENT, client_id=1)
        http_client = make_client_def(DownloadClientType.DIRECT_HTTP, client_id=2)
        clients = [torrent_client, http_client]

        selected = selector.select(
            make_release("https://example.com/book.epub"), clients
        )

        assert selected == http_client

    def test_protocol_based_selector_select_fallback_when_no_compatible(
        self, make_release: _ReleaseFactory, make_client_def: _ClientDefFactory
    ) -> None:
        """If none are compatible, fall back to first client."""
        selector = ProtocolBasedSelector()
        clients = [make_client_def(DownloadClientType.QBITTORRENT, client_id=1)]

        selected = selector.select(make_release("http://example.com/file.nzb"), clients)

        assert selected == clients[0]


class TestDownloadClientFactory:
    """Tests for download client factories."""

    def test_abstract_factory_raises(self, make_client_def: _ClientDefFactory) -> None:
        """Abstract factory raises by default."""
        definition = make_client_def(DownloadClientType.QBITTORRENT)

        class _ConcreteBaseFactory(DownloadClientFactory):
            def create(
                self, definition: DownloadClientDefinition
            ) -> BaseDownloadClient:
                return super().create(definition)

        factory = _ConcreteBaseFactory()
        with pytest.raises(NotImplementedError):
            factory.create(definition)

    def test_default_factory_delegates_to_create_download_client(
        self, make_client_def: _ClientDefFactory
    ) -> None:
        """Default factory delegates to `create_download_client`."""
        definition = make_client_def(DownloadClientType.QBITTORRENT)
        factory = DefaultDownloadClientFactory()
        sentinel = object()

        with patch(
            "bookcard.pvr.factory.download_client_factory.create_download_client",
            return_value=sentinel,
        ) as mock_create:
            assert factory.create(definition) is sentinel
            mock_create.assert_called_once_with(definition)


class TestDownloadItemUpdater:
    """Tests for `DownloadItemUpdater`."""

    def test_init_defaults(self) -> None:
        """Updater defaults to DefaultStatusMapper and UTCClock."""
        updater = DownloadItemUpdater()
        assert updater is not None

    @pytest.mark.parametrize(
        ("client_status", "expected"),
        [
            ("completed", DownloadItemStatus.COMPLETED),
            ("COMPLETED", DownloadItemStatus.COMPLETED),
            ("unknown-status", DownloadItemStatus.DOWNLOADING),
        ],
    )
    def test_default_status_mapper_map(
        self, client_status: str, expected: DownloadItemStatus
    ) -> None:
        """DefaultStatusMapper lowercases and provides a fallback."""
        assert DefaultStatusMapper().map(client_status) == expected

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (DownloadItemStatus.COMPLETED, True),
            (DownloadItemStatus.FAILED, True),
            (DownloadItemStatus.REMOVED, True),
            (DownloadItemStatus.DOWNLOADING, False),
            (DownloadItemStatus.QUEUED, False),
        ],
    )
    def test_download_status_mapper_is_terminal(
        self, status: DownloadItemStatus, expected: bool
    ) -> None:
        """Terminal status helper returns correct membership."""
        assert DownloadStatusMapper.is_terminal(status) is expected

    @pytest.mark.parametrize(
        ("client_item", "expected_progress"),
        [
            ({"progress": 0.5}, 0.5),
            ({"progress": "0.25"}, 0.25),
            ({"progress": None}, None),
            ({}, None),
        ],
    )
    def test_update_progress_safe_extract(
        self,
        make_db_item: _DBItemFactory,
        client_item: dict[str, object],
        expected_progress: float | None,
    ) -> None:
        """Progress is extracted and converted safely."""
        updater = DownloadItemUpdater()
        initial_progress = 0.1
        db_item = make_db_item(progress=initial_progress)

        updater._update_progress(db_item, cast("ClientDownloadItem", client_item))

        assert (
            db_item.progress == expected_progress
            if expected_progress is not None
            else initial_progress
        )

    def test_safe_extract_logs_and_defaults_on_conversion_error(
        self,
        make_db_item: _DBItemFactory,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Conversion errors are swallowed and logged."""
        updater = DownloadItemUpdater()
        caplog.set_level("WARNING")

        db_item = make_db_item(progress=0.1)
        bad_item = cast("ClientDownloadItem", {"progress": "not-a-float"})
        updater._update_progress(db_item, bad_item)

        assert db_item.progress == 0.1
        assert any(
            "Failed to convert progress" in rec.message for rec in caplog.records
        )

    def test_update_sets_status_metadata_completion_and_failure(
        self, fixed_time: datetime, make_db_item: _DBItemFactory
    ) -> None:
        """Update applies status mapping, metadata updates, and completion/failure hooks."""
        clock = _SequenceClock([fixed_time])
        mapper = MagicMock()
        mapper.map.return_value = DownloadItemStatus.COMPLETED
        updater = DownloadItemUpdater(status_mapper=mapper, clock=clock)

        db_item = make_db_item(status=DownloadItemStatus.QUEUED, progress=0.0)
        client_item: ClientDownloadItem = {
            "client_item_id": "x",
            "title": "t",
            "status": "completed",
            "progress": 1.0,
            "size_bytes": 123,
            "downloaded_bytes": 123,
            "download_speed_bytes_per_sec": 1.0,
            "eta_seconds": 0,
            "file_path": "/tmp/file",
        }

        updater.update(db_item, client_item)

        assert db_item.progress == 1.0
        assert db_item.status == DownloadItemStatus.COMPLETED
        assert db_item.size_bytes == 123
        assert db_item.downloaded_bytes == 123
        assert db_item.download_speed_bytes_per_sec == 1.0
        assert db_item.eta_seconds == 0
        assert db_item.file_path == "/tmp/file"
        assert db_item.completed_at == fixed_time
        assert db_item.error_message is None
        mapper.map.assert_called_once_with("completed")

    def test_completion_does_not_override_existing_timestamp(
        self, fixed_time: datetime, make_db_item: _DBItemFactory
    ) -> None:
        """Completed timestamp is only set once."""
        existing = fixed_time - timedelta(days=1)
        clock = _SequenceClock([fixed_time])
        mapper = MagicMock()
        mapper.map.return_value = DownloadItemStatus.COMPLETED
        updater = DownloadItemUpdater(status_mapper=mapper, clock=clock)

        db_item = make_db_item(
            status=DownloadItemStatus.COMPLETED, completed_at=existing
        )

        updater.update(
            db_item,
            cast("ClientDownloadItem", {"status": "completed", "progress": 1.0}),
        )

        assert db_item.completed_at == existing

    def test_failure_sets_default_error_message_once(
        self, fixed_time: datetime, make_db_item: _DBItemFactory
    ) -> None:
        """Failure default message is set only when missing."""
        clock = _SequenceClock([fixed_time])
        mapper = MagicMock()
        mapper.map.return_value = DownloadItemStatus.FAILED
        updater = DownloadItemUpdater(status_mapper=mapper, clock=clock)

        db_item = make_db_item(status=DownloadItemStatus.QUEUED, error_message=None)
        updater.update(db_item, cast("ClientDownloadItem", {"status": "failed"}))
        assert db_item.error_message == "Download failed reported by client"

        # Do not override if already set
        db_item2 = make_db_item(
            status=DownloadItemStatus.QUEUED, error_message="custom"
        )
        updater.update(db_item2, cast("ClientDownloadItem", {"status": "failed"}))
        assert db_item2.error_message == "custom"

    def test_utc_now_is_timezone_aware(self) -> None:
        """utc_now returns an aware UTC datetime."""
        now = DownloadItemUpdater.utc_now()
        assert now.tzinfo is UTC


class TestDownloadReconciler:
    """Tests for `DownloadReconciler`."""

    def test_reconcile_matches_by_client_id_case_insensitive(self) -> None:
        """First-pass matching uses normalized client IDs."""
        matcher = MagicMock()
        matcher.build_lookup_maps.return_value = {}
        reconciler = DownloadReconciler(matcher=matcher)

        db_item = DBDownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="abc",
            title="t",
            download_url="magnet:...",
        )
        db_items = [db_item]
        client_items: list[ClientDownloadItem] = [
            {"client_item_id": "ABC", "title": "t", "status": "downloading"}
        ]

        result = reconciler.reconcile(db_items, client_items)

        assert result.matched_pairs == [(db_items[0], client_items[0])]
        assert result.unmatched_db_items == []
        assert result.unmatched_client_items == []

    def test_reconcile_matches_pending_items_via_matcher(self) -> None:
        """Second-pass matching resolves PENDING DB items via matcher."""
        pending = DBDownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="PENDING",
            title="p",
            download_url="magnet:...",
        )
        other = DBDownloadItem(
            id=2,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="zzz",
            title="o",
            download_url="magnet:...",
        )
        db_items = [pending, other]
        client_item: ClientDownloadItem = {
            "client_item_id": "new",
            "title": "Some Title",
            "status": "downloading",
            "comment": "c",
            "size_bytes": 10,
        }
        client_items = [client_item]

        matcher = MagicMock()
        maps = object()
        matcher.build_lookup_maps.return_value = maps
        matcher.find_match.return_value = pending

        reconciler = DownloadReconciler(matcher=matcher)
        result = reconciler.reconcile(db_items, client_items)

        assert (pending, client_item) in result.matched_pairs
        assert other in result.unmatched_db_items
        assert result.unmatched_client_items == []
        matcher.find_match.assert_called()

    def test_reconcile_keeps_client_item_unmatched_if_match_not_pending(self) -> None:
        """Matcher results are only applied to PENDING DB items."""
        pending = DBDownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="PENDING",
            title="p",
            download_url="magnet:...",
        )
        db_items = [pending]
        client_item: ClientDownloadItem = {
            "client_item_id": "new",
            "title": "Some Title",
            "status": "downloading",
        }
        client_items = [client_item]

        matcher = MagicMock()
        matcher.build_lookup_maps.return_value = object()
        matcher.find_match.return_value = DBDownloadItem(
            id=999,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="OTHER",
            title="x",
            download_url="magnet:...",
        )

        reconciler = DownloadReconciler(matcher=matcher)
        result = reconciler.reconcile(db_items, client_items)

        assert result.matched_pairs == []
        assert result.unmatched_db_items == [pending]
        assert result.unmatched_client_items == [client_item]

    def test_create_search_result_includes_infohash_and_comment(self) -> None:
        """Search result includes infohash/comment in additional_info when present."""
        matcher = MagicMock()
        reconciler = DownloadReconciler(matcher=matcher)
        client_item: ClientDownloadItem = {
            "client_item_id": "abc",
            "title": "T",
            "status": "downloading",
            "comment": "hello",
        }

        result = reconciler._create_search_result(client_item)

        assert result.release.title == "T"
        assert result.release.additional_info == {"infohash": "abc", "comment": "hello"}
        assert result.indexer_name == "Client"

    def test_normalize_id_uppercases(self) -> None:
        """Normalization uses uppercasing."""
        assert DownloadReconciler._normalize_id("aBc") == "ABC"


class TestSQLModelDownloadItemRepository:
    """Tests for `SQLModelDownloadItemRepository`."""

    def test_repository_crud_and_queries(self, session: DummySession) -> None:
        """Repository delegates to session for CRUD and query operations."""
        repo = SQLModelDownloadItemRepository(cast("Session", session))
        item = DBDownloadItem(
            id=1,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="hash",
            title="Title",
            download_url="magnet:...",
            status=DownloadItemStatus.DOWNLOADING,
        )

        repo.add(item)
        assert item in session.added

        session.set_get_result(DBDownloadItem, item)
        assert repo.get(1) is item

        session.add_exec_result([item])
        assert list(repo.get_active()) == [item]

        session.add_exec_result([item])
        assert list(repo.get_history(limit=5, offset=2)) == [item]

        session.add_exec_result([item])
        assert list(repo.get_by_tracked_book(1)) == [item]

        session.add_exec_result([item])
        assert repo.get_latest_by_url_and_tracked_book(1, "magnet:...") is item

        session.add_exec_result([item])
        assert list(repo.get_by_client(1)) == [item]

        repo.update(item)
        assert session.added.count(item) >= 2  # add called by add() and update()

        repo.commit()
        assert session.commit_count == 1

        repo.refresh(item)
        assert item in session.refreshed
