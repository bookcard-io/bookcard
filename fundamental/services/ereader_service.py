# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING WITHOUT LIMITATION THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""E-reader device service.

Encapsulates e-reader device management operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fundamental.models.auth import EReaderDevice

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.models.auth import EBookFormat
    from fundamental.repositories.ereader_repository import EReaderRepository


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
    ) -> None:
        self._session = session
        self._devices = devices

    def create_device(
        self,
        user_id: int,
        email: str,
        *,
        device_name: str | None = None,
        device_type: str = "kindle",
        preferred_format: EBookFormat | None = None,
        is_default: bool = False,
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
        )
        self._devices.add(device)
        self._session.flush()
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

        if email is not None and email != device.email:
            existing = self._devices.find_by_email(device.user_id, email)
            if existing is not None and existing.id != device_id:
                msg = "device_email_already_exists"
                raise ValueError(msg)
            device.email = email

        if device_name is not None:
            device.device_name = device_name

        if device_type is not None:
            device.device_type = device_type

        if preferred_format is not None:
            device.preferred_format = preferred_format

        if is_default is not None:
            if is_default and not device.is_default:
                # Unset other defaults before setting this one
                self._unset_defaults(device.user_id, exclude_device_id=device_id)
            device.is_default = is_default

        self._session.flush()
        return device

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
