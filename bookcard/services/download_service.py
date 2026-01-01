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

"""Service for managing book downloads.

Orchestrates the download process:
1. Selects appropriate download client
2. Sends release to client
3. Tracks download status
4. Updates database records

Follows SOLID principles:
- SRP: Focuses solely on download orchestration
- IOC: Accepts dependencies via constructor
- SOC: Separates business logic from persistence and HTTP concerns
"""

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from bookcard.models.pvr import (
    DownloadClientDefinition,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.models.pvr import (
    DownloadItem as DBDownloadItem,
)
from bookcard.pvr.base import TrackingDownloadClient
from bookcard.pvr.base.interfaces import DownloadManager
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.models import DownloadItem, ReleaseInfo
from bookcard.services.download.client_selector import (
    DownloadClientSelector,
    FirstEnabledSelector,
)
from bookcard.services.download.factory import (
    DefaultDownloadClientFactory,
    DownloadClientFactory,
)
from bookcard.services.download.item_updater import DownloadItemUpdater
from bookcard.services.download.repository import DownloadItemRepository
from bookcard.services.download.status_mapper import DownloadStatusMapper
from bookcard.services.download_client_service import DownloadClientService

logger = logging.getLogger(__name__)


class DownloadService:
    """Service for orchestrating downloads.

    Parameters
    ----------
    download_item_repo : DownloadItemRepository
        Repository for download items.
    download_client_service : DownloadClientService
        Service for managing download clients.
    client_factory : DownloadClientFactory
        Factory for creating download clients.
    client_selector : DownloadClientSelector
        Strategy for selecting download clients.
    item_updater : DownloadItemUpdater
        Updater for download items.
    """

    def __init__(
        self,
        download_item_repo: DownloadItemRepository,
        download_client_service: DownloadClientService,
        client_factory: DownloadClientFactory | None = None,
        client_selector: DownloadClientSelector | None = None,
        item_updater: DownloadItemUpdater | None = None,
    ) -> None:
        """Initialize download service."""
        self._download_item_repo = download_item_repo
        self._client_service = download_client_service
        self._client_factory = client_factory or DefaultDownloadClientFactory()
        self._client_selector = client_selector or FirstEnabledSelector()
        self._item_updater = item_updater or DownloadItemUpdater()

    def initiate_download(
        self,
        release: ReleaseInfo,
        tracked_book: TrackedBook,
        client: DownloadClientDefinition | None = None,
    ) -> DBDownloadItem:
        """Initiate a download for a release.

        Parameters
        ----------
        release : ReleaseInfo
            Release to download.
        tracked_book : TrackedBook
            Tracked book this release belongs to.
        client : DownloadClientDefinition | None
            Specific download client to use. If None, selects automatically.

        Returns
        -------
        DBDownloadItem
            Created download item tracking the download.

        Raises
        ------
        ValueError
            If no suitable download client found or validation fails.
        PVRProviderError
            If download fails to start.
        """
        self._validate_initiate_download(release, tracked_book)

        if client is None:
            # Use decrypted clients for selection to ensure we can connect if needed
            clients = self._client_service.list_decrypted_download_clients(
                enabled_only=True
            )
            client = self._client_selector.select(release, clients)
            if client is None:
                msg = f"No suitable download client found for release: {release.title}"
                raise ValueError(msg)

        logger.info(
            "Initiating download for '%s' using client '%s'",
            release.title,
            client.name,
        )

        try:
            # Create client instance and start download
            client_instance = self._client_factory.create(client)
            client_item_id = client_instance.add_download(
                download_url=release.download_url,
                title=release.title,
                category=client.category,
                download_path=client.download_path,
            )

            # Create download item record
            download_item = self._create_download_item(
                release, tracked_book, client, client_item_id
            )
            self._download_item_repo.add(download_item)

            # Update tracked book status
            self._update_tracked_book_for_download(tracked_book)

            self._download_item_repo.commit()
            self._download_item_repo.refresh(download_item)
        except PVRProviderError:
            raise
        except Exception as e:
            logger.exception("Failed to initiate download for '%s'", release.title)
            msg = f"Failed to start download: {e}"
            raise PVRProviderError(msg) from e
        else:
            logger.info("Download started successfully: %s", client_item_id)
            return download_item

    def _validate_initiate_download(
        self, release: ReleaseInfo, tracked_book: TrackedBook
    ) -> None:
        """Validate download initiation parameters.

        Parameters
        ----------
        release : ReleaseInfo
            Release to validate.
        tracked_book : TrackedBook
            Tracked book to validate.

        Raises
        ------
        ValueError
            If validation fails.
        """
        if not release.download_url:
            msg = "Release must have a download URL"
            raise ValueError(msg)

        if tracked_book.status == TrackedBookStatus.DOWNLOADING:
            msg = f"Book {tracked_book.id} is already downloading"
            raise ValueError(msg)

    def _create_download_item(
        self,
        release: ReleaseInfo,
        tracked_book: TrackedBook,
        client: DownloadClientDefinition,
        client_item_id: str,
    ) -> DBDownloadItem:
        """Create download item from release information.

        Parameters
        ----------
        release : ReleaseInfo
            Release information.
        tracked_book : TrackedBook
            Tracked book.
        client : DownloadClientDefinition
            Download client.
        client_item_id : str
            Client-specific item ID.

        Returns
        -------
        DBDownloadItem
            Created download item.
        """
        return DBDownloadItem(
            tracked_book_id=tracked_book.id,  # type: ignore[arg-type]
            download_client_id=client.id,  # type: ignore[arg-type]
            indexer_id=release.indexer_id,
            client_item_id=client_item_id,
            title=release.title,
            download_url=release.download_url,
            status=DownloadItemStatus.QUEUED,
            quality=release.quality,
            size_bytes=release.size_bytes,
            release_info=release.model_dump(mode="json"),
        )

    def _update_tracked_book_for_download(self, tracked_book: TrackedBook) -> None:
        """Update tracked book status for download initiation.

        Parameters
        ----------
        tracked_book : TrackedBook
            Tracked book to update.
        """
        tracked_book.status = TrackedBookStatus.DOWNLOADING
        tracked_book.last_downloaded_at = datetime.now(UTC)

    def get_download_status(self, download_item_id: int) -> DBDownloadItem | None:
        """Get current status of a download item.

        Parameters
        ----------
        download_item_id : int
            ID of the download item.

        Returns
        -------
        DownloadItem | None
            Download item if found, None otherwise.
        """
        return self._download_item_repo.get(download_item_id)

    def track_download(self, download_item: DBDownloadItem) -> None:
        """Update status of a specific download item.

        Polls the client for current status and updates the database record.

        Parameters
        ----------
        download_item : DownloadItem
            Download item to update.
        """
        if DownloadStatusMapper.is_terminal(download_item.status):
            return

        client = self._client_service.get_download_client(
            download_item.download_client_id
        )
        if not client:
            logger.warning(
                "Download client %s not found for item %s",
                download_item.download_client_id,
                download_item.id,
            )
            return

        try:
            client_instance = self._client_factory.create(client)
            if not isinstance(client_instance, TrackingDownloadClient):
                logger.warning(
                    "Download client %s does not support tracking", client.name
                )
                return

            items = client_instance.get_items()
            matching_item = self._find_matching_item(download_item, items)

            if matching_item:
                self._item_updater.update(download_item, matching_item)  # type: ignore[arg-type]
                download_item.updated_at = datetime.now(UTC)
                self._download_item_repo.update(download_item)
                self._download_item_repo.commit()
            else:
                logger.info(
                    "Download item %s not found in client %s",
                    download_item.client_item_id,
                    client.name,
                )

        except Exception:
            logger.exception("Error tracking download item %s", download_item.id)

    def _find_matching_item(
        self, download_item: DBDownloadItem, items: Sequence[DownloadItem]
    ) -> DownloadItem | None:
        """Find matching item in client items list.

        Parameters
        ----------
        download_item : DownloadItem
            Database download item.
        items : list[dict[str, object]]
            Items from download client.

        Returns
        -------
        DownloadItem | None
            Matching item if found, None otherwise.
        """
        for item in items:
            if item.get("client_item_id") == download_item.client_item_id:
                return item
        return None

    def cancel_download(self, download_item_id: int) -> DBDownloadItem:
        """Cancel a download.

        Removes from client and updates DB status to REMOVED.

        Parameters
        ----------
        download_item_id : int
            ID of the download item to cancel.

        Returns
        -------
        DBDownloadItem
            Updated download item.

        Raises
        ------
        ValueError
            If download item not found.
        """
        download_item = self._download_item_repo.get(download_item_id)
        if not download_item:
            msg = f"Download item {download_item_id} not found"
            raise ValueError(msg)

        if not DownloadStatusMapper.is_terminal(download_item.status):
            # Get decrypted client for connection
            client = self._client_service.get_decrypted_download_client(
                download_item.download_client_id
            )
            if client:
                try:
                    client_instance = self._client_factory.create(client)
                    if isinstance(client_instance, DownloadManager):
                        client_instance.remove_item(
                            download_item.client_item_id, delete_files=True
                        )
                except (PVRProviderError, ValueError) as e:
                    logger.warning(
                        "Failed to remove item %s from client %s: %s",
                        download_item.client_item_id,
                        client.name,
                        e,
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning(
                        "Unexpected error removing item %s from client %s: %s",
                        download_item.client_item_id,
                        client.name,
                        e,
                    )

        download_item.status = DownloadItemStatus.REMOVED
        download_item.error_message = "Cancelled by user"
        download_item.updated_at = datetime.now(UTC)
        self._download_item_repo.update(download_item)
        self._download_item_repo.commit()
        self._download_item_repo.refresh(download_item)
        return download_item

    def get_active_downloads(self) -> Sequence[DBDownloadItem]:
        """Get active download items (queue).

        Returns
        -------
        Sequence[DBDownloadItem]
            List of active download items.
        """
        return self._download_item_repo.get_active()

    def get_download_history(
        self, limit: int = 100, offset: int = 0
    ) -> Sequence[DBDownloadItem]:
        """Get historical download items.

        Parameters
        ----------
        limit : int
            Maximum number of items to return.
        offset : int
            Number of items to skip.

        Returns
        -------
        Sequence[DBDownloadItem]
            List of historical download items.
        """
        return self._download_item_repo.get_history(limit, offset)
