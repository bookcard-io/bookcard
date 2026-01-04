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

"""Tracked book status update logic.

Handles propagating download status to tracked books.
"""

from bookcard.models.pvr import DownloadItemStatus, TrackedBook, TrackedBookStatus


class TrackedBookStatusUpdater:
    """Handles tracked book status updates from download events."""

    def update_from_download(
        self,
        tracked_book: TrackedBook,
        download_status: DownloadItemStatus,
        error_message: str | None = None,
    ) -> bool:
        """Update tracked book status from download status.

        Parameters
        ----------
        tracked_book : TrackedBook
            Tracked book to update.
        download_status : DownloadItemStatus
            Current status of the download.
        error_message : str | None
            Error message if failed.

        Returns
        -------
        bool
            True if status was changed, False otherwise.
        """
        if tracked_book.status in (
            TrackedBookStatus.COMPLETED,
            TrackedBookStatus.IGNORED,
        ):
            return False

        new_status = self._map_download_to_book_status(download_status)

        if new_status and tracked_book.status != new_status:
            tracked_book.status = new_status
            if error_message and new_status == TrackedBookStatus.FAILED:
                tracked_book.error_message = error_message
            return True

        return False

    def _map_download_to_book_status(
        self, download_status: DownloadItemStatus
    ) -> TrackedBookStatus | None:
        """Map download status to tracked book status."""
        if download_status == DownloadItemStatus.PAUSED:
            return TrackedBookStatus.PAUSED
        if download_status == DownloadItemStatus.STALLED:
            return TrackedBookStatus.STALLED
        if download_status == DownloadItemStatus.SEEDING:
            return TrackedBookStatus.SEEDING
        if download_status in (
            DownloadItemStatus.DOWNLOADING,
            DownloadItemStatus.QUEUED,
        ):
            return TrackedBookStatus.DOWNLOADING
        if download_status == DownloadItemStatus.FAILED:
            return TrackedBookStatus.FAILED

        return None
