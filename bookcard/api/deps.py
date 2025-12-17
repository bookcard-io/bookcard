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

from contextlib import suppress
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session  # noqa: TC002

from bookcard.database import get_session
from bookcard.models.auth import User  # noqa: TC001
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.repositories.kobo_repository import (
    KoboAuthTokenRepository,
)
from bookcard.repositories.user_repository import (
    TokenBlacklistRepository,
    UserRepository,
)
from bookcard.services.config_service import BasicConfigService, LibraryService
from bookcard.services.kobo.auth_service import KoboAuthService
from bookcard.services.oidc_auth_service import OIDCAuthError, OIDCAuthService
from bookcard.services.opds.auth_service import OpdsAuthService
from bookcard.services.permission_service import PermissionService
from bookcard.services.security import JWTManager, PasswordHasher, SecurityTokenError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


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

    # Prefer local JWT (existing behavior). When OIDC is enabled, we can
    # optionally fall back to validating a provider-issued token.
    with suppress(SecurityTokenError):
        return _get_user_from_local_jwt(request, session, token)

    if request.app.state.config.oidc_enabled:
        return _get_user_from_oidc_token(request, session, token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token"
    )


def _get_user_from_local_jwt(request: Request, session: Session, token: str) -> User:
    """Validate a locally-issued JWT and return the corresponding user.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : Session
        Database session.
    token : str
        Bearer token to validate.

    Returns
    -------
    User
        Authenticated user.

    Raises
    ------
    SecurityTokenError
        If the token is invalid/expired/blacklisted.
    HTTPException
        If the user does not exist.
    """
    jwt_mgr = JWTManager(request.app.state.config)
    blacklist_repo = TokenBlacklistRepository(session)
    claims = jwt_mgr.decode_token(
        token,
        is_blacklisted=lambda jti: blacklist_repo.is_blacklisted(jti),
    )
    user_id = int(claims.get("sub", 0))
    repo = UserRepository(session)
    user = repo.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found"
        )
    return user


def _get_user_from_oidc_token(request: Request, session: Session, token: str) -> User:
    """Validate an OIDC-issued JWT and return the corresponding local user.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : Session
        Database session.
    token : str
        Bearer token to validate.

    Returns
    -------
    User
        Authenticated local user linked to the OIDC identity.

    Raises
    ------
    HTTPException
        If the token is invalid or user cannot be resolved.
    """
    service = OIDCAuthService(request.app.state.config)
    try:
        claims = service.validate_access_token(token=token)
    except OIDCAuthError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token"
        ) from err

    sub = claims.get("sub")
    email = claims.get("email")
    preferred_username = claims.get("preferred_username")

    repo = UserRepository(session)
    if isinstance(sub, str) and sub:
        user = repo.find_by_oidc_sub(sub)
        if user is not None:
            return user
    if isinstance(email, str) and email:
        user = repo.find_by_email(email)
        if user is not None:
            return user
    if isinstance(preferred_username, str) and preferred_username:
        user = repo.find_by_username(preferred_username)
        if user is not None:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found"
    )


