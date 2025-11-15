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

"""Tests for device routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import fundamental.api.routes.devices as devices
from fundamental.models.auth import EBookFormat, EReaderDevice, User
from tests.conftest import DummySession


@pytest.fixture
def session() -> DummySession:
    """Create a DummySession instance."""
    return DummySession()


@pytest.fixture
def current_user() -> User:
    """Create a test user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


def test_create_device_success(session: DummySession, current_user: User) -> None:
    """Test create_device succeeds (covers lines 69-93)."""
    from fundamental.api.schemas.auth import EReaderDeviceCreate

    payload = EReaderDeviceCreate(
        email="device@example.com",
        device_name="My Kindle",
        device_type="kindle",
        preferred_format="epub",
        is_default=True,
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="My Kindle",
        device_type="kindle",
        preferred_format=EBookFormat.EPUB,
        is_default=True,
    )

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.create_device.return_value = device
        mock_service_class.return_value = mock_service

        result = devices.create_device(session, current_user, payload)  # type: ignore[arg-type]
        assert result.id == 1
        assert result.email == "device@example.com"
        mock_service.create_device.assert_called_once()
        session.commit()


def test_create_device_invalid_format_suppressed(
    session: DummySession, current_user: User
) -> None:
    """Test create_device suppresses invalid format (covers lines 72-76)."""
    from fundamental.api.schemas.auth import EReaderDeviceCreate

    payload = EReaderDeviceCreate(
        email="device@example.com",
        preferred_format="invalid_format",
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
        preferred_format=None,
    )

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.create_device.return_value = device
        mock_service_class.return_value = mock_service

        result = devices.create_device(session, current_user, payload)  # type: ignore[arg-type]
        assert result.id == 1
        # Verify preferred_format was None (invalid format suppressed)
        call_args = mock_service.create_device.call_args
        assert call_args[1]["preferred_format"] is None


def test_create_device_email_exists(session: DummySession, current_user: User) -> None:
    """Test create_device raises 409 when email exists (covers lines 89-93)."""
    from fundamental.api.schemas.auth import EReaderDeviceCreate

    payload = EReaderDeviceCreate(email="existing@example.com")

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.create_device.side_effect = ValueError(
            "device_email_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            devices.create_device(session, current_user, payload)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "device_email_already_exists"


def test_create_device_other_value_error(
    session: DummySession, current_user: User
) -> None:
    """Test create_device re-raises ValueError with other messages (covers line 93)."""
    from fundamental.api.schemas.auth import EReaderDeviceCreate

    payload = EReaderDeviceCreate(email="device@example.com")

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.create_device.side_effect = ValueError("other_error")
        mock_service_class.return_value = mock_service

        with pytest.raises(ValueError, match="other_error"):
            devices.create_device(session, current_user, payload)  # type: ignore[arg-type]


def test_list_devices_success(session: DummySession, current_user: User) -> None:
    """Test list_devices returns user devices (covers lines 115-117)."""
    device1 = EReaderDevice(
        id=1,
        user_id=1,
        email="device1@example.com",
        device_type="kindle",
    )
    device2 = EReaderDevice(
        id=2,
        user_id=1,
        email="device2@example.com",
        device_type="kobo",
    )

    with patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_user.return_value = [device1, device2]
        mock_repo_class.return_value = mock_repo

        result = devices.list_devices(session, current_user)  # type: ignore[arg-type]
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2


def test_get_device_success(session: DummySession, current_user: User) -> None:
    """Test get_device returns device (covers lines 147-156)."""
    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )

    with patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        result = devices.get_device(1, session, current_user)  # type: ignore[arg-type]
        assert result.id == 1
        assert result.email == "device@example.com"


def test_get_device_not_found(session: DummySession, current_user: User) -> None:
    """Test get_device raises 404 when device not found (covers lines 149-150)."""
    with patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            devices.get_device(999, session, current_user)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "device_not_found"


def test_get_device_permission_denied(
    session: DummySession, current_user: User
) -> None:
    """Test get_device raises 403 when device belongs to different user (covers lines 153-154)."""
    device = EReaderDevice(
        id=1,
        user_id=2,  # Different user
        email="device@example.com",
        device_type="kindle",
    )

    with patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            devices.get_device(1, session, current_user)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "permission_denied"


def test_update_device_success(session: DummySession, current_user: User) -> None:
    """Test update_device succeeds (covers lines 189-223)."""
    from fundamental.api.schemas.auth import EReaderDeviceUpdate

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )
    updated_device = EReaderDevice(
        id=1,
        user_id=1,
        email="newdevice@example.com",
        device_type="kobo",
        preferred_format=EBookFormat.MOBI,
    )
    payload = EReaderDeviceUpdate(
        email="newdevice@example.com",
        device_type="kobo",
        preferred_format="mobi",
    )

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_device.return_value = updated_device
        mock_service_class.return_value = mock_service

        result = devices.update_device(1, session, current_user, payload)  # type: ignore[arg-type]
        assert result.id == 1
        assert result.email == "newdevice@example.com"
        session.commit()


