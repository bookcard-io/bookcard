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

"""User settings operations (create/update/read)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import select

from bookcard.models.auth import UserSetting

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.repositories.admin_repositories import SettingRepository
    from bookcard.repositories.user_repository import UserRepository


class UserSettingsService:
    """Handles user settings."""

    def __init__(
        self,
        session: Session,
        user_repo: UserRepository,
        setting_repo: SettingRepository,
    ) -> None:
        self._session = session
        self._users = user_repo
        self._settings = setting_repo

    def upsert_setting(
        self, user_id: int, key: str, value: str, description: str | None = None
    ) -> UserSetting:
        """Create or update a user setting.

        Parameters
        ----------
        user_id : int
            User identifier.
        key : str
            Setting key.
        value : str
            Setting value.
        description : str | None
            Optional description.

        Returns
        -------
        UserSetting
            Created or updated setting.

        Raises
        ------
        ValueError
            If the user does not exist.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        stmt = select(UserSetting).where(
            UserSetting.user_id == user_id, UserSetting.key == key
        )
        existing_setting = self._session.exec(stmt).first()

        if existing_setting is not None:
            existing_setting.value = value
            if description is not None:
                existing_setting.description = description
            existing_setting.updated_at = datetime.now(UTC)
            self._session.flush()
            return existing_setting

        new_setting = UserSetting(
            user_id=user_id,
            key=key,
            value=value,
            description=description,
        )
        self._session.add(new_setting)
        self._session.flush()
        return new_setting

    def get_setting(self, user_id: int, key: str) -> UserSetting | None:
        """Return a setting by key for a user."""
        return self._settings.get_by_key(user_id, key)

    def get_all_settings(self, user_id: int) -> list[UserSetting]:
        """Return all settings for a user."""
        stmt = select(UserSetting).where(UserSetting.user_id == user_id)
        return list(self._session.exec(stmt).all())
