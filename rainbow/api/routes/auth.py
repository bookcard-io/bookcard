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

"""Authentication endpoints: register, login, and current user."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from rainbow.api.deps import get_current_user, get_db_session
from rainbow.api.schemas import (
    InviteValidationResponse,
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    ProfilePictureUpdateRequest,
    ProfileRead,
    TokenResponse,
    UserCreate,
    UserRead,
)
from rainbow.models.auth import User
from rainbow.repositories.user_repository import UserRepository
from rainbow.services.auth_service import AuthError, AuthService
from rainbow.services.security import JWTManager, PasswordHasher

router = APIRouter(prefix="/auth", tags=["auth"])


SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _auth_service(request: Request, session: Session) -> AuthService:
    cfg = request.app.state.config
    jwt = JWTManager(cfg)
    hasher = PasswordHasher()
    repo = UserRepository(session)
    return AuthService(session, repo, hasher, jwt)


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
def register(
    request: Request, session: SessionDep, payload: UserCreate
) -> TokenResponse:
    """Register a new user and return an access token."""
    service = _auth_service(request, session)
    try:
        _user, token = service.register_user(
            payload.username, payload.email, payload.password
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {AuthError.USERNAME_EXISTS, AuthError.EMAIL_EXISTS}:
            raise HTTPException(status_code=409, detail=msg) from exc
        raise
    return TokenResponse(access_token=token)


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request, session: SessionDep, payload: LoginRequest
) -> LoginResponse:
    """Login by username or email and return an access token with user data."""
    service = _auth_service(request, session)
    try:
        user, token = service.login_user(payload.identifier, payload.password)
    except ValueError as exc:
        if str(exc) == AuthError.INVALID_CREDENTIALS:
            raise HTTPException(
                status_code=401, detail=AuthError.INVALID_CREDENTIALS
            ) from exc
        raise
    return LoginResponse(
        access_token=token,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def me(
    current_user: CurrentUserDep,
) -> UserRead:
    """Return the current authenticated user."""
    # FastAPI will serialize using response_model=UserRead
    # with from_attributes=True from UserRead.model_config
    return UserRead.model_validate(current_user)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    payload: PasswordChangeRequest,
) -> None:
    """Change the current user's password.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Authenticated user dependency.
    payload : PasswordChangeRequest
        Request containing current and new passwords.
    """
    service = _auth_service(request, session)
    try:
        service.change_password(
            current_user.id,  # type: ignore[arg-type]
            payload.current_password,
            payload.new_password,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == AuthError.INVALID_PASSWORD:
            raise HTTPException(status_code=400, detail=msg) from exc
        if msg == "user_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    """Logout the current user.

    Note: This is a stateless JWT-based system. The client should discard
    the token after calling this endpoint.
    """
    return


@router.get("/profile", response_model=ProfileRead)
def get_profile(
    current_user: CurrentUserDep,
) -> ProfileRead:
    """Return the current user's profile with profile picture.

    Parameters
    ----------
    current_user : CurrentUserDep
        Authenticated user dependency.

    Returns
    -------
    ProfileRead
        User profile including profile picture path.
    """
    return ProfileRead.model_validate(current_user)


@router.put("/profile-picture", response_model=ProfileRead)
def update_profile_picture(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    payload: ProfilePictureUpdateRequest,
) -> ProfileRead:
    """Update the current user's profile picture.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Authenticated user dependency.
    payload : ProfilePictureUpdateRequest
        Request containing the profile picture path.

    Returns
    -------
    ProfileRead
        Updated user profile.

    Raises
    ------
    HTTPException
        If user is not found (404).
    """
    service = _auth_service(request, session)
    try:
        user = service.update_profile_picture(
            current_user.id,  # type: ignore[arg-type]
            payload.picture_path,
        )
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise
    return ProfileRead.model_validate(user)


@router.delete("/profile-picture", response_model=ProfileRead)
def delete_profile_picture(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ProfileRead:
    """Delete the current user's profile picture.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Authenticated user dependency.

    Returns
    -------
    ProfileRead
        Updated user profile with profile picture set to None.

    Raises
    ------
    HTTPException
        If user is not found (404).
    """
    service = _auth_service(request, session)
    try:
        user = service.delete_profile_picture(current_user.id)  # type: ignore[arg-type]
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise
    return ProfileRead.model_validate(user)


@router.get("/invite/{token}", response_model=InviteValidationResponse)
def validate_invite_token(
    request: Request,
    session: SessionDep,
    token: str,
) -> InviteValidationResponse:
    """Validate an invite token.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    token : str
        Invite token to validate.

    Returns
    -------
    InviteValidationResponse
        Response indicating if the token is valid.

    Raises
    ------
    HTTPException
        If token is invalid (404), expired (400), or already used (400).
    """
    service = _auth_service(request, session)
    try:
        service.validate_invite_token(token)
        return InviteValidationResponse(valid=True, token=token)
    except ValueError as exc:
        msg = str(exc)
        if msg == AuthError.INVALID_INVITE:
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg in {AuthError.INVITE_EXPIRED, AuthError.INVITE_ALREADY_USED}:
            raise HTTPException(status_code=400, detail=msg) from exc
        raise
