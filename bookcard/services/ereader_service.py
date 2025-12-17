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

"""E-reader device service.

Encapsulates e-reader device management operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.models.auth import EReaderDevice

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.auth import EBookFormat
    from bookcard.repositories.ereader_repository import EReaderRepository
    from bookcard.services.dedrm_service import DeDRMService


class EReaderService:
    """Operations for managing e-reader devices.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    devices : EReaderRepository
        Repository providing e-reader device persistence operations.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        devices: EReaderRepository,  # type: ignore[type-arg]
        dedrm_service: DeDRMService | None = None,
    ) -> None:
        self._session = session
        self._devices = devices
        self._dedrm_service = dedrm_service

    def create_device(
        self,
        user_id: int,
        email: str,
        *,
        device_name: str | None = None,
        device_type: str = "kindle",
        preferred_format: EBookFormat | None = None,
        is_default: bool = False,
        serial_number: str | None = None,
    ) -> EReaderDevice:
        """Create a new e-reader device.

        Parameters
        ----------
        user_id : int
            User identifier.
        email : str
            E-reader email address.
        device_name : str | None
            Optional user-friendly device name.
        device_type : str
            Device type (default: 'kindle').
        preferred_format : EBookFormat | None
            Preferred format for this device.
        is_default : bool
            Whether this is the default device (default: False).
        serial_number : str | None
            Optional device serial number for DRM removal.

        Returns
        -------
        EReaderDevice
            Created e-reader device entity.

        Raises
        ------
        ValueError
            If a device with the same email already exists for the user.
        """
        existing = self._devices.find_by_email(user_id, email)
        if existing is not None:
            msg = "device_email_already_exists"
            raise ValueError(msg)

        # If this is set as default, unset other defaults for this user
        if is_default:
            self._unset_defaults(user_id)

        device = EReaderDevice(
            user_id=user_id,
            email=email,
            device_name=device_name,
            device_type=device_type,
            preferred_format=preferred_format,
            is_default=is_default,
            serial_number=serial_number,
        )
        self._devices.add(device)
        self._session.flush()

        # Sync serial numbers if provided and service is available
        if serial_number and self._dedrm_service:
            self._sync_dedrm_keys()

        return device

    def update_device(
        self,
        device_id: int,
        *,
        email: str | None = None,
        device_name: str | None = None,
        device_type: str | None = None,
        preferred_format: EBookFormat | None = None,
        is_default: bool | None = None,
        serial_number: str | None = None,
    ) -> EReaderDevice:
        """Update an e-reader device.

        Parameters
        ----------
        device_id : int
            Device identifier.
        email : str | None
            New email address (if provided).
        device_name : str | None
            New device name (if provided).
        device_type : str | None
            New device type (if provided).
        preferred_format : EBookFormat | None
            New preferred format (if provided).
        is_default : bool | None
            New default status (if provided).
        serial_number : str | None
            New serial number (if provided).

        Returns
        -------
        EReaderDevice
            Updated e-reader device entity.

        Raises
        ------
        ValueError
            If the device does not exist or email conflicts with another device.
        """
        device = self._devices.get(device_id)
        if device is None:
            msg = "device_not_found"
            raise ValueError(msg)

        self._update_email_if_provided(device, device_id, email)
        self._update_device_fields(
            device,
            device_name=device_name,
            device_type=device_type,
            preferred_format=preferred_format,
        )
        self._update_default_status(device, device_id, is_default)
        self._update_serial_number(device, serial_number)

        self._session.flush()

        # Sync serial numbers if updated and service is available
        if serial_number is not None and self._dedrm_service:
            self._sync_dedrm_keys()

        return device

    def _update_email_if_provided(
        self, device: EReaderDevice, device_id: int, email: str | None
    ) -> None:
        """Update device email if provided and different.

        Parameters
        ----------
        device : EReaderDevice
            Device to update.
        device_id : int
            Device identifier for conflict checking.
        email : str | None
            New email address (if provided).

        Raises
        ------
        ValueError
            If email conflicts with another device.
        """
        if email is not None and email != device.email:
            existing = self._devices.find_by_email(device.user_id, email)
            if existing is not None and existing.id != device_id:
                msg = "device_email_already_exists"
                raise ValueError(msg)
            device.email = email

    def _update_device_fields(
        self,
        device: EReaderDevice,
        *,
        device_name: str | None = None,
        device_type: str | None = None,
        preferred_format: EBookFormat | None = None,
    ) -> None:
        """Update device fields if provided.

        Parameters
        ----------
        device : EReaderDevice
            Device to update.
        device_name : str | None
            New device name (if provided).
        device_type : str | None
            New device type (if provided).
        preferred_format : EBookFormat | None
            New preferred format (if provided).
        """
        if device_name is not None:
            device.device_name = device_name

        if device_type is not None:
            device.device_type = device_type

        if preferred_format is not None:
            device.preferred_format = preferred_format

    def _update_default_status(
        self, device: EReaderDevice, device_id: int, is_default: bool | None
    ) -> None:
        """Update device default status if provided.

        Parameters
        ----------
        device : EReaderDevice
            Device to update.
        device_id : int
            Device identifier for exclusion from unset operation.
        is_default : bool | None
            New default status (if provided).
        """
        if is_default is not None:
            if is_default and not device.is_default:
                # Unset other defaults before setting this one
                self._unset_defaults(device.user_id, exclude_device_id=device_id)
            device.is_default = is_default

    def _update_serial_number(
        self, device: EReaderDevice, serial_number: str | None
    ) -> None:
        """Update device serial number if provided.

        Parameters
        ----------
        device : EReaderDevice
            Device to update.
        serial_number : str | None
            New serial number (if provided).
        """
        if serial_number is not None:
            device.serial_number = serial_number

    def _sync_dedrm_keys(self) -> None:
        """Sync all device serial numbers to DeDRM configuration."""
        if not self._dedrm_service:
            return

        from sqlmodel import select

        # We need to query all devices with serial numbers to ensure complete sync
        # Since EReaderRepository might not have a "find all with serial" method handy,
        # we can use the session directly or add a method to repo.
        # Direct session usage is acceptable here for this specific cross-cutting concern.
        stmt = select(EReaderDevice.serial_number).where(
            EReaderDevice.serial_number != None  # noqa: E711
        )
        serial_numbers = list(self._session.exec(stmt).all())
        valid_serials = [s for s in serial_numbers if s and s.strip()]

        if valid_serials:
            try:
                self._dedrm_service.update_configuration(valid_serials)
            except Exception:
                # Log but don't fail the request
                import logging

                logger = logging.getLogger(__name__)
                logger.exception("Failed to auto-sync DeDRM keys")

    def set_default_device(self, device_id: int) -> EReaderDevice:
        """Set a device as the default for its user.

        Parameters
        ----------
        device_id : int
            Device identifier.

        Returns
        -------
        EReaderDevice
            Updated e-reader device entity.

        Raises
        ------
        ValueError
            If the device does not exist.
        """
        device = self._devices.get(device_id)
        if device is None:
            msg = "device_not_found"
            raise ValueError(msg)

        self._unset_defaults(device.user_id, exclude_device_id=device_id)
        device.is_default = True
        self._session.flush()
        return device

    def delete_device(self, device_id: int) -> None:
        """Delete an e-reader device.

        Parameters
        ----------
        device_id : int
            Device identifier.

        Raises
        ------
        ValueError
            If the device does not exist.
        """
        device = self._devices.get(device_id)
        if device is None:
            msg = "device_not_found"
            raise ValueError(msg)

        self._devices.delete(device)
        self._session.flush()

    def _unset_defaults(
        self, user_id: int, exclude_device_id: int | None = None
    ) -> None:
        """Unset default status for all user devices except the excluded one.

        Parameters
        ----------
        user_id : int
            User identifier.
        exclude_device_id : int | None
            Device ID to exclude from unsetting (if any).
        """
        devices = list(self._devices.find_by_user(user_id))
        for device in devices:
            if device.is_default and (
                exclude_device_id is None or device.id != exclude_device_id
            ):
                device.is_default = False
