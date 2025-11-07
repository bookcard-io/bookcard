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

"""FastAPI dependency providers.

Provides request-scoped database sessions and repository factories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session  # noqa: TC002

from rainbow.database import get_session
from rainbow.repositories.user_repository import UserRepository
from rainbow.services.security import JWTManager, SecurityTokenError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from rainbow.models.auth import User


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
    try:
        claims = jwt_mgr.decode_token(token)
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
