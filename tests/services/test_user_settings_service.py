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

"""Tests for user settings service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.models.auth import User, UserSetting
from bookcard.services.user_settings_service import UserSettingsService
from tests.conftest import DummySession

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session() -> DummySession:
    """Return a fresh DummySession."""
    return DummySession()


@pytest.fixture
def user_repo() -> MagicMock:
    """Return a mock UserRepository."""
    return MagicMock(spec=["get"])


@pytest.fixture
def setting_repo() -> MagicMock:
    """Return a mock SettingRepository."""
    return MagicMock(spec=["get_by_key"])


@pytest.fixture
def service(
    session: DummySession,
    user_repo: MagicMock,
    setting_repo: MagicMock,
) -> UserSettingsService:
    """Return a UserSettingsService with mocked dependencies."""
    return UserSettingsService(
        session=session,  # type: ignore[arg-type]
        user_repo=user_repo,
        setting_repo=setting_repo,
    )


@pytest.fixture
def sample_user() -> User:
    """Return a sample user for tests."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
    )


@pytest.fixture
def sample_setting() -> UserSetting:
    """Return a sample setting for tests."""
    return UserSetting(
        id=1,
        user_id=1,
        key="theme",
        value="dark",
        description="User theme preference",
    )


# ---------------------------------------------------------------------------
# upsert_setting tests
# ---------------------------------------------------------------------------


class TestUpsertSetting:
    """Tests for UserSettingsService.upsert_setting."""

    def test_upsert_setting_creates_new(
        self,
        service: UserSettingsService,
        session: DummySession,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Upsert creates a new setting when none exists."""
        user_repo.get.return_value = sample_user
        session.add_exec_result([None])  # No existing setting

        result = service.upsert_setting(1, "theme", "dark", "Theme preference")

        assert result.user_id == 1
        assert result.key == "theme"
        assert result.value == "dark"
        assert result.description == "Theme preference"
        assert result in session.added
        assert session.flush_count == 1

    def test_upsert_setting_creates_new_no_description(
        self,
        service: UserSettingsService,
        session: DummySession,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Upsert creates a new setting without description."""
        user_repo.get.return_value = sample_user
        session.add_exec_result([None])

        result = service.upsert_setting(1, "theme", "dark")

        assert result.description is None

    def test_upsert_setting_updates_existing(
        self,
        service: UserSettingsService,
        session: DummySession,
        user_repo: MagicMock,
        sample_user: User,
        sample_setting: UserSetting,
    ) -> None:
        """Upsert updates an existing setting."""
        user_repo.get.return_value = sample_user
        session.add_exec_result([sample_setting])

        result = service.upsert_setting(1, "theme", "light", "New description")

        assert result.value == "light"
        assert result.description == "New description"
        assert result.updated_at is not None
        assert session.flush_count == 1

    def test_upsert_setting_updates_value_only(
        self,
        service: UserSettingsService,
        session: DummySession,
        user_repo: MagicMock,
        sample_user: User,
        sample_setting: UserSetting,
    ) -> None:
        """Upsert updates value but keeps existing description when not provided."""
        user_repo.get.return_value = sample_user
        original_desc = sample_setting.description
        session.add_exec_result([sample_setting])

        result = service.upsert_setting(1, "theme", "light")

        assert result.value == "light"
        assert result.description == original_desc

    def test_upsert_setting_user_not_found(
        self,
        service: UserSettingsService,
        user_repo: MagicMock,
    ) -> None:
        """Upsert fails when user not found."""
        user_repo.get.return_value = None

        with pytest.raises(ValueError, match="user_not_found"):
            service.upsert_setting(999, "theme", "dark")


# ---------------------------------------------------------------------------
# get_setting tests
# ---------------------------------------------------------------------------


class TestGetSetting:
    """Tests for UserSettingsService.get_setting."""

    def test_get_setting_found(
        self,
        service: UserSettingsService,
        setting_repo: MagicMock,
        sample_setting: UserSetting,
    ) -> None:
        """Get returns setting when found."""
        setting_repo.get_by_key.return_value = sample_setting

        result = service.get_setting(1, "theme")

        assert result is sample_setting
        setting_repo.get_by_key.assert_called_once_with(1, "theme")

    def test_get_setting_not_found(
        self,
        service: UserSettingsService,
        setting_repo: MagicMock,
    ) -> None:
        """Get returns None when setting not found."""
        setting_repo.get_by_key.return_value = None

        result = service.get_setting(1, "nonexistent")

        assert result is None


# ---------------------------------------------------------------------------
# get_all_settings tests
# ---------------------------------------------------------------------------


class TestGetAllSettings:
    """Tests for UserSettingsService.get_all_settings."""

    def test_get_all_settings_returns_list(
        self,
        service: UserSettingsService,
        session: DummySession,
    ) -> None:
        """Get all returns list of settings for user."""
        setting1 = UserSetting(id=1, user_id=1, key="theme", value="dark")
        setting2 = UserSetting(id=2, user_id=1, key="language", value="en")
        session.add_exec_result([setting1, setting2])

        result = service.get_all_settings(1)

        assert len(result) == 2
        assert setting1 in result
        assert setting2 in result

    def test_get_all_settings_empty(
        self,
        service: UserSettingsService,
        session: DummySession,
    ) -> None:
        """Get all returns empty list when user has no settings."""
        session.add_exec_result([])

        result = service.get_all_settings(1)

        assert result == []
