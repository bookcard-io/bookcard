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

"""Tests for KoboReadingStateService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from fundamental.models.kobo import KoboBookmark, KoboReadingState
from fundamental.models.reading import ReadStatus, ReadStatusEnum
from fundamental.services.kobo.reading_state_service import KoboReadingStateService
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session for testing.

    Returns
    -------
    DummySession
        Dummy session instance.
    """
    return DummySession()


@pytest.fixture
def mock_reading_state_repo() -> MagicMock:
    """Create a mock KoboReadingStateRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    repo = MagicMock()
    repo.find_by_user_and_book = MagicMock(return_value=None)
    return repo


@pytest.fixture
def mock_read_status_repo() -> MagicMock:
    """Create a mock ReadStatusRepository.

    Returns
    -------
    MagicMock
        Mock repository instance.
    """
    repo = MagicMock()
    repo.find_by_user_library_book = MagicMock(return_value=None)
    repo.add = MagicMock()
    return repo


@pytest.fixture
def mock_reading_service() -> MagicMock:
    """Create a mock ReadingService.

    Returns
    -------
    MagicMock
        Mock service instance.
    """
    service = MagicMock()
    service.update_progress = MagicMock()
    return service


@pytest.fixture
def reading_state_service(
    session: DummySession,
    mock_reading_state_repo: MagicMock,
    mock_read_status_repo: MagicMock,
    mock_reading_service: MagicMock,
) -> KoboReadingStateService:
    """Create KoboReadingStateService instance for testing.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    mock_reading_service : MagicMock
        Mock reading service.

    Returns
    -------
    KoboReadingStateService
        Service instance.
    """
    return KoboReadingStateService(
        session,  # type: ignore[arg-type]
        mock_reading_state_repo,
        mock_read_status_repo,
        mock_reading_service,
    )


@pytest.fixture
def reading_state() -> KoboReadingState:
    """Create a test reading state.

    Returns
    -------
    KoboReadingState
        Reading state instance.
    """
    return KoboReadingState(id=1, user_id=1, book_id=1, last_modified=datetime.now(UTC))


# ============================================================================
# Tests for KoboReadingStateService.__init__
# ============================================================================


def test_init(
    session: DummySession,
    mock_reading_state_repo: MagicMock,
    mock_read_status_repo: MagicMock,
    mock_reading_service: MagicMock,
) -> None:
    """Test KoboReadingStateService initialization.

    Parameters
    ----------
    session : DummySession
        Dummy session instance.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    mock_reading_service : MagicMock
        Mock reading service.
    """
    service = KoboReadingStateService(
        session,  # type: ignore[arg-type]
        mock_reading_state_repo,
        mock_read_status_repo,
        mock_reading_service,
    )
    assert service._session == session
    assert service._reading_state_repo == mock_reading_state_repo
    assert service._read_status_repo == mock_read_status_repo
    assert service._reading_service == mock_reading_service


# ============================================================================
# Tests for KoboReadingStateService.get_or_create_reading_state
# ============================================================================


def test_get_or_create_reading_state_existing(
    reading_state_service: KoboReadingStateService,
    reading_state: KoboReadingState,
) -> None:
    """Test getting existing reading state.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    reading_state : KoboReadingState
        Test reading state.
    """
    reading_state_service._reading_state_repo.find_by_user_and_book.return_value = (  # type: ignore[assignment]
        reading_state
    )

    result = reading_state_service.get_or_create_reading_state(user_id=1, book_id=1)

    assert result == reading_state
    reading_state_service._reading_state_repo.find_by_user_and_book.assert_called_once_with(  # type: ignore[attr-defined]
        1, 1
    )


def test_get_or_create_reading_state_new(
    reading_state_service: KoboReadingStateService,
    mock_reading_state_repo: MagicMock,
    session: DummySession,
) -> None:
    """Test creating new reading state.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    session : DummySession
        Dummy session instance.
    """
    mock_reading_state_repo.find_by_user_and_book.return_value = None
    mock_reading_state_repo.add = MagicMock()

    result = reading_state_service.get_or_create_reading_state(user_id=1, book_id=1)

    assert result is not None
    assert result.user_id == 1
    assert result.book_id == 1
    assert result.current_bookmark is not None
    assert result.statistics is not None
    assert (
        session.flush_count >= 2
    )  # Once for reading_state, once for bookmark/statistics


# ============================================================================
# Tests for KoboReadingStateService.update_reading_state
# ============================================================================


def test_update_reading_state_with_bookmark(
    reading_state_service: KoboReadingStateService,
    mock_reading_state_repo: MagicMock,
    reading_state: KoboReadingState,
    session: DummySession,
) -> None:
    """Test updating reading state with bookmark.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    reading_state : KoboReadingState
        Test reading state.
    session : DummySession
        Dummy session instance.
    """
    mock_reading_state_repo.find_by_user_and_book.return_value = reading_state
    state_data = {
        "CurrentBookmark": {
            "ProgressPercent": 50.0,
            "Location": {"Value": "epubcfi(/6/4)", "Type": "CFI"},
        }
    }

    result = reading_state_service.update_reading_state(
        user_id=1, book_id=1, library_id=1, state_data=state_data
    )

    assert result["EntitlementId"] == "1"
    assert "CurrentBookmarkResult" in result
    assert session.flush_count > 0


def test_update_reading_state_with_statistics(
    reading_state_service: KoboReadingStateService,
    mock_reading_state_repo: MagicMock,
    reading_state: KoboReadingState,
) -> None:
    """Test updating reading state with statistics.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    reading_state : KoboReadingState
        Test reading state.
    """
    mock_reading_state_repo.find_by_user_and_book.return_value = reading_state
    state_data = {
        "Statistics": {
            "SpentReadingMinutes": 120,
            "RemainingTimeMinutes": 60,
        }
    }

    result = reading_state_service.update_reading_state(
        user_id=1, book_id=1, library_id=1, state_data=state_data
    )

    assert "StatisticsResult" in result


def test_update_reading_state_with_status_info(
    reading_state_service: KoboReadingStateService,
    mock_reading_state_repo: MagicMock,
    mock_read_status_repo: MagicMock,
    reading_state: KoboReadingState,
) -> None:
    """Test updating reading state with status info.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_reading_state_repo : MagicMock
        Mock reading state repository.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    reading_state : KoboReadingState
        Test reading state.
    """
    mock_reading_state_repo.find_by_user_and_book.return_value = reading_state
    read_status = ReadStatus(
        id=1, user_id=1, library_id=1, book_id=1, status=ReadStatusEnum.NOT_READ
    )
    mock_read_status_repo.find_by_user_library_book.return_value = read_status
    state_data = {"StatusInfo": {"Status": "Reading"}}

    result = reading_state_service.update_reading_state(
        user_id=1, book_id=1, library_id=1, state_data=state_data
    )

    assert "StatusInfoResult" in result


# ============================================================================
# Tests for KoboReadingStateService._update_bookmark
# ============================================================================


def test_update_bookmark_new(
    reading_state_service: KoboReadingStateService,
    reading_state: KoboReadingState,
    mock_reading_service: MagicMock,
) -> None:
    """Test updating bookmark when bookmark doesn't exist.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    reading_state : KoboReadingState
        Test reading state.
    mock_reading_service : MagicMock
        Mock reading service.
    """
    reading_state.current_bookmark = None
    bookmark_data = {
        "ProgressPercent": 50.0,
        "ContentSourceProgressPercent": 45.0,
        "Location": {
            "Value": "epubcfi(/6/4)",
            "Type": "CFI",
            "Source": "kobo",
        },
    }
    update_results: dict[str, object] = {}

    reading_state_service._update_bookmark(
        reading_state,
        bookmark_data,
        user_id=1,
        library_id=1,
        book_id=1,
        update_results=update_results,
    )

    assert reading_state.current_bookmark is not None
    assert reading_state.current_bookmark.progress_percent == 50.0
    assert "CurrentBookmarkResult" in update_results
    mock_reading_service.update_progress.assert_called_once()


def test_update_bookmark_invalid_data(
    reading_state_service: KoboReadingStateService,
    reading_state: KoboReadingState,
) -> None:
    """Test updating bookmark with invalid data.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    reading_state : KoboReadingState
        Test reading state.
    """
    update_results: dict[str, object] = {}

    reading_state_service._update_bookmark(
        reading_state,
        None,
        user_id=1,
        library_id=1,
        book_id=1,
        update_results=update_results,
    )

    assert "CurrentBookmarkResult" not in update_results


def test_update_bookmark_no_progress(
    reading_state_service: KoboReadingStateService,
    reading_state: KoboReadingState,
) -> None:
    """Test updating bookmark without progress.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    reading_state : KoboReadingState
        Test reading state.
    """
    bookmark = KoboBookmark(reading_state_id=1)
    reading_state.current_bookmark = bookmark
    bookmark_data = {"Location": {"Value": "epubcfi(/6/4)"}}
    update_results: dict[str, object] = {}

    reading_state_service._update_bookmark(
        reading_state,
        bookmark_data,
        user_id=1,
        library_id=1,
        book_id=1,
        update_results=update_results,
    )

    assert "CurrentBookmarkResult" in update_results


# ============================================================================
# Tests for KoboReadingStateService._update_statistics
# ============================================================================


def test_update_statistics_new(
    reading_state_service: KoboReadingStateService,
    reading_state: KoboReadingState,
) -> None:
    """Test updating statistics when statistics don't exist.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    reading_state : KoboReadingState
        Test reading state.
    """
    reading_state.statistics = None
    stats_data = {
        "SpentReadingMinutes": 120,
        "RemainingTimeMinutes": 60,
    }
    update_results: dict[str, object] = {}

    reading_state_service._update_statistics(reading_state, stats_data, update_results)

    assert reading_state.statistics is not None
    assert reading_state.statistics.spent_reading_minutes == 120
    assert "StatisticsResult" in update_results


def test_update_statistics_invalid_data(
    reading_state_service: KoboReadingStateService,
    reading_state: KoboReadingState,
) -> None:
    """Test updating statistics with invalid data.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    reading_state : KoboReadingState
        Test reading state.
    """
    update_results: dict[str, object] = {}

    reading_state_service._update_statistics(reading_state, None, update_results)

    assert "StatisticsResult" not in update_results


# ============================================================================
# Tests for KoboReadingStateService._update_status_info
# ============================================================================


def test_update_status_info_success(
    reading_state_service: KoboReadingStateService,
    mock_read_status_repo: MagicMock,
) -> None:
    """Test updating status info successfully.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    """
    read_status = ReadStatus(
        id=1, user_id=1, library_id=1, book_id=1, status=ReadStatusEnum.NOT_READ
    )
    mock_read_status_repo.find_by_user_library_book.return_value = read_status
    status_data = {"Status": "Reading"}
    update_results: dict[str, object] = {}

    reading_state_service._update_status_info(
        status_data, user_id=1, library_id=1, book_id=1, update_results=update_results
    )

    assert read_status.status == ReadStatusEnum.READING
    assert "StatusInfoResult" in update_results


def test_update_status_info_invalid_data(
    reading_state_service: KoboReadingStateService,
) -> None:
    """Test updating status info with invalid data.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    """
    update_results: dict[str, object] = {}

    reading_state_service._update_status_info(
        None, user_id=1, library_id=1, book_id=1, update_results=update_results
    )

    assert "StatusInfoResult" not in update_results


def test_update_status_info_no_status_key(
    reading_state_service: KoboReadingStateService,
) -> None:
    """Test updating status info without Status key.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    """
    status_data = {}
    update_results: dict[str, object] = {}

    reading_state_service._update_status_info(
        status_data, user_id=1, library_id=1, book_id=1, update_results=update_results
    )

    assert "StatusInfoResult" not in update_results


def test_update_status_info_non_string_status(
    reading_state_service: KoboReadingStateService,
    mock_read_status_repo: MagicMock,
) -> None:
    """Test updating status info with non-string status.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    """
    read_status = ReadStatus(
        id=1, user_id=1, library_id=1, book_id=1, status=ReadStatusEnum.NOT_READ
    )
    mock_read_status_repo.find_by_user_library_book.return_value = read_status
    status_data = {"Status": 123}
    update_results: dict[str, object] = {}

    reading_state_service._update_status_info(
        status_data, user_id=1, library_id=1, book_id=1, update_results=update_results
    )

    assert "StatusInfoResult" not in update_results


# ============================================================================
# Tests for KoboReadingStateService._sync_to_reading_progress
# ============================================================================


def test_sync_to_reading_progress(
    reading_state_service: KoboReadingStateService,
    mock_reading_service: MagicMock,
) -> None:
    """Test syncing to reading progress.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_reading_service : MagicMock
        Mock reading service.
    """
    reading_state_service._sync_to_reading_progress(
        user_id=1, library_id=1, book_id=1, progress=0.5, cfi="epubcfi(/6/4)"
    )

    mock_reading_service.update_progress.assert_called_once_with(
        user_id=1,
        library_id=1,
        book_id=1,
        book_format="EPUB",
        progress=0.5,
        cfi="epubcfi(/6/4)",
        device="kobo",
    )


# ============================================================================
# Tests for KoboReadingStateService._get_or_create_read_status
# ============================================================================


def test_get_or_create_read_status_existing(
    reading_state_service: KoboReadingStateService,
    mock_read_status_repo: MagicMock,
) -> None:
    """Test getting existing read status.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    """
    read_status = ReadStatus(
        id=1, user_id=1, library_id=1, book_id=1, status=ReadStatusEnum.NOT_READ
    )
    mock_read_status_repo.find_by_user_library_book.return_value = read_status

    result = reading_state_service._get_or_create_read_status(
        user_id=1, library_id=1, book_id=1
    )

    assert result == read_status


def test_get_or_create_read_status_new(
    reading_state_service: KoboReadingStateService,
    mock_read_status_repo: MagicMock,
    session: DummySession,
) -> None:
    """Test creating new read status.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    session : DummySession
        Dummy session instance.
    """
    mock_read_status_repo.find_by_user_library_book.return_value = None

    result = reading_state_service._get_or_create_read_status(
        user_id=1, library_id=1, book_id=1
    )

    assert result is not None
    assert result.user_id == 1
    assert result.library_id == 1
    assert result.book_id == 1
    assert result.status == ReadStatusEnum.NOT_READ
    assert session.flush_count > 0


def test_get_or_create_read_status_missing_method(
    reading_state_service: KoboReadingStateService,
    mock_read_status_repo: MagicMock,
) -> None:
    """Test getting read status when method is missing.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    mock_read_status_repo : MagicMock
        Mock read status repository.
    """
    delattr(mock_read_status_repo, "find_by_user_library_book")

    with pytest.raises(
        AttributeError, match="missing find_by_user_library_book method"
    ):
        reading_state_service._get_or_create_read_status(
            user_id=1, library_id=1, book_id=1
        )


# ============================================================================
# Tests for KoboReadingStateService._get_ub_read_status
# ============================================================================


@pytest.mark.parametrize(
    ("kobo_status", "expected"),
    [
        ("ReadyToRead", ReadStatusEnum.NOT_READ),
        ("Finished", ReadStatusEnum.READ),
        ("Reading", ReadStatusEnum.READING),
        ("Unknown", None),
    ],
)
def test_get_ub_read_status(
    reading_state_service: KoboReadingStateService,
    kobo_status: str,
    expected: ReadStatusEnum | None,
) -> None:
    """Test converting Kobo status to ReadStatusEnum.

    Parameters
    ----------
    reading_state_service : KoboReadingStateService
        Service instance.
    kobo_status : str
        Kobo status string.
    expected : ReadStatusEnum | None
        Expected ReadStatusEnum.
    """
    result = reading_state_service._get_ub_read_status(kobo_status)
    assert result == expected
