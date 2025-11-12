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

"""Tests for e-reader service."""

from __future__ import annotations

import pytest

from fundamental.models.auth import EBookFormat, EReaderDevice
from fundamental.repositories.ereader_repository import EReaderRepository
from fundamental.services.ereader_service import EReaderService
from tests.conftest import DummySession


def test_create_device_email_already_exists() -> None:
    """Test create_device raises ValueError when email exists (covers lines 97-100)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    existing_device = EReaderDevice(
        id=1,
        user_id=1,
        email="existing@example.com",
        device_type="kindle",
    )

    session.add_exec_result([existing_device])

    with pytest.raises(ValueError, match="device_email_already_exists"):
        service.create_device(1, "existing@example.com")


def test_create_device_set_as_default() -> None:
    """Test create_device unsets other defaults when is_default=True (covers lines 103-104)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    default_device = EReaderDevice(
        id=1,
        user_id=1,
        email="olddefault@example.com",
        device_type="kindle",
        is_default=True,
    )

    session.add_exec_result([])  # find_by_email() call
    session.add_exec_result([default_device])  # find_by_user() call

    device = service.create_device(
        1,
        "newdevice@example.com",
        is_default=True,
    )

    assert device.is_default is True
    assert default_device.is_default is False


def test_update_device_not_found() -> None:
    """Test update_device raises ValueError when device not found (covers lines 155-158)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="device_not_found"):
        service.update_device(999, email="new@example.com")


def test_update_device_email_conflict() -> None:
    """Test update_device raises ValueError when email conflicts (covers lines 160-164)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="old@example.com",
        device_type="kindle",
    )

    existing_device = EReaderDevice(
        id=2,
        user_id=1,
        email="existing@example.com",
        device_type="kobo",
    )

    session.add(device)  # Add to session for get() lookup
    session.add_exec_result([existing_device])  # find_by_email() call

    with pytest.raises(ValueError, match="device_email_already_exists"):
        service.update_device(1, email="existing@example.com")


def test_update_device_updates_all_fields() -> None:
    """Test update_device updates all provided fields (covers lines 165, 168, 171, 174)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="old@example.com",
        device_name="Old Device",
        device_type="kindle",
        preferred_format=None,
        is_default=False,
    )

    session.add(device)  # Add to session for get() lookup
    session.add_exec_result([])  # find_by_email() call

    result = service.update_device(
        1,
        email="new@example.com",
        device_name="New Device",
        device_type="kobo",
        preferred_format=EBookFormat.EPUB,
    )

    assert result.email == "new@example.com"
    assert result.device_name == "New Device"
    assert result.device_type == "kobo"
    assert result.preferred_format == EBookFormat.EPUB


def test_update_device_email_no_change() -> None:
    """Test update_device doesn't check when email unchanged (covers lines 160-165)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )

    session.add(device)  # Add to session for get() lookup

    result = service.update_device(1, email="device@example.com")

    assert result.email == "device@example.com"
    # Should not call find_by_email when email unchanged


def test_update_device_set_as_default() -> None:
    """Test update_device unsets others when setting as default (covers lines 176-180)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
        is_default=False,
    )

    default_device = EReaderDevice(
        id=2,
        user_id=1,
        email="default@example.com",
        device_type="kobo",
        is_default=True,
    )

    session.add(device)  # Add to session for get() lookup
    session.add_exec_result([default_device])  # find_by_user() call

    result = service.update_device(1, is_default=True)

    assert result.is_default is True
    assert default_device.is_default is False


def test_set_default_device_not_found() -> None:
    """Test set_default_device raises ValueError when device not found (covers lines 203-206)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="device_not_found"):
        service.set_default_device(999)


def test_set_default_device_unsets_others() -> None:
    """Test set_default_device unsets other defaults (covers lines 203-211)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
        is_default=False,
    )

    default_device = EReaderDevice(
        id=2,
        user_id=1,
        email="default@example.com",
        device_type="kobo",
        is_default=True,
    )

    session.add(device)  # Add to session for get() lookup
    session.add_exec_result([default_device])  # find_by_user() call

    result = service.set_default_device(1)

    assert result.is_default is True
    assert default_device.is_default is False


def test_delete_device_success() -> None:
    """Test delete_device succeeds (covers lines 231-232)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )

    session.add(device)  # Add to session for get() lookup

    service.delete_device(1)

    assert device in session.deleted


def test_delete_device_not_found() -> None:
    """Test delete_device raises ValueError when device not found (covers lines 226-229)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="device_not_found"):
        service.delete_device(999)


def test_unset_defaults_unsets_all() -> None:
    """Test _unset_defaults unsets all default devices (covers lines 246-251)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    device1 = EReaderDevice(
        id=1,
        user_id=1,
        email="device1@example.com",
        device_type="kindle",
        is_default=True,
    )

    device2 = EReaderDevice(
        id=2,
        user_id=1,
        email="device2@example.com",
        device_type="kobo",
        is_default=True,
    )

    session.add_exec_result([device1, device2])

    service._unset_defaults(1)

    assert device1.is_default is False
    assert device2.is_default is False


def test_unset_defaults_excludes_device() -> None:
    """Test _unset_defaults excludes specified device (covers lines 246-251)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]
    service = EReaderService(session, repo)  # type: ignore[arg-type]

    device1 = EReaderDevice(
        id=1,
        user_id=1,
        email="device1@example.com",
        device_type="kindle",
        is_default=True,
    )

    device2 = EReaderDevice(
        id=2,
        user_id=1,
        email="device2@example.com",
        device_type="kobo",
        is_default=True,
    )

    session.add_exec_result([device1, device2])

    service._unset_defaults(1, exclude_device_id=1)

    assert device1.is_default is True  # Excluded, should remain default
    assert device2.is_default is False  # Should be unset
