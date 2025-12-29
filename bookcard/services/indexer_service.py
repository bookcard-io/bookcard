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
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.factory import create_indexer
from bookcard.repositories.base import Repository
from bookcard.services.security import DataEncryptor

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
        encryptor: DataEncryptor | None = None,
    ) -> None:
        """Initialize indexer service.

        Parameters
        ----------
        session : Session
            Database session.
        repository : IndexerRepository | None
            Indexer repository. If None, creates a new instance.
        encryptor : DataEncryptor | None
            Data encryptor for securing API keys.
        """
        self._session = session
        self._repository = repository or IndexerRepository(session)
        self._encryptor = encryptor

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
        api_key = data.api_key
        if api_key and self._encryptor:
            api_key = self._encryptor.encrypt(api_key)

        indexer = IndexerDefinition(
            name=data.name,
            indexer_type=data.indexer_type,
            protocol=data.protocol,
            base_url=data.base_url,
            api_key=api_key,
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

        if data.api_key and self._encryptor:
            update_mapping["api_key"] = self._encryptor.encrypt(data.api_key)

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
        logger.info("Testing connection for indexer %s", indexer_id)
        indexer = self._repository.get(indexer_id)
        if indexer is None:
            msg = f"Indexer {indexer_id} not found"
            logger.error(msg)
            raise ValueError(msg)

        try:
            # Create a detached copy with decrypted API key for connection testing
            # We don't want to modify the attached session object or expose the key
            # in memory longer than necessary.
            test_indexer = IndexerDefinition.model_validate(indexer)
            if test_indexer.api_key and self._encryptor:
                try:
                    test_indexer.api_key = self._encryptor.decrypt(test_indexer.api_key)
                except ValueError:
                    # If decryption fails, it might be an old plain text key
                    # or actually invalid. We try to use it as is, or we could
                    # choose to fail fast here.
                    logger.warning(
                        "Failed to decrypt API key for indexer %s. Using as-is.",
                        indexer.id,
                    )

            logger.info(
                "Creating indexer instance for %s (url=%s, type=%s)",
                indexer.name,
                indexer.base_url,
                indexer.indexer_type,
            )
            indexer_instance = create_indexer(test_indexer)
            logger.info("Running test_connection on instance")
            success = indexer_instance.test_connection()
            logger.info("Connection test result: %s", success)

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
            logger.info("PVRProviderError during connection test: %s", error_msg)
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

    def test_connection_with_settings(self, data: "IndexerCreate") -> tuple[bool, str]:
        """Test connection using provided settings without saving.

        Parameters
        ----------
        data : IndexerCreate
            Indexer settings.

        Returns
        -------
        tuple[bool, str]
            Tuple of (success, message).
        """
        try:
            # Create temporary indexer definition
            indexer_def = IndexerDefinition(
                name=data.name,
                indexer_type=data.indexer_type,
                protocol=data.protocol,
                base_url=data.base_url,
                api_key=data.api_key,  # Use raw API key for testing
                enabled=True,
                priority=0,
                timeout_seconds=data.timeout_seconds,
                retry_count=data.retry_count,
                categories=data.categories,
                additional_settings=data.additional_settings,
                status=IndexerStatus.UNKNOWN,
            )

            logger.info(
                "Testing connection with settings (url=%s, type=%s)",
                indexer_def.base_url,
                indexer_def.indexer_type,
            )

            indexer_instance = create_indexer(indexer_def)
            success = indexer_instance.test_connection()
            logger.info("Connection test result: %s", success)

            if success:
                return (True, "Connection test successful")
        except PVRProviderError as e:
            error_msg = str(e)
            logger.info("PVRProviderError during connection test: %s", error_msg)
            return (False, f"Connection test failed: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.exception("Unexpected error testing indexer connection")
            return (False, error_msg)
        else:
            return (False, "Connection test failed")

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
            # Create a detached copy with decrypted API key for connection testing
            test_indexer = IndexerDefinition.model_validate(indexer)
            if test_indexer.api_key and self._encryptor:
                try:
                    test_indexer.api_key = self._encryptor.decrypt(test_indexer.api_key)
                except ValueError:
                    logger.warning(
                        "Failed to decrypt API key for indexer %s. Using as-is.",
                        indexer.id,
                    )

            indexer_instance = create_indexer(test_indexer)
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
