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

"""Service for download client management operations.

Follows SOLID principles:
- SRP: Focuses solely on download client CRUD, health checking, and status management
- IOC: Accepts repository and factory as dependencies
- SOC: Separates business logic from persistence and HTTP concerns
"""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, NoReturn, cast

from sqlmodel import Session, select

from bookcard.models.pvr import DownloadClientDefinition, DownloadClientStatus
from bookcard.pvr.base import TrackingDownloadClient
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.factory.download_client_factory import create_download_client
from bookcard.repositories.base import Repository
from bookcard.services.security import DataEncryptor

if TYPE_CHECKING:
    from bookcard.api.schemas.download_clients import (
        DownloadClientCreate,
        DownloadClientUpdate,
    )

logger = logging.getLogger(__name__)


def _raise_tracking_not_supported_error(client_name: str) -> NoReturn:
    """Raise an error when download client doesn't support tracking.

    Centralized function for raising tracking support errors to follow DRY
    and satisfy linter requirements for abstracting raise statements.

    Parameters
    ----------
    client_name : str
        Name of the download client that doesn't support tracking.

    Raises
    ------
    TypeError
        Always raises with the error message.
    """
    msg = f"Download client {client_name} does not support tracking downloads"
    raise TypeError(msg)


class DownloadClientRepository(Repository[DownloadClientDefinition]):
    """Repository for download client definitions.

    Extends generic Repository with download client-specific queries.
    """

    def __init__(self, session: Session) -> None:
        """Initialize download client repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        super().__init__(session, DownloadClientDefinition)

    def list_enabled(self) -> list[DownloadClientDefinition]:
        """List all enabled download clients ordered by priority.

        Returns
        -------
        list[DownloadClientDefinition]
            List of enabled download clients.
        """
        stmt = (
            select(DownloadClientDefinition)
            .where(DownloadClientDefinition.enabled)
            .order_by(DownloadClientDefinition.priority, DownloadClientDefinition.id)  # type: ignore[invalid-argument-type]
        )
        return list(self._session.exec(stmt).all())

    def list_by_status(
        self, status: DownloadClientStatus
    ) -> list[DownloadClientDefinition]:
        """List download clients by status.

        Parameters
        ----------
        status : DownloadClientStatus
            Status to filter by.

        Returns
        -------
        list[DownloadClientDefinition]
            List of download clients with the specified status.
        """
        stmt = select(DownloadClientDefinition).where(
            DownloadClientDefinition.status == status
        )
        return list(self._session.exec(stmt).all())


class DownloadClientService:
    """Service for download client management operations.

    Handles CRUD operations, health checking, and status management
    for download clients. Delegates to repository for persistence and factory
    for download client instance creation.

    Parameters
    ----------
    session : Session
        Database session.
    repository : DownloadClientRepository | None
        Download client repository. If None, creates a new instance.
    """

    def __init__(
        self,
        session: Session,
        repository: DownloadClientRepository | None = None,
        encryptor: DataEncryptor | None = None,
    ) -> None:
        """Initialize download client service.

        Parameters
        ----------
        session : Session
            Database session.
        repository : DownloadClientRepository | None
            Download client repository. If None, creates a new instance.
        encryptor : DataEncryptor | None
            Data encryptor for securing passwords.
        """
        self._session = session
        self._repository = repository or DownloadClientRepository(session)
        self._encryptor = encryptor

    def create_download_client(
        self, data: "DownloadClientCreate"
    ) -> DownloadClientDefinition:
        """Create a new download client.

        Parameters
        ----------
        data : DownloadClientCreate
            Download client creation data.

        Returns
        -------
        DownloadClientDefinition
            Created download client.

        Raises
        ------
        ValueError
            If download client type is invalid or configuration is invalid.
        """
        password = data.password
        if password and self._encryptor:
            password = self._encryptor.encrypt(password)

        client = DownloadClientDefinition(
            name=data.name,
            client_type=data.client_type,
            host=data.host,
            port=data.port,
            username=data.username,
            password=password,
            use_ssl=data.use_ssl,
            enabled=data.enabled,
            priority=data.priority,
            timeout_seconds=data.timeout_seconds,
            category=data.category,
            download_path=data.download_path,
            additional_settings=data.additional_settings,
            status=DownloadClientStatus.UNHEALTHY,  # New clients start as unhealthy
        )
        self._repository.add(client)
        self._session.commit()
        self._session.refresh(client)
        logger.info("Created download client: %s (id=%s)", client.name, client.id)
        return client

    def get_download_client(self, client_id: int) -> DownloadClientDefinition | None:
        """Get a download client by ID.

        Parameters
        ----------
        client_id : int
            Download client ID.

        Returns
        -------
        DownloadClientDefinition | None
            Download client if found, None otherwise.
        """
        return self._repository.get(client_id)

    def list_download_clients(
        self, enabled_only: bool = False
    ) -> list[DownloadClientDefinition]:
        """List all download clients.

        Parameters
        ----------
        enabled_only : bool
            If True, only return enabled download clients.

        Returns
        -------
        list[DownloadClientDefinition]
            List of download clients.
        """
        if enabled_only:
            return self._repository.list_enabled()
        return list(self._repository.list())

    def update_download_client(
        self, client_id: int, data: "DownloadClientUpdate"
    ) -> DownloadClientDefinition | None:
        """Update a download client.

        Parameters
        ----------
        client_id : int
            Download client ID.
        data : DownloadClientUpdate
            Update data (partial).

        Returns
        -------
        DownloadClientDefinition | None
            Updated download client if found, None otherwise.

        Raises
        ------
        ValueError
            If update data is invalid.
        """
        client = self._repository.get(client_id)
        if client is None:
            return None

        # Update only provided fields using a mapping approach
        self._apply_updates(client, data)

        client.updated_at = datetime.now(UTC)
        self._session.add(client)
        self._session.commit()
        self._session.refresh(client)
        logger.info("Updated download client: %s (id=%s)", client.name, client.id)
        return client

    def _apply_updates(
        self, client: DownloadClientDefinition, data: "DownloadClientUpdate"
    ) -> None:
        """Apply update data to download client instance.

        Parameters
        ----------
        client : DownloadClientDefinition
            Download client instance to update.
        data : DownloadClientUpdate
            Update data (partial).
        """
        update_mapping = {
            "name": data.name,
            "host": data.host,
            "port": data.port,
            "username": data.username,
            "password": data.password,
            "use_ssl": data.use_ssl,
            "enabled": data.enabled,
            "priority": data.priority,
            "timeout_seconds": data.timeout_seconds,
            "category": data.category,
            "download_path": data.download_path,
            "additional_settings": data.additional_settings,
        }

        if data.password and self._encryptor:
            update_mapping["password"] = self._encryptor.encrypt(data.password)

        for field_name, value in update_mapping.items():
            if value is not None:
                setattr(client, field_name, value)

    def delete_download_client(self, client_id: int) -> bool:
        """Delete a download client.

        Parameters
        ----------
        client_id : int
            Download client ID.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        client = self._repository.get(client_id)
        if client is None:
            return False

        self._repository.delete(client)
        self._session.commit()
        logger.info("Deleted download client: %s (id=%s)", client.name, client_id)
        return True

    def test_connection(self, client_id: int) -> tuple[bool, str]:
        """Test connection to a download client.

        Parameters
        ----------
        client_id : int
            Download client ID.

        Returns
        -------
        tuple[bool, str]
            Tuple of (success, message).

        Raises
        ------
        ValueError
            If download client not found.
        """
        client = self._repository.get(client_id)
        if client is None:
            msg = f"Download client {client_id} not found"
            raise ValueError(msg)

        try:
            # Decrypt password for connection testing
            test_client = self._decrypt_download_client(client)
            client_instance = create_download_client(test_client)
            success = client_instance.test_connection()
            if success:
                message = "Connection test successful"
                # Update status on success
                self._update_client_status(
                    client, DownloadClientStatus.HEALTHY, None, True
                )
            else:
                message = "Connection test failed"
                self._update_client_status(
                    client, DownloadClientStatus.UNHEALTHY, message, False
                )
        except PVRProviderError as e:
            error_msg = str(e)
            self._update_client_status(
                client, DownloadClientStatus.UNHEALTHY, error_msg, False
            )
            return (False, f"Connection test failed: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.exception("Unexpected error testing download client connection")
            self._update_client_status(
                client, DownloadClientStatus.UNHEALTHY, error_msg, False
            )
            return (False, error_msg)

        return (success, message)

    def test_connection_with_settings(
        self, data: "DownloadClientCreate"
    ) -> tuple[bool, str]:
        """Test connection using provided settings without saving.

        Parameters
        ----------
        data : DownloadClientCreate
            Download client settings.

        Returns
        -------
        tuple[bool, str]
            Tuple of (success, message).
        """
        try:
            # Create temporary download client definition
            client_def = DownloadClientDefinition(
                name=data.name,
                client_type=data.client_type,
                host=data.host,
                port=data.port,
                username=data.username,
                password=data.password,
                use_ssl=data.use_ssl,
                enabled=data.enabled,
                priority=data.priority,
                timeout_seconds=data.timeout_seconds,
                category=data.category,
                download_path=data.download_path,
                additional_settings=data.additional_settings,
                status=DownloadClientStatus.UNHEALTHY,
            )

            logger.info(
                "Testing connection with settings (host=%s, type=%s)",
                client_def.host,
                client_def.client_type,
            )

            client_instance = create_download_client(client_def)
            success = client_instance.test_connection()
            logger.info("Connection test result: %s", success)

            if success:
                return (True, "Connection test successful")
        except PVRProviderError as e:
            error_msg = str(e)
            logger.info("PVRProviderError during connection test: %s", error_msg)
            return (False, f"Connection test failed: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.exception("Unexpected error testing download client connection")
            return (False, error_msg)
        else:
            return (False, "Connection test failed")

    def get_download_client_status(
        self, client_id: int
    ) -> DownloadClientDefinition | None:
        """Get download client status information.

        Parameters
        ----------
        client_id : int
            Download client ID.

        Returns
        -------
        DownloadClientDefinition | None
            Download client with status information if found, None otherwise.
        """
        return self._repository.get(client_id)

    def check_download_client_health(self, client_id: int) -> None:
        """Check download client health and update status.

        Parameters
        ----------
        client_id : int
            Download client ID.

        Raises
        ------
        ValueError
            If download client not found.
        """
        client = self._repository.get(client_id)
        if client is None:
            msg = f"Download client {client_id} not found"
            raise ValueError(msg)

        if not client.enabled:
            # Disabled clients are marked as disabled
            if client.status != DownloadClientStatus.DISABLED:
                self._update_client_status(
                    client, DownloadClientStatus.DISABLED, None, False
                )
            return

        try:
            client_instance = create_download_client(client)
            success = client_instance.test_connection()
            if success:
                self._update_client_status(
                    client, DownloadClientStatus.HEALTHY, None, True
                )
            else:
                self._update_client_status(
                    client,
                    DownloadClientStatus.UNHEALTHY,
                    "Connection test failed",
                    False,
                )
        except PVRProviderError as e:
            self._update_client_status(
                client, DownloadClientStatus.UNHEALTHY, str(e), False
            )
        except Exception as e:
            logger.exception("Unexpected error checking download client health")
            self._update_client_status(
                client, DownloadClientStatus.UNHEALTHY, f"Unexpected error: {e}", False
            )

    def get_download_items(self, client_id: int) -> list[dict[str, object]]:
        """Get active downloads from a download client.

        Parameters
        ----------
        client_id : int
            Download client ID.

        Returns
        -------
        list[dict[str, object]]
            List of download items.

        Raises
        ------
        ValueError
            If download client not found.
        TypeError
            If client doesn't support tracking.
        PVRProviderError
            If fetching items fails.
        """
        client = self._repository.get(client_id)
        if client is None:
            msg = f"Download client {client_id} not found"
            raise ValueError(msg)

        try:
            # Decrypt password for getting items
            test_client = self._decrypt_download_client(client)
            client_instance = create_download_client(test_client)
            if not isinstance(client_instance, TrackingDownloadClient):
                _raise_tracking_not_supported_error(client.name)

            # Type checker: after isinstance check and potential raise, this is guaranteed
            # to be TrackingDownloadClient which has get_items()
            tracking_client = cast("TrackingDownloadClient", client_instance)
            items = tracking_client.get_items()
            # `DownloadItem` is a TypedDict but runtime values are plain dicts.
            # Cast for callers expecting `dict[str, object]`.
            return [cast("dict[str, object]", item) for item in items]
        except (ValueError, TypeError, PVRProviderError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error getting download items: {e}"
            logger.exception("Unexpected error getting download items")
            raise PVRProviderError(error_msg) from e

    def get_decrypted_download_client(
        self, client_id: int
    ) -> DownloadClientDefinition | None:
        """Get a download client with decrypted password.

        Returns a detached copy of the download client definition with the password
        decrypted. Safe to use for making requests without exposing the password
        in the database session.

        Parameters
        ----------
        client_id : int
            Download client ID.

        Returns
        -------
        DownloadClientDefinition | None
            Decrypted download client definition if found, None otherwise.
        """
        client = self.get_download_client(client_id)
        if client is None:
            return None
        return self._decrypt_download_client(client)

    def list_decrypted_download_clients(
        self, enabled_only: bool = False
    ) -> list[DownloadClientDefinition]:
        """List all download clients with decrypted passwords.

        Returns detached copies of download client definitions with passwords decrypted.

        Parameters
        ----------
        enabled_only : bool
            If True, only return enabled download clients.

        Returns
        -------
        list[DownloadClientDefinition]
            List of decrypted download client definitions.
        """
        clients = self.list_download_clients(enabled_only=enabled_only)
        return [self._decrypt_download_client(client) for client in clients]

    def _decrypt_download_client(
        self, client: DownloadClientDefinition
    ) -> DownloadClientDefinition:
        """Create a detached copy of a download client with decrypted password.

        Parameters
        ----------
        client : DownloadClientDefinition
            Original download client definition.

        Returns
        -------
        DownloadClientDefinition
            Detached copy with decrypted password.
        """
        # Create a detached copy with decrypted password
        # We don't want to modify the attached session object or expose the password
        # in memory longer than necessary.
        decrypted_client = DownloadClientDefinition.model_validate(client)

        if decrypted_client.password and self._encryptor:
            try:
                decrypted_client.password = self._encryptor.decrypt(
                    decrypted_client.password
                )
            except ValueError:
                # If decryption fails, it might be an old plain text password
                # or actually invalid. We try to use it as is.
                logger.warning(
                    "Failed to decrypt password for download client %s. Using as-is.",
                    client.id,
                )

        return decrypted_client

    def _update_client_status(
        self,
        client: DownloadClientDefinition,
        status: DownloadClientStatus,
        error_message: str | None,
        success: bool,
    ) -> None:
        """Update download client status and health metrics.

        Parameters
        ----------
        client : DownloadClientDefinition
            Download client to update.
        status : DownloadClientStatus
            New status.
        error_message : str | None
            Error message if status is unhealthy.
        success : bool
            Whether the operation was successful.
        """
        client.status = status
        client.last_checked_at = datetime.now(UTC)

        if success:
            client.last_successful_connection_at = datetime.now(UTC)
            client.error_count = 0
            client.error_message = None
        else:
            client.error_count += 1
            client.error_message = error_message

        client.updated_at = datetime.now(UTC)
        self._session.add(client)
        self._session.commit()
        self._session.refresh(client)
