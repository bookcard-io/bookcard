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

"""Admin-related repositories for settings and invites."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import desc, select

from fundamental.models.auth import Invite, User, UserSetting
from fundamental.repositories.base import Repository

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlmodel import Session


class UserAdminRepository(Repository[User]):
    """Repository for `User` entity with list helpers."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, User)

    def list_users(self, limit: int = 100, offset: int = 0) -> Iterable[User]:
        """Return users with simple pagination."""
        stmt = select(User).offset(offset).limit(limit)
        return self._session.exec(stmt).all()  # type: ignore[no-matching-overload]


class SettingRepository(Repository[UserSetting]):
    """Repository for `UserSetting` with user and key lookup."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, UserSetting)

    def get_by_key(self, user_id: int, key: str) -> UserSetting | None:
        """Return setting by user ID and key if present.

        Parameters
        ----------
        user_id : int
            User identifier.
        key : str
            Setting key.

        Returns
        -------
        UserSetting | None
            User setting entity if found, None otherwise.
        """
        stmt = select(UserSetting).where(
            UserSetting.user_id == user_id, UserSetting.key == key
        )
        return self._session.exec(stmt).first()  # type: ignore[no-matching-overload]


class InviteRepository(Repository[Invite]):
    """Repository for `Invite` with list helpers."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Invite)

    def list_all(self, limit: int = 100) -> Iterable[Invite]:
        """Return most recent invites up to a limit."""
        stmt = select(Invite).order_by(desc(Invite.created_at)).limit(limit)
        return self._session.exec(stmt).all()  # type: ignore[no-matching-overload]

    def get_by_token(self, token: str) -> Invite | None:
        """Return an invite by token if it exists.

        Parameters
        ----------
        token : str
            Invite token.

        Returns
        -------
        Invite | None
            Invite entity if found, None otherwise.
        """
        stmt = select(Invite).where(Invite.token == token)
        return self._session.exec(stmt).first()  # type: ignore[no-matching-overload]