def get_optional_user(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> User | None:
    """Return the current user when a valid token is present; allow anonymous otherwise.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : Session
        Database session.

    Returns
    -------
    User | None
        Authenticated user if token is valid, otherwise ``None`` when anonymous
        browsing is enabled.

    Raises
    ------
    HTTPException
        If a token is provided but invalid, or if anonymous browsing is disabled.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        with suppress(SecurityTokenError):
            return _get_user_from_local_jwt(request, session, token)

        if request.app.state.config.oidc_enabled:
            return _get_user_from_oidc_token(request, session, token)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token"
        )

    basic_config_service = BasicConfigService(session)
    basic_config = basic_config_service.get_basic_config()
    if not basic_config.allow_anonymous_browsing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_token"
        )

    return None


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


def get_active_library_id(
    session: Annotated[Session, Depends(get_db_session)],
) -> int:
    """Get the active library ID.

    Parameters
    ----------
    session : Session
        Database session.

    Returns
    -------
    int
        Active library ID.

    Raises
    ------
    HTTPException
        If no active library is configured.
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()

    if library is None or library.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    return library.id


def require_permission(
    resource: str,
    action: str,
    context: dict[str, object] | None = None,
) -> Callable[[User, Session], None]:
    """Create a FastAPI dependency that requires a specific permission.

    Returns a dependency function that checks if the current user has the
    required permission. Supports optional context for condition evaluation.

    Parameters
    ----------
    resource : str
        Resource name (e.g., 'books', 'shelves').
    action : str
        Action name (e.g., 'read', 'write', 'delete').
    context : dict[str, object] | None
        Optional context provider function or dict for condition evaluation.
        If a callable, it will be called with the request to get context.

    Returns
    -------
    Callable
        FastAPI dependency function that checks the permission.

    Examples
    --------
    >>> # Simple permission check
    >>> @router.get("/books")
    >>> def list_books(
    ...     _permission: None = Depends(
    ...         require_permission(
    ...             "books",
    ...             "read",
    ...         )
    ...     ),
    ... ):
    ...     return {
    ...         "books": []
    ...     }
    >>>
    >>> # Permission check with context
    >>> @router.get("/books/{book_id}")
    >>> def get_book(
    ...     book_id: int,
    ...     session: Session = Depends(
    ...         get_db_session
    ...     ),
    ...     current_user: User = Depends(
    ...         get_current_user
    ...     ),
    ...     _permission: None = Depends(
    ...         require_permission(
    ...             "books",
    ...             "read",
    ...             lambda req: get_book_context(
    ...                 req,
    ...                 session,
    ...             ),
    ...         )
    ...     ),
    ... ):
    ...     return {
    ...         "book": book
    ...     }
    """

    def permission_checker(
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[Session, Depends(get_db_session)],
    ) -> None:
        """Check permission and raise exception if denied.

        Parameters
        ----------
        current_user : User
            Current authenticated user.
        session : Session
            Database session.

        Raises
        ------
        HTTPException
            If user does not have the required permission (403).
        """
        permission_service = PermissionService(session)

        # Resolve context if it's a callable
        resolved_context = None
        if context is not None:
            if isinstance(context, dict):
                resolved_context = context
            elif callable(context):
                # Context provider function - would need request, but we can't access it here
                # For now, support dict only. Callable context can be handled in route handlers.
                resolved_context = None

        permission_service.check_permission(
            current_user, resource, action, resolved_context
        )

    return permission_checker


def get_opds_user(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> User | None:
    """Authenticate request via HTTP Basic Auth or JWT for OPDS feeds.

    Supports both HTTP Basic Auth (for e-reader compatibility) and
    JWT Bearer tokens (for web clients). Returns None if authentication fails.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : Session
        Database session.

    Returns
    -------
    User | None
        Authenticated user or None if authentication fails.
    """
    user_repo = UserRepository(session)
    hasher = PasswordHasher()
    jwt_mgr = JWTManager(request.app.state.config)

    auth_service = OpdsAuthService(
        session=session,
        user_repo=user_repo,
        hasher=hasher,
        jwt_manager=jwt_mgr,
    )

    return auth_service.authenticate_request(request)


def get_kobo_auth_token(request: Request) -> str:
    """Extract Kobo auth token from URL path.

    Kobo requests include the auth token in the path:
    /kobo/{auth_token}/v1/...

    Parameters
    ----------
    request : Request
        FastAPI request object.

    Returns
    -------
    str
        Auth token from path.

    Raises
    ------
    HTTPException
        If token is missing from path (404).
    """
    path_parts = request.url.path.split("/")
    if len(path_parts) < 3 or path_parts[1] != "kobo":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="kobo_path_invalid"
        )
    return path_parts[2]


def get_kobo_user(
    auth_token: Annotated[str, Depends(get_kobo_auth_token)],
    session: Annotated[Session, Depends(get_db_session)],
) -> User:
    """Authenticate Kobo user from auth token.

    Parameters
    ----------
    auth_token : str
        Auth token from path.
    session : Session
        Database session.

    Returns
    -------
    User
        Authenticated user.

    Raises
    ------
    HTTPException
        If token is invalid or user not found (401).
    """
    auth_token_repo = KoboAuthTokenRepository(session)
    user_repo = UserRepository(session)

    auth_service = KoboAuthService(
        session=session,
        auth_token_repo=auth_token_repo,
        user_repo=user_repo,
    )

    user = auth_service.validate_auth_token(auth_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="kobo_auth_invalid"
        )
    return user
