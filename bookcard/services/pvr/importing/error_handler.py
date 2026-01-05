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

"""Error handling for PVR import."""

import logging
from typing import Protocol

from bookcard.models.pvr import (
    DownloadItem,
    TrackedBookStatus,
)
from bookcard.services.pvr.importing.protocols import SessionFactory

logger = logging.getLogger(__name__)


class ImportErrorHandler(Protocol):
    """Protocol for import error handler."""

    def handle(self, error: Exception, download_item: DownloadItem) -> None:
        """Handle import error.

        Parameters
        ----------
        error : Exception
            The error that occurred.
        download_item : DownloadItem
            The download item involved.
        """
        ...


class DefaultImportErrorHandler:
    """Default implementation of import error handler."""

    def __init__(self, session_factory: SessionFactory) -> None:
        """Initialize handler."""
        self._session_factory = session_factory

    def handle(self, error: Exception, download_item: DownloadItem) -> None:
        """Handle import error safely in a new transaction.

        Uses a new session to avoid detached instance issues after
        the main transaction rollback.
        """
        if not download_item.id:
            logger.error(
                "Cannot record error for download item with no ID. Error: %s", error
            )
            return

        item_id = download_item.id
        error_msg = str(error)

        try:
            with self._session_factory.create_session() as session:
                item = session.get(DownloadItem, item_id)
                if item:
                    item.error_message = error_msg
                    item.tracked_book.status = TrackedBookStatus.FAILED
                    item.tracked_book.error_message = f"Import failed: {error_msg}"

                    session.add(item)
                    session.add(item.tracked_book)
                    session.commit()
        except Exception:
            logger.exception(
                "Failed to record import error for item %d. Original error: %s",
                item_id,
                error_msg,
            )
