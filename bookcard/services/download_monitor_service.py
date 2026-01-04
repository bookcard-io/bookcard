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

from sqlmodel import Session

from bookcard.common.clock import Clock, UTCClock
from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadClientStatus,
    DownloadItem,
    DownloadItemStatus,
    TrackedBookStatus,
)
from bookcard.pvr.base.interfaces import DownloadTracker
from bookcard.pvr.models import DownloadItem as ClientDownloadItem
from bookcard.services.download.book_updater import TrackedBookStatusUpdater
from bookcard.services.download.client_health_manager import ClientHealthManager
from bookcard.services.download.client_repository import (
    DownloadClientRepository,
    SQLModelDownloadClientRepository,
)
from bookcard.services.download.factory import (
    DefaultDownloadClientFactory,
    DownloadClientFactory,
)
from bookcard.services.download.item_updater import DownloadItemUpdater
from bookcard.services.download.reconciler import DownloadReconciler
from bookcard.services.download.repository import (
    DownloadItemRepository,
    SQLModelDownloadItemRepository,
)
from bookcard.services.download.status_mapper import (
    ClientStatusMapper,
    DefaultStatusMapper,
)
from bookcard.services.pvr.search.matcher import (
    DownloadItemMatcher,
    GuidMatchStrategy,
    InfohashMatchStrategy,
    MetaMatchStrategy,
    TitleMatchStrategy,
    UrlMatchStrategy,
)
from bookcard.services.security import DataEncryptor

logger = logging.getLogger(__name__)


PENDING_CLIENT_ITEM_ID = "PENDING"


