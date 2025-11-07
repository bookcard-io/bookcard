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

"""User service.

Encapsulates user profile operations and validations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from fundamental.models.auth import User

if TYPE_CHECKING:
    from collections.abc import Iterable

    from fundamental.repositories.user_repository import UserRepository


class UserService:
    """Operations for retrieving and updating user profiles.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    users : UserRepository
        Repository providing user persistence operations.
    """

    def __init__(self, session: Session, users: UserRepository) -> None:  # type: ignore[type-arg]
        self._session = session
        self._users = users

    def get(self, user_id: int) -> User | None:
        """Return a user by id or ``None`` if missing."""
        return self._users.get(user_id)

    def update_profile(
        self, user_id: int, *, username: str | None = None, email: str | None = None
    ) -> User:
        """Update username and/or email ensuring uniqueness.

        Raises
        ------
        ValueError
            If the desired username or email is already in use by another user.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        if username is not None and username != user.username:
            exists = self._users.find_by_username(username)
            if exists is not None and exists.id != user.id:
                msg = "username_already_exists"
                raise ValueError(msg)
            user.username = username

        if email is not None and email != user.email:
            exists = self._users.find_by_email(email)
            if exists is not None and exists.id != user.id:
                msg = "email_already_exists"
                raise ValueError(msg)
            user.email = email

        self._session.flush()
        return user

    def list_users(self, limit: int | None = None, offset: int = 0) -> Iterable[User]:
        """List users with pagination.

        Parameters
        ----------
        limit : int | None
            Maximum number of users to return.
        offset : int
            Number of users to skip.

        Returns
        -------
        Iterable[User]
            User entities.
        """
        return self._users.list(limit=limit, offset=offset)

    def get_with_relationships(self, user_id: int) -> User | None:
        """Get user by ID with eager-loaded relationships.

        Loads user with ereader_devices and roles (including nested role data).

        Uses `selectinload()` which executes separate SELECT queries with IN clauses
        to avoid cartesian product issues when loading multiple one-to-many relationships.

        Alternative: `joinedload()` would use LEFT OUTER JOINs in a single query,
        but can cause row multiplication (cartesian product) with multiple one-to-many
        relationships (e.g., user with 3 devices and 2 roles = 6 rows returned).

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        User | None
            User with relationships loaded, or None if not found.
        """
        from fundamental.models.auth import UserRole

        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                # selectinload: Executes separate SELECT with IN clause
                # SELECT * FROM ereader_devices WHERE user_id IN (1)
                # SELECT * FROM user_roles WHERE user_id IN (1)
                # SELECT * FROM roles WHERE id IN (role_ids)
                selectinload(User.ereader_devices),
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )
        return self._session.exec(stmt).first()

    def list_users_with_relationships(
        self, limit: int | None = None, offset: int = 0
    ) -> list[User]:
        """List users with eager-loaded relationships.

        Loads users with ereader_devices and roles (including nested role data).

        Uses `selectinload()` which executes separate SELECT queries with IN clauses
        to avoid cartesian product issues when loading multiple one-to-many relationships.

        Example queries executed:
        1. SELECT * FROM users LIMIT 10 OFFSET 0
        2. SELECT * FROM ereader_devices WHERE user_id IN (1, 2, 3, ...)
        3. SELECT * FROM user_roles WHERE user_id IN (1, 2, 3, ...)
        4. SELECT * FROM roles WHERE id IN (role_ids)

        Alternative: `joinedload()` would use LEFT OUTER JOINs in a single query,
        but can cause row multiplication (cartesian product) with multiple one-to-many
        relationships (e.g., 10 users with avg 3 devices and 2 roles = 60 rows returned).

        Parameters
        ----------
        limit : int | None
            Maximum number of users to return.
        offset : int
            Number of users to skip.

        Returns
        -------
        list[User]
            Users with relationships loaded.
        """
        from fundamental.models.auth import UserRole

        stmt = (
            select(User)
            .offset(offset)
            .options(
                # selectinload: Executes separate SELECT with IN clause
                # Avoids cartesian product issues with multiple one-to-many relationships
                selectinload(User.ereader_devices),
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self._session.exec(stmt).all())

    def update_admin_status(self, user_id: int, is_admin: bool) -> User:
        """Update user admin status.

        Parameters
        ----------
        user_id : int
            User identifier.
        is_admin : bool
            New admin status.

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If the user does not exist.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        user.is_admin = is_admin
        self._session.flush()
        return user

    def update_active_status(self, user_id: int, is_active: bool) -> User:
        """Update user active status.

        Parameters
        ----------
        user_id : int
            User identifier.
        is_active : bool
            New active status.

        Returns
        -------
        User
            Updated user entity.

        Raises
        ------
        ValueError
            If the user does not exist.
        """
        user = self._users.get(user_id)
        if user is None:
            msg = "user_not_found"
            raise ValueError(msg)

        user.is_active = is_active
        self._session.flush()
        return user
