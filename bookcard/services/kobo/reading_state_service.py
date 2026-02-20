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

"""Kobo reading state service.

Manages Kobo reading states (bookmarks, statistics, status) and syncs
with the main ReadingProgress model.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from bookcard.models.kobo import (
    KoboBookmark,
    KoboReadingState,
    KoboStatistics,
)
from bookcard.models.reading import ReadStatus, ReadStatusEnum

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.repositories.kobo_repository import KoboReadingStateRepository
    from bookcard.repositories.reading_repository import ReadStatusRepository
    from bookcard.services.reading_service import ReadingService


class KoboReadingStateService:
    """Service for managing Kobo reading states.

    Handles creation, updates, and synchronization of Kobo-specific
    reading states with the main reading progress tracking.

    Parameters
    ----------
    session : Session
        Database session.
    reading_state_repo : KoboReadingStateRepository
        Repository for Kobo reading states.
    read_status_repo : ReadStatusRepository
        Repository for read status.
    reading_service : ReadingService
        Service for main reading progress.
    """

    def __init__(
        self,
        session: Session,
        reading_state_repo: KoboReadingStateRepository,
        read_status_repo: ReadStatusRepository,
        reading_service: ReadingService,
    ) -> None:
        self._session = session
        self._reading_state_repo = reading_state_repo
        self._read_status_repo = read_status_repo
        self._reading_service = reading_service

    def get_or_create_reading_state(
        self, user_id: int, book_id: int, library_id: int | None = None
    ) -> KoboReadingState:
        """Get or create reading state for a user/book/library.

        Parameters
        ----------
        user_id : int
            User ID.
        book_id : int
            Book ID.
        library_id : int | None
            Library ID.  When provided the lookup is scoped to the
            specific library; otherwise falls back to a legacy
            library-unaware lookup.

        Returns
        -------
        KoboReadingState
            Reading state (existing or newly created).
        """
        if library_id is not None:
            reading_state = self._reading_state_repo.find_by_user_library_and_book(
                user_id, library_id, book_id
            )
        else:
            reading_state = self._reading_state_repo.find_by_user_and_book(
                user_id, book_id
            )

        if reading_state:
            return reading_state

        # Create new reading state
        reading_state = KoboReadingState(
            user_id=user_id,
            book_id=book_id,
            library_id=library_id or 0,
        )
        self._reading_state_repo.add(reading_state)
        self._session.flush()

        # Create bookmark and statistics
        bookmark = KoboBookmark(reading_state_id=reading_state.id or 0)
        statistics = KoboStatistics(reading_state_id=reading_state.id or 0)
        reading_state.current_bookmark = bookmark
        reading_state.statistics = statistics
        self._session.flush()

        return reading_state

    def update_reading_state(
        self,
        user_id: int,
        book_id: int,
        library_id: int,
        state_data: dict[str, object],
    ) -> dict[str, object]:
        """Update reading state from device.

        Parameters
        ----------
        user_id : int
            User ID.
        book_id : int
            Book ID.
        library_id : int
            Library ID.
        state_data : dict[str, object]
            Reading state data from device.

        Returns
        -------
        dict[str, object]
            Update results dictionary.
        """
        reading_state = self.get_or_create_reading_state(
            user_id, book_id, library_id=library_id
        )
        update_results: dict[str, object] = {"EntitlementId": str(book_id)}

        if "CurrentBookmark" in state_data:
            self._update_bookmark(
                reading_state,
                state_data["CurrentBookmark"],
                user_id,
                library_id,
                book_id,
                update_results,
            )

        if "Statistics" in state_data:
            self._update_statistics(
                reading_state, state_data["Statistics"], update_results
            )

        if "StatusInfo" in state_data:
            self._update_status_info(
                state_data["StatusInfo"],
                user_id,
                library_id,
                book_id,
                update_results,
            )

        reading_state.last_modified = datetime.now(UTC)
        reading_state.priority_timestamp = datetime.now(UTC)
        self._session.flush()

        return update_results

    def _update_bookmark(
        self,
        reading_state: KoboReadingState,
        bookmark_data: object,
        user_id: int,
        library_id: int,
        book_id: int,
        update_results: dict[str, object],
    ) -> None:
        """Update bookmark from state data.

        Parameters
        ----------
        reading_state : KoboReadingState
            Reading state to update.
        bookmark_data : object
            Bookmark data from device.
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        update_results : dict[str, object]
            Update results dictionary to modify.
        """
        if not bookmark_data or not isinstance(bookmark_data, dict):
            return

        if reading_state.current_bookmark is None:
            reading_state.current_bookmark = KoboBookmark(
                reading_state_id=reading_state.id or 0
            )
        bookmark = reading_state.current_bookmark

        if "ProgressPercent" in bookmark_data:
            progress = bookmark_data["ProgressPercent"]
            if isinstance(progress, (int, float)):
                bookmark.progress_percent = float(progress)

        if "ContentSourceProgressPercent" in bookmark_data:
            content_progress = bookmark_data["ContentSourceProgressPercent"]
            if isinstance(content_progress, (int, float)):
                bookmark.content_source_progress_percent = float(content_progress)

        if "Location" in bookmark_data:
            location = bookmark_data["Location"]
            if isinstance(location, dict):
                bookmark.location_value = location.get("Value")
                bookmark.location_type = location.get("Type")
                bookmark.location_source = location.get("Source")

        bookmark.last_modified = datetime.now(UTC)
        update_results["CurrentBookmarkResult"] = {"Result": "Success"}

        if bookmark.progress_percent is not None:
            self._sync_to_reading_progress(
                user_id,
                library_id,
                book_id,
                bookmark.progress_percent / 100.0,
                bookmark.location_value,
            )

    def _update_statistics(
        self,
        reading_state: KoboReadingState,
        stats_data: object,
        update_results: dict[str, object],
    ) -> None:
        """Update statistics from state data.

        Parameters
        ----------
        reading_state : KoboReadingState
            Reading state to update.
        stats_data : object
            Statistics data from device.
        update_results : dict[str, object]
            Update results dictionary to modify.
        """
        if not stats_data or not isinstance(stats_data, dict):
            return

        if reading_state.statistics is None:
            reading_state.statistics = KoboStatistics(
                reading_state_id=reading_state.id or 0
            )
        statistics = reading_state.statistics

        if "SpentReadingMinutes" in stats_data:
            minutes = stats_data["SpentReadingMinutes"]
            if isinstance(minutes, (int, float)):
                statistics.spent_reading_minutes = int(minutes)

        if "RemainingTimeMinutes" in stats_data:
            minutes = stats_data["RemainingTimeMinutes"]
            if isinstance(minutes, (int, float)):
                statistics.remaining_time_minutes = int(minutes)

        statistics.last_modified = datetime.now(UTC)
        update_results["StatisticsResult"] = {"Result": "Success"}

    def _update_status_info(
        self,
        status_data: object,
        user_id: int,
        library_id: int,
        book_id: int,
        update_results: dict[str, object],
    ) -> None:
        """Update status info from state data.

        Parameters
        ----------
        status_data : object
            Status data from device.
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        update_results : dict[str, object]
            Update results dictionary to modify.
        """
        if not status_data or not isinstance(status_data, dict):
            return

        # After isinstance check, access dict directly
        if "Status" not in status_data:
            return
        status_value = status_data["Status"]
        status_str = status_value if isinstance(status_value, str) else None
        if not status_str:
            return

        read_status = self._get_or_create_read_status(user_id, library_id, book_id)
        new_status = self._get_ub_read_status(status_str)
        if new_status is not None:
            read_status.status = new_status
            read_status.updated_at = datetime.now(UTC)
            update_results["StatusInfoResult"] = {"Result": "Success"}

    def _sync_to_reading_progress(
        self,
        user_id: int,
        library_id: int,
        book_id: int,
        progress: float,
        cfi: str | None = None,
    ) -> None:
        """Sync Kobo reading state to main reading progress.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.
        progress : float
            Progress as fraction (0.0 to 1.0).
        cfi : str | None
            Optional CFI location.
        """
        # Use EPUB format for Kobo (most common)
        self._reading_service.update_progress(
            user_id=user_id,
            library_id=library_id,
            book_id=book_id,
            book_format="EPUB",
            progress=progress,
            cfi=cfi,
            device="kobo",
        )

    def _get_or_create_read_status(
        self, user_id: int, library_id: int, book_id: int
    ) -> ReadStatus:
        """Get or create read status.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_id : int
            Book ID.

        Returns
        -------
        ReadStatus
            Read status.
        """
        find_method = getattr(self._read_status_repo, "find_by_user_library_book", None)
        if find_method is None:
            msg = "ReadStatusRepository missing find_by_user_library_book method"
            raise AttributeError(msg)
        read_status = find_method(user_id, library_id, book_id)
        if read_status:
            return read_status

        read_status = ReadStatus(
            user_id=user_id,
            library_id=library_id,
            book_id=book_id,
            status=ReadStatusEnum.NOT_READ,
        )
        self._read_status_repo.add(read_status)
        self._session.flush()
        return read_status

    def _get_ub_read_status(self, kobo_status: str) -> ReadStatusEnum | None:
        """Convert Kobo status string to ReadStatusEnum.

        Parameters
        ----------
        kobo_status : str
            Kobo status string.

        Returns
        -------
        ReadStatusEnum | None
            Read status enum or None.
        """
        status_map: dict[str, ReadStatusEnum] = {
            "ReadyToRead": ReadStatusEnum.NOT_READ,
            "Finished": ReadStatusEnum.READ,
            "Reading": ReadStatusEnum.READING,
        }
        return status_map.get(kobo_status)
