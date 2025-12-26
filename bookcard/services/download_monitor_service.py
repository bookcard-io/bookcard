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

"""Download monitoring service.

This module provides the DownloadMonitorService which is responsible for:
- Polling all enabled download clients for status updates
- Updating the local database with current download progress and status
- Handling download completion and failure detection
- reconciling local download items with remote client state
"""

import logging
from datetime import UTC, datetime

from sqlmodel import Session, select

from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientStatus,
    DownloadItem,
    DownloadItemStatus,
    TrackedBookStatus,
)
from bookcard.pvr.base.interfaces import DownloadTracker
from bookcard.pvr.factory.download_client_factory import create_download_client
from bookcard.pvr.models import DownloadItem as ClientDownloadItem

logger = logging.getLogger(__name__)


class DownloadMonitorService:
    """Service for monitoring download clients and updating local state.

    This service is designed to be run periodically (e.g., via a background task).
    It iterates through all enabled download clients, fetches their active downloads,
    and updates the corresponding DownloadItem records in the database.
    """

    def __init__(self, session: Session) -> None:
        """Initialize service.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def check_downloads(self) -> None:
        """Check all enabled download clients for updates.

        Iterates through all enabled download clients, fetches their active items,
        and updates local database records. Handles connection errors by updating
        client status.
        """
        clients = self._get_enabled_clients()

        for client_def in clients:
            try:
                self._check_client(client_def)
            except Exception as e:
                logger.exception(
                    "Failed to check download client %s (id=%d)",
                    client_def.name,
                    client_def.id,
                )
                self._update_client_status(
                    client_def,
                    DownloadClientStatus.UNHEALTHY,
                    str(e),
                )

    def _get_enabled_clients(self) -> list[DownloadClientDefinition]:
        """Get all enabled download clients.

        Returns
        -------
        list[DownloadClientDefinition]
            List of enabled download clients.
        """
        stmt = select(DownloadClientDefinition).where(
            DownloadClientDefinition.enabled == True  # noqa: E712
        )
        return list(self.session.exec(stmt).all())

    def _check_client(self, client_def: DownloadClientDefinition) -> None:
        """Check a single download client.

        Parameters
        ----------
        client_def : DownloadClientDefinition
            Download client definition to check.
        """
        client = create_download_client(client_def)

        # Check if client supports tracking
        if not isinstance(client, DownloadTracker):
            logger.warning(
                "Download client %s (type=%s) does not support tracking",
                client_def.name,
                client_def.client_type,
            )
            return

        # Fetch items from client
        # Note: client.get_items() returns a Sequence of TypedDicts
        client_items = client.get_items()

        # Update client status to HEALTHY
        self._update_client_status(client_def, DownloadClientStatus.HEALTHY)

        # Process items
        self._process_client_items(client_def, list(client_items))

    def _update_client_status(
        self,
        client_def: DownloadClientDefinition,
        status: DownloadClientStatus,
        error_message: str | None = None,
    ) -> None:
        """Update download client status.

        Parameters
        ----------
        client_def : DownloadClientDefinition
            Client definition to update.
        status : DownloadClientStatus
            New status.
        error_message : str | None
            Error message if status is UNHEALTHY.
        """
        client_def.status = status
        client_def.last_checked_at = datetime.now(UTC)

        if status == DownloadClientStatus.HEALTHY:
            client_def.last_successful_connection_at = datetime.now(UTC)
            client_def.error_count = 0
            client_def.error_message = None
        else:
            client_def.error_count += 1
            client_def.error_message = error_message

        self.session.add(client_def)
        self.session.commit()

    def _process_client_items(
        self,
        client_def: DownloadClientDefinition,
        client_items: list[ClientDownloadItem],
    ) -> None:
        """Process items returned by the download client.

        Updates existing DownloadItems in the database and handles
        reconciliation (detecting removed items).

        Parameters
        ----------
        client_def : DownloadClientDefinition
            Download client definition.
        client_items : list[ClientDownloadItem]
            List of download items returned by the client.
        """
        # Strategy:
        # 1. Map client_items by hash (client_item_id)
        # 2. Iterate DB items for this client
        # 3. If DB item in client_items -> update
        # 4. If DB item NOT in client_items -> check if it was expected to be there.
        #    If it was downloading/queued, it might have been removed or finished.

        client_items_map = {
            item["client_item_id"].upper(): item for item in client_items
        }

        stmt = select(DownloadItem).where(
            DownloadItem.download_client_id == client_def.id
        )
        db_items = list(self.session.exec(stmt).all())

        for db_item in db_items:
            client_item_id = db_item.client_item_id.upper()

            if client_item_id in client_items_map:
                # Update existing item
                self._update_download_item(db_item, client_items_map[client_item_id])
                # Remove from map to track processed items
                del client_items_map[client_item_id]
            elif db_item.status not in (
                DownloadItemStatus.COMPLETED,
                DownloadItemStatus.FAILED,
                DownloadItemStatus.REMOVED,
            ):
                # Item exists in DB as active but not found in client
                # This could mean it was removed externally or completed and removed
                logger.warning(
                    "Download item %s (id=%d) not found in client %s. Marking as REMOVED.",
                    db_item.client_item_id,
                    db_item.id,
                    client_def.name,
                )
                db_item.status = DownloadItemStatus.REMOVED
                db_item.error_message = "Item removed from download client"
                self.session.add(db_item)

        self.session.commit()

    def _update_download_item(
        self,
        db_item: DownloadItem,
        client_item: ClientDownloadItem,
    ) -> None:
        """Update a database download item from client data.

        Parameters
        ----------
        db_item : DownloadItem
            Database record to update.
        client_item : ClientDownloadItem
            Data from download client.
        """
        # Update fields
        # Note: client_item["status"] returns string from pvr.utils.status.DownloadStatus
        # We need to ensure it matches DownloadItemStatus enum
        client_status_str = client_item.get("status", "unknown")
        db_item.status = self._map_status(client_status_str)
        db_item.progress = float(client_item.get("progress", 0.0))
        db_item.size_bytes = client_item.get("size_bytes")
        db_item.downloaded_bytes = client_item.get("downloaded_bytes")
        db_item.download_speed_bytes_per_sec = client_item.get(
            "download_speed_bytes_per_sec"
        )
        db_item.eta_seconds = client_item.get("eta_seconds")

        if client_item.get("file_path"):
            db_item.file_path = client_item["file_path"]

        # Check for completion
        if db_item.status == DownloadItemStatus.COMPLETED and not db_item.completed_at:
            db_item.completed_at = datetime.now(UTC)

            # Update TrackedBook status if linked
            if db_item.tracked_book:
                db_item.tracked_book.status = TrackedBookStatus.COMPLETED
                db_item.tracked_book.last_downloaded_at = datetime.now(UTC)
                self.session.add(db_item.tracked_book)

        # Check for failure
        if db_item.status == DownloadItemStatus.FAILED and not db_item.error_message:
            db_item.error_message = "Download failed reported by client"

            if db_item.tracked_book:
                db_item.tracked_book.status = TrackedBookStatus.FAILED
                db_item.tracked_book.error_message = db_item.error_message
                self.session.add(db_item.tracked_book)

        self.session.add(db_item)

    def _map_status(self, client_status: str) -> DownloadItemStatus:
        """Map client status string to DownloadItemStatus enum.

        Parameters
        ----------
        client_status : str
            Status string from download client adapter.

        Returns
        -------
        DownloadItemStatus
            Mapped status enum.
        """
        status_map = {
            "queued": DownloadItemStatus.QUEUED,
            "downloading": DownloadItemStatus.DOWNLOADING,
            "paused": DownloadItemStatus.PAUSED,
            "completed": DownloadItemStatus.COMPLETED,
            "failed": DownloadItemStatus.FAILED,
            "removed": DownloadItemStatus.REMOVED,
            # Map others to closest
            "stalled": DownloadItemStatus.DOWNLOADING,
            "checking": DownloadItemStatus.DOWNLOADING,
            "metadata": DownloadItemStatus.DOWNLOADING,
        }

        return status_map.get(client_status.lower(), DownloadItemStatus.DOWNLOADING)