class DownloadMonitorService:
    """Service for monitoring download clients and updating local state.

    Refactored to follow SOLID principles with separated concerns.
    """

    def __init__(
        self,
        session: Session,
        encryptor: DataEncryptor | None = None,
        item_repo: DownloadItemRepository | None = None,
        client_repo: DownloadClientRepository | None = None,
        client_factory: DownloadClientFactory | None = None,
        status_mapper: ClientStatusMapper | None = None,
        health_manager: ClientHealthManager | None = None,
        reconciler: DownloadReconciler | None = None,
        item_updater: DownloadItemUpdater | None = None,
        book_updater: TrackedBookStatusUpdater | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Initialize service.

        Parameters
        ----------
        session : Session
            Database session.
        encryptor : DataEncryptor | None
            Data encryptor for decrypting passwords.
        item_repo : DownloadItemRepository | None
            Repository for download items.
        client_repo : DownloadClientRepository | None
            Repository for download clients.
        client_factory : DownloadClientFactory | None
            Factory for creating download clients.
        status_mapper : ClientStatusMapper | None
            Status mapper strategy.
        health_manager : ClientHealthManager | None
            Client health manager.
        reconciler : DownloadReconciler | None
            Download reconciler.
        item_updater : DownloadItemUpdater | None
            Download item updater.
        book_updater : TrackedBookStatusUpdater | None
            Tracked book status updater.
        clock : Clock | None
            Time provider.
        """
        self._session = session
        self._encryptor = encryptor
        self._item_repo = item_repo or SQLModelDownloadItemRepository(session)
        self._client_repo = client_repo or SQLModelDownloadClientRepository(session)
        self._client_factory = client_factory or DefaultDownloadClientFactory()
        self._status_mapper = status_mapper or DefaultStatusMapper()
        self._clock = clock or UTCClock()
        self._health_manager = health_manager or ClientHealthManager(
            session, self._clock
        )
        self._item_updater = item_updater or DownloadItemUpdater(
            self._status_mapper, self._clock
        )
        self._book_updater = book_updater or TrackedBookStatusUpdater()

        if reconciler:
            self._reconciler = reconciler
        else:
            matcher = DownloadItemMatcher(
                strategies=[
                    GuidMatchStrategy(),
                    InfohashMatchStrategy(),
                    UrlMatchStrategy(),
                    MetaMatchStrategy(),
                    TitleMatchStrategy(),
                ]
            )
            self._reconciler = DownloadReconciler(matcher)

    def check_downloads(self) -> None:
        """Check all enabled download clients for updates.

        Iterates through all enabled download clients, fetches their active items,
        and updates local database records. Handles connection errors by updating
        client status.
        """
        clients = self._client_repo.get_enabled_clients()

        for client_def in clients:
            try:
                self._process_client(client_def)
            except (ConnectionError, TimeoutError) as e:
                logger.warning(
                    "Connection error checking download client %s (id=%d): %s",
                    client_def.name,
                    client_def.id,
                    e,
                )
                self._update_client_health(client_def, str(e))
            except Exception as e:
                logger.exception(
                    "Unexpected error checking download client %s (id=%d)",
                    client_def.name,
                    client_def.id,
                )
                self._update_client_health(client_def, str(e))

    def _update_client_health(
        self, client_def: DownloadClientDefinition, error_message: str
    ) -> None:
        """Update client health status on error."""
        self._health_manager.update_status(
            client_def,
            DownloadClientStatus.UNHEALTHY,
            error_message,
        )
        self._session.commit()

    def _process_client(self, client_def: DownloadClientDefinition) -> None:
        """Process a single download client."""
        # Create client instance (handling decryption)
        client = self._create_client_instance(client_def)
        if not client:
            return

        # Fetch items
        client_items = list(client.get_items())

        # Update health status
        self._health_manager.update_status(client_def, DownloadClientStatus.HEALTHY)

        # Get DB items for this client via repository
        if client_def.id is None:
            return
        db_items = list(self._item_repo.get_by_client(client_def.id))

        # Reconcile
        result = self._reconciler.reconcile(db_items, client_items)

        # Update matched items
        for db_item, client_item in result.matched_pairs:
            self._update_item(db_item, client_item)

        # Handle unmatched DB items (removed/missing)
        for db_item in result.unmatched_db_items:
            self._handle_missing_item(db_item, client_def)

        # Commit changes
        self._session.commit()

    def _create_client_instance(
        self, client_def: DownloadClientDefinition
    ) -> DownloadTracker | None:
        """Create a client instance with decrypted password."""
        # Create a detached copy for connection to avoid messing with session objects
        test_client = DownloadClientDefinition(
            id=client_def.id,
            name=client_def.name,
            client_type=client_def.client_type,
            host=client_def.host,
            port=client_def.port,
            username=client_def.username,
            password=client_def.password,
            use_ssl=client_def.use_ssl,
            enabled=client_def.enabled,
            priority=client_def.priority,
            timeout_seconds=client_def.timeout_seconds,
            category=client_def.category,
            download_path=client_def.download_path,
            additional_settings=client_def.additional_settings,
        )

        if test_client.password and self._encryptor:
            try:
                test_client.password = self._encryptor.decrypt(test_client.password)
            except ValueError:
                logger.warning(
                    "Failed to decrypt password for client %s (id=%d). Using as-is.",
                    client_def.name,
                    client_def.id,
                )

        client = self._client_factory.create(test_client)

        if not isinstance(client, DownloadTracker):
            logger.warning(
                "Download client %s (type=%s) does not support tracking",
                client_def.name,
                client_def.client_type,
            )
            return None

        return client

    def _update_item(
        self, db_item: DownloadItem, client_item: ClientDownloadItem
    ) -> None:
        """Update a download item and propagate status."""
        self._item_updater.update(db_item, client_item)

        # Propagate to tracked book
        if db_item.tracked_book:
            # FIX: If tracked book is already completed, do not update status.
            # This prevents re-imports if client reports temporary errors (e.g. during file moves).
            if db_item.tracked_book.status == TrackedBookStatus.COMPLETED:
                return

            if self._book_updater.update_from_download(
                db_item.tracked_book,
                db_item.status,
                db_item.error_message,
            ):
                self._session.add(db_item.tracked_book)

        self._session.add(db_item)

    def _handle_missing_item(
        self, db_item: DownloadItem, client_def: DownloadClientDefinition
    ) -> None:
        """Handle an item that exists in DB but not in client."""
        # Skip pending items (they match later)
        if db_item.client_item_id == PENDING_CLIENT_ITEM_ID:
            logger.debug(
                "Pending item %d ('%s') not found in client yet",
                db_item.id,
                db_item.title,
            )
            return

        if db_item.status not in (
            DownloadItemStatus.COMPLETED,
            DownloadItemStatus.FAILED,
            DownloadItemStatus.REMOVED,
        ):
            logger.warning(
                "Download item %s (id=%d) not found in client %s. Marking as REMOVED.",
                db_item.client_item_id,
                db_item.id,
                client_def.name,
            )
            db_item.status = DownloadItemStatus.REMOVED
            db_item.error_message = "Item removed from download client"

            self._session.add(db_item)
