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

"""Service for indexer management operations.

Follows SOLID principles:
- SRP: Focuses solely on indexer CRUD, health checking, and status management
- IOC: Accepts repository and factory as dependencies
- SOC: Separates business logic from persistence and HTTP concerns
"""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from bookcard.models.pvr import IndexerDefinition, IndexerStatus
from bookcard.pvr.base import PVRProviderError
from bookcard.pvr.factory import create_indexer
from bookcard.repositories.base import Repository

if TYPE_CHECKING:
    from bookcard.api.schemas.indexers import IndexerCreate, IndexerUpdate

logger = logging.getLogger(__name__)


class IndexerRepository(Repository[IndexerDefinition]):
    """Repository for indexer definitions.

    Extends generic Repository with indexer-specific queries.
    """

    def __init__(self, session: Session) -> None:
        """Initialize indexer repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        super().__init__(session, IndexerDefinition)

    def list_enabled(self) -> list[IndexerDefinition]:
        """List all enabled indexers ordered by priority.

        Returns
        -------
        list[IndexerDefinition]
            List of enabled indexers.
        """
        stmt = (
            select(IndexerDefinition)
            .where(IndexerDefinition.enabled)
            .order_by(IndexerDefinition.priority, IndexerDefinition.id)
        )
        return list(self._session.exec(stmt).all())

    def list_by_status(self, status: IndexerStatus) -> list[IndexerDefinition]:
        """List indexers by status.

        Parameters
        ----------
        status : IndexerStatus
            Status to filter by.

        Returns
        -------
        list[IndexerDefinition]
            List of indexers with the specified status.
        """
        stmt = select(IndexerDefinition).where(IndexerDefinition.status == status)
        return list(self._session.exec(stmt).all())


class IndexerService:
    """Service for indexer management operations.

    Handles CRUD operations, health checking, and status management
    for indexers. Delegates to repository for persistence and factory
    for indexer instance creation.

    Parameters
    ----------
    session : Session
        Database session.
    repository : IndexerRepository | None
        Indexer repository. If None, creates a new instance.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        repository: IndexerRepository | None = None,
    ) -> None:
        """Initialize indexer service.

        Parameters
        ----------
        session : Session
            Database session.
        repository : IndexerRepository | None
            Indexer repository. If None, creates a new instance.
        """
        self._session = session
        self._repository = repository or IndexerRepository(session)

    def create_indexer(self, data: "IndexerCreate") -> IndexerDefinition:
        """Create a new indexer.

        Parameters
        ----------
        data : IndexerCreate
            Indexer creation data.

        Returns
        -------
        IndexerDefinition
            Created indexer.

        Raises
        ------
        ValueError
            If indexer type is invalid or configuration is invalid.
        """
        indexer = IndexerDefinition(
            name=data.name,
            indexer_type=data.indexer_type,
            protocol=data.protocol,
            base_url=data.base_url,
            api_key=data.api_key,
            enabled=data.enabled,
            priority=data.priority,
            timeout_seconds=data.timeout_seconds,
            retry_count=data.retry_count,
            categories=data.categories,
            additional_settings=data.additional_settings,
            status=IndexerStatus.UNHEALTHY,  # New indexers start as unhealthy
        )
        self._repository.add(indexer)
        self._session.commit()
        self._session.refresh(indexer)
        logger.info("Created indexer: %s (id=%s)", indexer.name, indexer.id)
        return indexer

    def get_indexer(self, indexer_id: int) -> IndexerDefinition | None:
        """Get an indexer by ID.

        Parameters
        ----------
        indexer_id : int
            Indexer ID.

        Returns
        -------
        IndexerDefinition | None
            Indexer if found, None otherwise.
        """
        return self._repository.get(indexer_id)

    def list_indexers(self, enabled_only: bool = False) -> list[IndexerDefinition]:
        """List all indexers.

        Parameters
        ----------
        enabled_only : bool
            If True, only return enabled indexers.

        Returns
        -------
        list[IndexerDefinition]
            List of indexers.
        """
        if enabled_only:
            return self._repository.list_enabled()
        return list(self._repository.list())

    def update_indexer(
        self, indexer_id: int, data: "IndexerUpdate"
    ) -> IndexerDefinition | None:
        """Update an indexer.

        Parameters
        ----------
        indexer_id : int
            Indexer ID.
        data : IndexerUpdate
            Update data (partial).

        Returns
        -------
        IndexerDefinition | None
            Updated indexer if found, None otherwise.

        Raises
        ------
        ValueError
            If update data is invalid.
        """
        indexer = self._repository.get(indexer_id)
        if indexer is None:
            return None

        # Update only provided fields using a mapping approach
        self._apply_updates(indexer, data)

        indexer.updated_at = datetime.now(UTC)
        self._session.add(indexer)
        self._session.commit()
        self._session.refresh(indexer)
        logger.info("Updated indexer: %s (id=%s)", indexer.name, indexer.id)
        return indexer

    def _apply_updates(self, indexer: IndexerDefinition, data: "IndexerUpdate") -> None:
        """Apply update data to indexer instance.

        Parameters
        ----------
        indexer : IndexerDefinition
            Indexer instance to update.
        data : IndexerUpdate
            Update data (partial).
        """
        update_mapping = {
            "name": data.name,
            "base_url": data.base_url,
            "api_key": data.api_key,
            "enabled": data.enabled,
            "priority": data.priority,
            "timeout_seconds": data.timeout_seconds,
            "retry_count": data.retry_count,
            "categories": data.categories,
            "additional_settings": data.additional_settings,
        }

        for field_name, value in update_mapping.items():
            if value is not None:
                setattr(indexer, field_name, value)

    def delete_indexer(self, indexer_id: int) -> bool:
        """Delete an indexer.

        Parameters
        ----------
        indexer_id : int
            Indexer ID.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        indexer = self._repository.get(indexer_id)
        if indexer is None:
            return False

        self._repository.delete(indexer)
        self._session.commit()
        logger.info("Deleted indexer: %s (id=%s)", indexer.name, indexer_id)
        return True

    def test_connection(self, indexer_id: int) -> tuple[bool, str]:
        """Test connection to an indexer.

        Parameters
        ----------
        indexer_id : int
            Indexer ID.

        Returns
        -------
        tuple[bool, str]
            Tuple of (success, message).

        Raises
        ------
        ValueError
            If indexer not found.
        """
        indexer = self._repository.get(indexer_id)
        if indexer is None:
            msg = f"Indexer {indexer_id} not found"
            raise ValueError(msg)

        try:
            indexer_instance = create_indexer(indexer)
            success = indexer_instance.test_connection()
            if success:
                message = "Connection test successful"
                # Update status on success
                self._update_indexer_status(indexer, IndexerStatus.HEALTHY, None, True)
            else:
                message = "Connection test failed"
                self._update_indexer_status(
                    indexer, IndexerStatus.UNHEALTHY, message, False
                )
        except PVRProviderError as e:
            error_msg = str(e)
            self._update_indexer_status(
                indexer, IndexerStatus.UNHEALTHY, error_msg, False
            )
            return (False, f"Connection test failed: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.exception("Unexpected error testing indexer connection")
            self._update_indexer_status(
                indexer, IndexerStatus.UNHEALTHY, error_msg, False
            )
            return (False, error_msg)
        else:
            return (success, message)

    def get_indexer_status(self, indexer_id: int) -> IndexerDefinition | None:
        """Get indexer status information.

        Parameters
        ----------
        indexer_id : int
            Indexer ID.

        Returns
        -------
        IndexerDefinition | None
            Indexer with status information if found, None otherwise.
        """
        return self._repository.get(indexer_id)

    def check_indexer_health(self, indexer_id: int) -> None:
        """Check indexer health and update status.

        Parameters
        ----------
        indexer_id : int
            Indexer ID.

        Raises
        ------
        ValueError
            If indexer not found.
        """
        indexer = self._repository.get(indexer_id)
        if indexer is None:
            msg = f"Indexer {indexer_id} not found"
            raise ValueError(msg)

        if not indexer.enabled:
            # Disabled indexers are marked as disabled
            if indexer.status != IndexerStatus.DISABLED:
                self._update_indexer_status(
                    indexer, IndexerStatus.DISABLED, None, False
                )
            return

        try:
            indexer_instance = create_indexer(indexer)
            success = indexer_instance.test_connection()
            if success:
                self._update_indexer_status(indexer, IndexerStatus.HEALTHY, None, True)
            else:
                self._update_indexer_status(
                    indexer, IndexerStatus.UNHEALTHY, "Connection test failed", False
                )
        except PVRProviderError as e:
            self._update_indexer_status(indexer, IndexerStatus.UNHEALTHY, str(e), False)
        except Exception as e:
            logger.exception("Unexpected error checking indexer health")
            self._update_indexer_status(
                indexer, IndexerStatus.UNHEALTHY, f"Unexpected error: {e}", False
            )

    def _update_indexer_status(
        self,
        indexer: IndexerDefinition,
        status: IndexerStatus,
        error_message: str | None,
        success: bool,
    ) -> None:
        """Update indexer status and health metrics.

        Parameters
        ----------
        indexer : IndexerDefinition
            Indexer to update.
        status : IndexerStatus
            New status.
        error_message : str | None
            Error message if status is unhealthy.
        success : bool
            Whether the operation was successful.
        """
        indexer.status = status
        indexer.last_checked_at = datetime.now(UTC)

        if success:
            indexer.last_successful_query_at = datetime.now(UTC)
            indexer.error_count = 0
            indexer.error_message = None
        else:
            indexer.error_count += 1
            indexer.error_message = error_message

        indexer.updated_at = datetime.now(UTC)
        self._session.add(indexer)
        self._session.commit()
        self._session.refresh(indexer)
