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
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for e-reader repository."""

from __future__ import annotations

from fundamental.models.auth import EReaderDevice
from fundamental.repositories.ereader_repository import EReaderRepository
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