def test_update_device_not_found(session: DummySession, current_user: User) -> None:
    """Test update_device raises 404 when device not found (covers lines 191-192)."""
    from fundamental.api.schemas.auth import EReaderDeviceUpdate

    payload = EReaderDeviceUpdate(email="newdevice@example.com")

    with patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            devices.update_device(999, session, current_user, payload)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "device_not_found"


def test_update_device_service_not_found(
    session: DummySession, current_user: User
) -> None:
    """Test update_device raises 404 when service raises device_not_found (covers line 220)."""
    from fundamental.api.schemas.auth import EReaderDeviceUpdate

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )
    payload = EReaderDeviceUpdate(email="newdevice@example.com")

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_device.side_effect = ValueError("device_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            devices.update_device(1, session, current_user, payload)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "device_not_found"


def test_update_device_permission_denied(
    session: DummySession, current_user: User
) -> None:
    """Test update_device raises 403 when device belongs to different user (covers lines 195-196)."""
    from fundamental.api.schemas.auth import EReaderDeviceUpdate

    device = EReaderDevice(
        id=1,
        user_id=2,  # Different user
        email="device@example.com",
        device_type="kindle",
    )
    payload = EReaderDeviceUpdate(email="newdevice@example.com")

    with patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            devices.update_device(1, session, current_user, payload)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "permission_denied"


def test_update_device_invalid_format_suppressed(
    session: DummySession, current_user: User
) -> None:
    """Test update_device suppresses invalid format (covers lines 200-204)."""
    from fundamental.api.schemas.auth import EReaderDeviceUpdate

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )
    updated_device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
        preferred_format=None,
    )
    payload = EReaderDeviceUpdate(preferred_format="invalid_format")

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_device.return_value = updated_device
        mock_service_class.return_value = mock_service

        result = devices.update_device(1, session, current_user, payload)  # type: ignore[arg-type]
        assert result.id == 1
        # Verify preferred_format was None (invalid format suppressed)
        call_args = mock_service.update_device.call_args
        assert call_args[1]["preferred_format"] is None


def test_update_device_email_exists(session: DummySession, current_user: User) -> None:
    """Test update_device raises 409 when email exists (covers lines 221-222)."""
    from fundamental.api.schemas.auth import EReaderDeviceUpdate

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )
    payload = EReaderDeviceUpdate(email="existing@example.com")

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_device.side_effect = ValueError(
            "device_email_already_exists"
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            devices.update_device(1, session, current_user, payload)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "device_email_already_exists"


def test_update_device_other_value_error(
    session: DummySession, current_user: User
) -> None:
    """Test update_device re-raises ValueError with other messages (covers lines 220, 223)."""
    from fundamental.api.schemas.auth import EReaderDeviceUpdate

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )
    payload = EReaderDeviceUpdate(email="newdevice@example.com")

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.update_device.side_effect = ValueError("other_error")
        mock_service_class.return_value = mock_service

        with pytest.raises(ValueError, match="other_error"):
            devices.update_device(1, session, current_user, payload)  # type: ignore[arg-type]


def test_delete_device_success(session: DummySession, current_user: User) -> None:
    """Test delete_device succeeds (covers lines 248-263)."""
    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.delete_device.return_value = None
        mock_service_class.return_value = mock_service

        devices.delete_device(1, session, current_user)  # type: ignore[arg-type]
        mock_service.delete_device.assert_called_once_with(1)
        session.commit()


def test_delete_device_not_found(session: DummySession, current_user: User) -> None:
    """Test delete_device raises 404 when device not found (covers lines 250-251)."""
    with patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            devices.delete_device(999, session, current_user)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "device_not_found"


def test_delete_device_permission_denied(
    session: DummySession, current_user: User
) -> None:
    """Test delete_device raises 403 when device belongs to different user (covers lines 254-255)."""
    device = EReaderDevice(
        id=1,
        user_id=2,  # Different user
        email="device@example.com",
        device_type="kindle",
    )

    with patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            devices.delete_device(1, session, current_user)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "permission_denied"


def test_delete_device_service_error(session: DummySession, current_user: User) -> None:
    """Test delete_device raises 404 when service raises ValueError (covers lines 262-263)."""
    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
    )

    with (
        patch("fundamental.api.routes.devices.EReaderRepository") as mock_repo_class,
        patch("fundamental.api.routes.devices.EReaderService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo.get.return_value = device
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.delete_device.side_effect = ValueError("device_not_found")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            devices.delete_device(1, session, current_user)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "device_not_found"
