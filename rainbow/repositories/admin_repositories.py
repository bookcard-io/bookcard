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

"""Admin-related repositories for settings and invites."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import desc, select

from rainbow.models.auth import Invite, User, UserSetting
from rainbow.repositories.base import Repository

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
