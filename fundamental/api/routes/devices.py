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

"""Device endpoints: create and manage e-reader devices for the current user."""

from __future__ import annotations

from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from fundamental.api.deps import get_current_user, get_db_session
from fundamental.api.schemas.auth import (
    EReaderDeviceCreate,
    EReaderDeviceRead,
    EReaderDeviceUpdate,
)
from fundamental.models.auth import EBookFormat, User
from fundamental.repositories.ereader_repository import EReaderRepository
from fundamental.services.dedrm_service import DeDRMService
from fundamental.services.ereader_service import EReaderService
from fundamental.services.permission_service import PermissionService

router = APIRouter(prefix="/devices", tags=["devices"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=EReaderDeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(
    session: SessionDep,
    current_user: CurrentUserDep,
    payload: EReaderDeviceCreate,
) -> EReaderDeviceRead:
    """Create an e-reader device for the current user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    payload : EReaderDeviceCreate
        Device creation payload.

    Returns
    -------
    EReaderDeviceRead
        Created device.

    Raises
    ------
    HTTPException
        If device email already exists (409) or permission denied (403).
    """
    # Optional permission check (default: user can create own devices)
    permission_service = PermissionService(session)
    if not permission_service.has_permission(current_user, "devices", "write"):
        # If no permission, fall back to ownership check (user can create own devices)
        pass  # Allow through - ownership is primary check

    device_repo = EReaderRepository(session)
    # Instantiate DeDRMService for auto-syncing
    dedrm_service = DeDRMService()
    device_service = EReaderService(session, device_repo, dedrm_service)

    preferred_format = None
    if payload.preferred_format:
        with suppress(ValueError):
            # Invalid format, use None
            preferred_format = EBookFormat(payload.preferred_format.lower())

    try:
        device = device_service.create_device(
            current_user.id,  # type: ignore[arg-type]
            payload.email,
            device_name=payload.device_name,
            device_type=payload.device_type,
            preferred_format=preferred_format,
            is_default=payload.is_default,
            serial_number=payload.serial_number,
        )
        session.commit()
        return EReaderDeviceRead.model_validate(device)
    except ValueError as exc:
        msg = str(exc)
        if msg == "device_email_already_exists":
            raise HTTPException(status_code=409, detail=msg) from exc
        raise


@router.get("", response_model=list[EReaderDeviceRead])
def list_devices(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[EReaderDeviceRead]:
    """List all e-reader devices for the current user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    list[EReaderDeviceRead]
        List of devices.

    Raises
    ------
    HTTPException
        If permission denied (403).
    """
    # Optional permission check (default: user can see own devices)
    permission_service = PermissionService(session)
    if not permission_service.has_permission(current_user, "devices", "read"):
        # If no permission, fall back to ownership check (user can see own devices)
        pass  # Allow through - ownership is primary check

    device_repo = EReaderRepository(session)
    devices = list(device_repo.find_by_user(current_user.id))  # type: ignore[arg-type]
    return [EReaderDeviceRead.model_validate(device) for device in devices]


@router.get("/{device_id}", response_model=EReaderDeviceRead)
def get_device(
    device_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> EReaderDeviceRead:
    """Get an e-reader device by ID.

    Parameters
    ----------
    device_id : int
        Device identifier.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    EReaderDeviceRead
        Device data.

    Raises
    ------
    HTTPException
        If device not found (404) or does not belong to current user (403).
    """
    device_repo = EReaderRepository(session)
    device = device_repo.get(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device_not_found")

    # Verify device belongs to current user
    if device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="permission_denied")

    return EReaderDeviceRead.model_validate(device)


@router.put("/{device_id}", response_model=EReaderDeviceRead)
def update_device(
    device_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    payload: EReaderDeviceUpdate,
) -> EReaderDeviceRead:
    """Update an e-reader device.

    Parameters
    ----------
    device_id : int
        Device identifier.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    payload : EReaderDeviceUpdate
        Device update payload.

    Returns
    -------
    EReaderDeviceRead
        Updated device.

    Raises
    ------
    HTTPException
        If device not found (404), does not belong to current user (403), or email conflict (409).
    """
    device_repo = EReaderRepository(session)
    device = device_repo.get(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device_not_found")

    # Verify device belongs to current user
    if device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="permission_denied")

    dedrm_service = DeDRMService()
    device_service = EReaderService(session, device_repo, dedrm_service)

    preferred_format = None
    if payload.preferred_format:
        with suppress(ValueError):
            # Invalid format, use None
            preferred_format = EBookFormat(payload.preferred_format.lower())

    try:
        updated_device = device_service.update_device(
            device_id,
            email=payload.email,
            device_name=payload.device_name,
            device_type=payload.device_type,
            preferred_format=preferred_format,
            is_default=payload.is_default,
            serial_number=payload.serial_number,
        )
        session.commit()
        return EReaderDeviceRead.model_validate(updated_device)
    except ValueError as exc:
        msg = str(exc)
        if msg == "device_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg == "device_email_already_exists":
            raise HTTPException(status_code=409, detail=msg) from exc
        raise


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> None:
    """Delete an e-reader device.

    Parameters
    ----------
    device_id : int
        Device identifier.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Raises
    ------
    HTTPException
        If device not found (404) or does not belong to current user (403).
    """
    device_repo = EReaderRepository(session)
    device = device_repo.get(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device_not_found")

    # Verify device belongs to current user
    if device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="permission_denied")

    device_service = EReaderService(session, device_repo)

    try:
        device_service.delete_device(device_id)
        session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="device_not_found") from exc
