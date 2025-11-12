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

"""FastAPI dependency providers.

Provides request-scoped database sessions and repository factories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session  # noqa: TC002

from fundamental.database import get_session
from fundamental.models.auth import User  # noqa: TC001
from fundamental.repositories.user_repository import (
    TokenBlacklistRepository,
    UserRepository,
)
from fundamental.services.security import JWTManager, SecurityTokenError

if TYPE_CHECKING:
    from collections.abc import Iterator


def get_db_session(request: Request) -> Iterator[Session]:
    """Yield a request-scoped database session.

    Parameters
    ----------
    request : Request
        Incoming FastAPI request containing application state.

    Yields
    ------
    Iterator[Session]
        Active SQLModel session bound to the app's engine.
    """
    engine = request.app.state.engine
    with get_session(engine) as session:
        yield session


def get_current_user(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> User:
    """Decode JWT from Authorization header and return the current user.

    Raises
    ------
    HTTPException
        If the token is missing, invalid, or the user does not exist.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_token"
        )
    token = auth_header.removeprefix("Bearer ")
    jwt_mgr = JWTManager(request.app.state.config)

    # Create blacklist repository for checking
    blacklist_repo = TokenBlacklistRepository(session)

    try:
        # Check blacklist during decode
        claims = jwt_mgr.decode_token(
            token,
            is_blacklisted=lambda jti: blacklist_repo.is_blacklisted(jti),
        )
    except SecurityTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token"
        ) from err
    user_id = int(claims.get("sub", 0))
    repo = UserRepository(session)
    user = repo.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found"
        )
    return user


def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require the current user to be an admin.

    Parameters
    ----------
    current_user : User
        Current authenticated user from get_current_user.

    Returns
    -------
    User
        Admin user.

    Raises
    ------
    HTTPException
        If the user is not an admin (403).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="admin_required"
        )
    return current_user
