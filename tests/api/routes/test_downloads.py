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

"""Tests for download routes."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import status

from bookcard.api.routes import downloads
from bookcard.models.pvr import DownloadItem, DownloadItemStatus
from bookcard.services.download_service import DownloadService
from bookcard.services.pvr_import_service import PVRImportService
from tests.conftest import DummySession


@pytest.fixture
def mock_download_service(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock DownloadService."""
    mock = MagicMock(spec=DownloadService)
    monkeypatch.setattr(downloads, "get_download_service", lambda session: mock)
    return mock


@pytest.fixture
def mock_import_service(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock PVRImportService."""
    mock = MagicMock(spec=PVRImportService)
    monkeypatch.setattr(downloads, "get_import_service", lambda session: mock)
    return mock


def test_get_queue(
    mock_download_service: MagicMock,
    session: DummySession,
) -> None:
    """Test getting download queue.

    Parameters
    ----------
    mock_download_service : MagicMock
        Mock download service.
    session : DummySession
        Dummy database session.
    """
    mock_items = [
        DownloadItem(
            id=1,
            title="Book 1",
            status=DownloadItemStatus.DOWNLOADING,
            tracked_book_id=1,
            download_client_id=1,
            client_item_id="123",
            download_url="http://example.com/1.torrent",
        ),
        DownloadItem(
            id=2,
            title="Book 2",
            status=DownloadItemStatus.QUEUED,
            tracked_book_id=2,
            download_client_id=1,
            client_item_id="456",
            download_url="http://example.com/2.torrent",
        ),
    ]
    mock_download_service.get_active_downloads.return_value = mock_items

    result = downloads.get_queue(service=mock_download_service)

    assert result.total_count == 2
    assert len(result.items) == 2
    assert result.items[0].id == 1
    assert result.items[1].id == 2
    mock_download_service.get_active_downloads.assert_called_once()


def test_get_history(
    mock_download_service: MagicMock,
    session: DummySession,
) -> None:
    """Test getting download history.

    Parameters
    ----------
    mock_download_service : MagicMock
        Mock download service.
    session : DummySession
        Dummy database session.
    """
    mock_items = [
        DownloadItem(
            id=3,
            title="Book 3",
            status=DownloadItemStatus.COMPLETED,
            tracked_book_id=3,
            download_client_id=1,
            client_item_id="789",
            download_url="http://example.com/3.torrent",
            completed_at=datetime.now(UTC),
        )
    ]
    mock_download_service.get_download_history.return_value = mock_items

    result = downloads.get_history(service=mock_download_service, limit=50, offset=10)

    assert result.total_count == 1
    assert len(result.items) == 1
    assert result.items[0].id == 3
    mock_download_service.get_download_history.assert_called_once_with(50, 10)


def test_cancel_download_success(
    mock_download_service: MagicMock,
    session: DummySession,
) -> None:
    """Test successfully cancelling a download.

    Parameters
    ----------
    mock_download_service : MagicMock
        Mock download service.
    session : DummySession
        Dummy database session.
    """
    mock_item = DownloadItem(
        id=1,
        title="Book 1",
        status=DownloadItemStatus.REMOVED,
        tracked_book_id=1,
        download_client_id=1,
        client_item_id="123",
        download_url="http://example.com/1.torrent",
        error_message="Cancelled by user",
    )
    mock_download_service.cancel_download.return_value = mock_item

    # Since cancel_download now returns None in the route, we verify the call
    downloads.cancel_download(item_id=1, service=mock_download_service)

    mock_download_service.cancel_download.assert_called_once_with(1)


def test_cancel_download_not_found(
    mock_download_service: MagicMock,
    session: DummySession,
) -> None:
    """Test cancelling non-existent download.

    Parameters
    ----------
    mock_download_service : MagicMock
        Mock download service.
    session : DummySession
        Dummy database session.
    """
    mock_download_service.cancel_download.side_effect = ValueError(
        "Download item 999 not found"
    )

    with pytest.raises(downloads.HTTPException) as exc:
        downloads.cancel_download(item_id=999, service=mock_download_service)

    # Type check ignore as these attributes exist on HTTPException but mypy/pyright
    # might infer BaseException which doesn't have them
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]
    assert exc.value.detail == "Download item not found or cannot be cancelled"  # type: ignore[attr-defined]


def test_retry_download_success(
    mock_import_service: MagicMock,
    session: DummySession,
) -> None:
    """Test successful retry download.

    Parameters
    ----------
    mock_import_service : MagicMock
        Mock import service.
    session : DummySession
        Dummy database session.
    """
    mock_item = MagicMock(spec=DownloadItem)
    session.get = MagicMock(return_value=mock_item)  # type: ignore[assignment]

    # Mock success result
    mock_result = MagicMock()
    mock_result.is_success = True
    mock_import_service.process_completed_download.return_value = mock_result

    result = downloads.retry_download(
        item_id=1, session=session, service=mock_import_service
    )

    assert result == {"status": "success", "message": "Download imported successfully"}
    mock_import_service.process_completed_download.assert_called_once_with(mock_item)


def test_retry_download_not_found(
    mock_import_service: MagicMock,
    session: DummySession,
) -> None:
    """Test retry download for non-existent item.

    Parameters
    ----------
    mock_import_service : MagicMock
        Mock import service.
    session : DummySession
        Dummy database session.
    """
    session.get = MagicMock(return_value=None)  # type: ignore[assignment]

    with pytest.raises(downloads.HTTPException) as exc:
        downloads.retry_download(
            item_id=999, session=session, service=mock_import_service
        )

    # Type check ignore as these attributes exist on HTTPException but mypy/pyright
    # might infer BaseException which doesn't have them
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND  # type: ignore[attr-defined]
    assert exc.value.detail == "Download item not found"  # type: ignore[attr-defined]
    mock_import_service.process_completed_download.assert_not_called()


def test_retry_download_failure(
    mock_import_service: MagicMock,
    session: DummySession,
) -> None:
    """Test retry download failure handling.

    Parameters
    ----------
    mock_import_service : MagicMock
        Mock import service.
    session : DummySession
        Dummy database session.
    """
    mock_item = MagicMock(spec=DownloadItem)
    session.get = MagicMock(return_value=mock_item)  # type: ignore[assignment]

    # Mock failure result
    mock_result = MagicMock()
    mock_result.is_success = False
    mock_result.error_message = "Import error"
    mock_import_service.process_completed_download.return_value = mock_result

    with pytest.raises(downloads.HTTPException) as exc:
        downloads.retry_download(
            item_id=1, session=session, service=mock_import_service
        )

    # Type check ignore as these attributes exist on HTTPException but mypy/pyright
    # might infer BaseException which doesn't have them
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR  # type: ignore[attr-defined]
    assert "Import failed: Import error" in exc.value.detail  # type: ignore[attr-defined]
