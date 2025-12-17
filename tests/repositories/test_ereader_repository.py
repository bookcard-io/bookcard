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

"""Tests for e-reader repository."""

from __future__ import annotations

from bookcard.models.auth import EReaderDevice
from bookcard.repositories.ereader_repository import EReaderRepository
from tests.conftest import DummySession


def test_find_by_user_returns_user_devices() -> None:
    """Test find_by_user returns all devices for a user (covers lines 60-61)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]

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
        is_default=False,
    )

    session.add_exec_result([device1, device2])
    result = list(repo.find_by_user(1))
    assert len(result) == 2
    assert result[0].id == 1
    assert result[1].id == 2


def test_find_by_user_returns_empty() -> None:
    """Test find_by_user returns empty when user has no devices (covers lines 60-61)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = list(repo.find_by_user(999))
    assert len(result) == 0


def test_find_default_returns_default_device() -> None:
    """Test find_default returns default device for user (covers lines 76-80)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]

    default_device = EReaderDevice(
        id=1,
        user_id=1,
        email="default@example.com",
        device_type="kindle",
        is_default=True,
    )

    session.add_exec_result([default_device])
    result = repo.find_default(1)
    assert result is not None
    assert result.id == 1
    assert result.is_default is True


def test_find_default_returns_none() -> None:
    """Test find_default returns None when no default device (covers lines 76-80)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_default(1)
    assert result is None


def test_find_by_email_returns_matching_device() -> None:
    """Test find_by_email returns device with matching email (covers lines 97-100)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_type="kindle",
        is_default=False,
    )

    session.add_exec_result([device])
    result = repo.find_by_email(1, "device@example.com")
    assert result is not None
    assert result.id == 1
    assert result.email == "device@example.com"


def test_find_by_email_returns_none() -> None:
    """Test find_by_email returns None when not found (covers lines 97-100)."""
    session = DummySession()
    repo = EReaderRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_email(1, "nonexistent@example.com")
    assert result is None
