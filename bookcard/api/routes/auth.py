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

"""Authentication endpoints: register, login, and current user."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from bookcard.api.deps import get_current_user, get_db_session
from bookcard.api.schemas import (
    AuthConfigResponse,
    EmailServerConfigRead,
    EmailServerConfigUpdate,
    InviteValidationResponse,
    LoginRequest,
    LoginResponse,
    OIDCCallbackRequest,
    PasswordChangeRequest,
    ProfilePictureUpdateRequest,
    ProfileRead,
    ProfileUpdate,
    SettingRead,
    SettingsRead,
    SettingUpdate,
    TokenResponse,
    UserCreate,
    UserRead,
)
from bookcard.models.auth import Role, RolePermission, User, UserRole, UserSetting
from bookcard.models.config import EmailServerConfig, EmailServerType
from bookcard.repositories.admin_repositories import InviteRepository, SettingRepository
from bookcard.repositories.user_repository import (
    TokenBlacklistRepository,
    UserRepository,
)
from bookcard.services.authentication_service import AuthenticationService, AuthError
from bookcard.services.email_config_update import (
    EmailServerConfigUpdate as EmailServerConfigUpdateDTO,
)
from bookcard.services.file_storage_service import FileStorageService
from bookcard.services.oidc_auth_service import OIDCAuthError, OIDCAuthService
from bookcard.services.security import (
    DataEncryptor,
    JWTManager,
    PasswordHasher,
    SecurityTokenError,
)
from bookcard.services.system_configuration_service import SystemConfigurationService
from bookcard.services.user_linking_service import UserLinkingService
from bookcard.services.user_profile_service import ProfileError, UserProfileService
from bookcard.services.user_settings_service import UserSettingsService

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


class AuthFacade:
    """Facade used by the API layer to orchestrate auth-related operations.

    This is intentionally thin: it composes smaller services so the route
    handlers can depend on a single object without pulling business logic
    into the web layer.
    """

    def __init__(
        self,
        *,
        authentication: AuthenticationService,
        user_profile: UserProfileService,
        user_settings: UserSettingsService,
        system_config: SystemConfigurationService,
    ) -> None:
        self._authentication = authentication
        self._user_profile = user_profile
        self._user_settings = user_settings
        self._system_config = system_config

    def register_user(
        self, username: str, email: str, password: str
    ) -> tuple[User, str]:
        """Register a new user and return (user, token)."""
        return self._authentication.register_user(username, email, password)

    def login_user(self, identifier: str, password: str) -> tuple[User, str]:
        """Login a user and return (user, token)."""
        return self._authentication.login_user(identifier, password)

    def validate_invite_token(self, token: str) -> bool:
        """Validate an invite token."""
        return self._authentication.validate_invite_token(token)

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> None:
        """Change a user's password."""
        self._user_profile.change_password(user_id, current_password, new_password)

    def update_profile(
        self,
        user_id: int,
        *,
        username: str | None = None,
        email: str | None = None,
        full_name: str | None = None,
    ) -> User:
        """Update user profile fields."""
        return self._user_profile.update_profile(
            user_id, username=username, email=email, full_name=full_name
        )

    def upload_profile_picture(
        self, user_id: int, file_content: bytes, filename: str
    ) -> User:
        """Upload and set a user's profile picture."""
        return self._user_profile.upload_profile_picture(
            user_id, file_content, filename
        )

    def update_profile_picture(self, user_id: int, picture_path: str) -> User:
        """Set profile picture path without uploading."""
        return self._user_profile.update_profile_picture_path(user_id, picture_path)

    def delete_profile_picture(self, user_id: int) -> User:
        """Delete a user's profile picture."""
        return self._user_profile.delete_profile_picture(user_id)

    def upsert_setting(
        self, user_id: int, key: str, value: str, description: str | None = None
    ) -> UserSetting:
        """Create or update a user setting."""
        return self._user_settings.upsert_setting(user_id, key, value, description)

    def get_all_settings(self, user_id: int) -> list[UserSetting]:
        """Return all settings for a user."""
        return self._user_settings.get_all_settings(user_id)

    def get_email_server_config(
        self, decrypt: bool = False
    ) -> EmailServerConfig | None:
        """Return global email server configuration."""
        return self._system_config.get_email_server_config(decrypt=decrypt)

    def upsert_email_server_config(
        self, update: EmailServerConfigUpdate
    ) -> EmailServerConfig:
        """Create or update global email server configuration."""
        dto = EmailServerConfigUpdateDTO(**update.model_dump(exclude_unset=True))
        return self._system_config.upsert_email_server_config(dto)


def _auth_service(request: Request, session: Session) -> AuthFacade:
    """Create the request-scoped auth facade.

    Parameters
    ----------
    request : Request
        FastAPI request.
    session : Session
        Database session.

    Returns
    -------
    AuthFacade
        Composed facade for auth routes.
    """
    cfg = request.app.state.config
    encryptor = DataEncryptor(cfg.encryption_key)
    user_repo = UserRepository(session)
    return AuthFacade(
        authentication=AuthenticationService(
            session=session,
            user_repo=user_repo,
            invite_repo=InviteRepository(session),
            hasher=PasswordHasher(),
            jwt=JWTManager(cfg),
        ),
        user_profile=UserProfileService(
            session=session,
            user_repo=user_repo,
            hasher=PasswordHasher(),
            file_storage=FileStorageService(data_directory=cfg.data_directory),
        ),
        user_settings=UserSettingsService(
            session=session,
            user_repo=user_repo,
            setting_repo=SettingRepository(session),
        ),
        system_config=SystemConfigurationService(
            session=session,
            encryptor=encryptor,
        ),
    )


def _load_user_with_permissions(session: Session, *, user_id: int) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.ereader_devices),  # type: ignore[invalid-argument-type]
            selectinload(User.roles)  # type: ignore[invalid-argument-type]
            .selectinload(UserRole.role)  # type: ignore[invalid-argument-type]
            .selectinload(Role.permissions)  # type: ignore[invalid-argument-type]
            .selectinload(RolePermission.permission),  # type: ignore[invalid-argument-type]
        )
    )
    user_with_rels = session.exec(stmt).first()
    if user_with_rels is None:
        raise HTTPException(status_code=500, detail="user_not_found")
    return user_with_rels


def _oidc_service(request: Request) -> OIDCAuthService:
    return OIDCAuthService(request.app.state.config)


def _user_linking_service(session: Session) -> UserLinkingService:
    return UserLinkingService(UserRepository(session), PasswordHasher())


def _is_oidc_enabled(request: Request) -> bool:
    """Return True if OIDC authentication is enabled for the app.

    Uses a defensive attribute lookup to support lightweight test stubs that
    may not provide the full `AppConfig` surface area.
    """
    return bool(getattr(request.app.state.config, "oidc_enabled", False))


@router.get("/config", response_model=AuthConfigResponse)
def auth_config(request: Request) -> AuthConfigResponse:
    """Return authentication configuration for clients."""
    cfg = request.app.state.config
    return AuthConfigResponse(
        oidc_enabled=_is_oidc_enabled(request),
        oidc_issuer=getattr(cfg, "oidc_issuer", ""),
        local_login_enabled=not _is_oidc_enabled(request),
    )


@router.get("/oidc/login")
def oidc_login(
    request: Request,
    redirect_uri: str | None = None,
    next: str | None = None,  # noqa: A002
) -> RedirectResponse:
    """Redirect the user to an OIDC provider for login."""
    if not _is_oidc_enabled(request):
        raise HTTPException(status_code=404, detail="oidc_disabled")

    resolved_redirect_uri = redirect_uri or str(request.url_for("oidc_callback_get"))
    service = _oidc_service(request)
    auth_url = service.build_authorization_url(
        redirect_uri=resolved_redirect_uri,
        next_path=next,
    )
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/oidc/callback", name="oidc_callback_get", response_model=LoginResponse)
def oidc_callback_get(
    request: Request,
    session: SessionDep,
    code: str,
    state: str,
) -> LoginResponse:
    """Handle OIDC callback (GET) and return a local session token."""
    if not _is_oidc_enabled(request):
        raise HTTPException(status_code=404, detail="oidc_disabled")

    service = _oidc_service(request)
    try:
        state_payload = service.decode_state(state=state)
    except OIDCAuthError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    redirect_uri = state_payload.get("redirect_uri")
    if not isinstance(redirect_uri, str) or not redirect_uri:
        raise HTTPException(status_code=400, detail="oidc_state_missing_redirect_uri")

    return _handle_oidc_callback(
        request=request,
        session=session,
        code=code,
        state=state,
        redirect_uri=redirect_uri,
    )


@router.post("/oidc/callback", response_model=LoginResponse)
def oidc_callback_post(
    request: Request,
    session: SessionDep,
    payload: OIDCCallbackRequest,
) -> LoginResponse:
    """Handle OIDC callback (POST) and return a local session token."""
    if not _is_oidc_enabled(request):
        raise HTTPException(status_code=404, detail="oidc_disabled")

    return _handle_oidc_callback(
        request=request,
        session=session,
        code=payload.code,
        state=payload.state,
        redirect_uri=payload.redirect_uri,
    )


def _handle_oidc_callback(
    *,
    request: Request,
    session: Session,
    code: str,
    state: str,
    redirect_uri: str,
) -> LoginResponse:
    service = _oidc_service(request)
    try:
        state_payload = service.decode_state(state=state)
    except OIDCAuthError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    expected_redirect_uri = state_payload.get("redirect_uri")
    if expected_redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="oidc_redirect_uri_mismatch")

    try:
        token_set = service.exchange_code_for_token(
            code=code, redirect_uri=redirect_uri
        )
        userinfo = service.fetch_userinfo(access_token=token_set.access_token)
    except OIDCAuthError as err:
        raise HTTPException(status_code=401, detail=str(err)) from err

    linker = _user_linking_service(session)
    try:
        user = linker.find_or_create_oidc_user(userinfo=userinfo, session=session)
        session.commit()
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    jwt_mgr = JWTManager(request.app.state.config)
    access_token = jwt_mgr.create_access_token(
        str(user.id), {"username": user.username, "is_admin": user.is_admin}
    )

    user_with_rels = _load_user_with_permissions(session, user_id=int(user.id))  # type: ignore[arg-type]
    return LoginResponse(
        access_token=access_token, user=UserRead.from_user(user_with_rels)
    )


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
def register(
    request: Request, session: SessionDep, payload: UserCreate
) -> TokenResponse:
    """Register a new user and return an access token."""
    if _is_oidc_enabled(request):
        raise HTTPException(status_code=400, detail="local_auth_disabled")
    service = _auth_service(request, session)
    try:
        _user, token = service.register_user(
            payload.username, payload.email, payload.password
        )
        logger.info(
            "User registered: username=%s, email=%s", payload.username, payload.email
        )
    except ValueError as exc:
        msg = str(exc)
        if msg in {AuthError.USERNAME_EXISTS, AuthError.EMAIL_EXISTS}:
            logger.debug(
                "Registration failed: %s for username=%s", msg, payload.username
            )
            raise HTTPException(status_code=409, detail=msg) from exc
        raise
    return TokenResponse(access_token=token)


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request, session: SessionDep, payload: LoginRequest
) -> LoginResponse:
    """Login by username or email and return an access token with user data."""
    if _is_oidc_enabled(request):
        raise HTTPException(status_code=400, detail="local_auth_disabled")
    service = _auth_service(request, session)
    try:
        user, token = service.login_user(payload.identifier, payload.password)
        logger.info(
            "User logged in: user_id=%s, identifier=%s", user.id, payload.identifier
        )
    except ValueError as exc:
        if str(exc) == AuthError.INVALID_CREDENTIALS:
            logger.debug(
                "Login failed: invalid credentials for identifier=%s",
                payload.identifier,
            )
            raise HTTPException(
                status_code=401, detail=AuthError.INVALID_CREDENTIALS
            ) from exc
        raise

    user_with_rels = _load_user_with_permissions(session, user_id=int(user.id))  # type: ignore[arg-type]
    return LoginResponse(
        access_token=token,
        user=UserRead.from_user(user_with_rels),
    )


@router.get("/me", response_model=UserRead)
def me(
    request: Request,
    session: SessionDep,
) -> UserRead:
    """Return the current authenticated user."""
    current_user = get_current_user(request, session)
    user_with_rels = _load_user_with_permissions(
        session,
        user_id=int(current_user.id),  # type: ignore[arg-type]
    )
    return UserRead.from_user(user_with_rels)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    request: Request,
    session: SessionDep,
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
    current_user = get_current_user(request, session)
    try:
        service.change_password(
            current_user.id,  # type: ignore[arg-type]
            payload.current_password,
            payload.new_password,
        )
        logger.info("Password changed: user_id=%s", current_user.id)
    except ValueError as exc:
        msg = str(exc)
        if msg == ProfileError.INVALID_PASSWORD:
            logger.debug(
                "Password change failed: invalid password for user_id=%s",
                current_user.id,
            )
            raise HTTPException(status_code=400, detail=msg) from exc
        if msg == "user_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    session: SessionDep,
) -> None:
    """Logout the current user and blacklist their token.

    Extracts the JWT token from the Authorization header, decodes it to get
    the JWT ID (jti), and adds it to the token blacklist to prevent further use.

    This endpoint is idempotent - it will return 204 even if the token is
    missing or invalid, as the user is effectively already logged out.

    Parameters
    ----------
    request : Request
        FastAPI request object containing Authorization header.
    session : SessionDep
        Database session dependency.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        # No token provided - user is already logged out
        return

    token = auth_header.removeprefix("Bearer ")
    jwt_mgr = JWTManager(request.app.state.config)

    try:
        # Decode token to get jti and expiration
        claims = jwt_mgr.decode_token(token)
    except SecurityTokenError:
        # Token is invalid or expired - user is already logged out
        return

    # Extract jti and expiration from token
    jti = claims.get("jti")
    exp_timestamp = claims.get("exp")

    if not jti or not exp_timestamp:
        # Token doesn't have jti or exp, can't blacklist it
        # This shouldn't happen with our token creation, but handle gracefully
        return

    # Convert expiration timestamp to datetime
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=UTC)

    # Add token to blacklist
    blacklist_repo = TokenBlacklistRepository(session)
    blacklist_repo.add_to_blacklist(jti, expires_at)
    session.flush()
    logger.info("User logged out: jti=%s", jti)


@router.get("/profile", response_model=ProfileRead)
def get_profile(
    request: Request,
    session: SessionDep,
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
    current_user = get_current_user(request, session)
    return ProfileRead.model_validate(current_user)


@router.patch("/profile", response_model=ProfileRead)
def update_profile(
    request: Request,
    session: SessionDep,
    payload: ProfileUpdate,
) -> ProfileRead:
    """Update the current user's profile information.

    Allows updating username, email, and full_name. Only provided fields
    will be updated. Password changes should use PUT /auth/password.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    payload : ProfileUpdate
        Request containing fields to update.

    Returns
    -------
    ProfileRead
        Updated user profile.

    Raises
    ------
    HTTPException
        If user is not found (404), username already exists (409), or
        email already exists (409).
    """
    service = _auth_service(request, session)
    current_user = get_current_user(request, session)
    try:
        user = service.update_profile(
            current_user.id,  # type: ignore[arg-type]
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
        )
        session.commit()
        logger.info("Profile updated: user_id=%s", current_user.id)
    except ValueError as exc:
        msg = str(exc)
        if msg == "user_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg in {ProfileError.USERNAME_EXISTS, ProfileError.EMAIL_EXISTS}:
            raise HTTPException(status_code=409, detail=msg) from exc
        raise
    return ProfileRead.model_validate(user)


@router.post("/profile-picture", response_model=ProfileRead)
def upload_profile_picture(
    request: Request,
    session: SessionDep,
    file: Annotated[UploadFile, File()],
) -> ProfileRead:
    """Upload the current user's profile picture.

    Accepts an image file and saves it to {data_directory}/{user_id}/assets/.
    Replaces any existing profile picture.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    file : UploadFile
        Image file to upload (JPEG, PNG, GIF, WebP, or SVG).

    Returns
    -------
    ProfileRead
        Updated user profile.

    Raises
    ------
    HTTPException
        If user is not found (404), invalid file type (400), or file save fails (500).
    """
    service = _auth_service(request, session)
    current_user = get_current_user(request, session)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="filename_required",
        )

    try:
        file_content = file.file.read()
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_read_file: {exc!s}",
        ) from exc

    try:
        user = service.upload_profile_picture(
            current_user.id,  # type: ignore[arg-type]
            file_content,
            file.filename,
        )
        session.commit()
        logger.info(
            "Profile picture uploaded: user_id=%s, filename=%s",
            current_user.id,
            file.filename,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "user_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg == ProfileError.INVALID_FILE_TYPE:
            raise HTTPException(status_code=400, detail=msg) from exc
        if msg.startswith("failed_to_save_file"):
            raise HTTPException(status_code=500, detail=msg) from exc
        raise
    return ProfileRead.model_validate(user)


@router.patch("/profile-picture", response_model=ProfileRead)
def update_profile_picture(
    request: Request,
    session: SessionDep,
    payload: ProfilePictureUpdateRequest,
) -> ProfileRead:
    """Update the current user's profile picture path.

    Updates the profile picture path in the database without uploading a new file.
    Use POST /auth/profile-picture to upload a new file.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
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
    current_user = get_current_user(request, session)
    try:
        user = service.update_profile_picture(
            current_user.id,  # type: ignore[arg-type]
            payload.picture_path,
        )
        session.commit()
    except ValueError as exc:
        msg = str(exc)
        if msg == "user_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise
    return ProfileRead.model_validate(user)


@router.get("/profile-picture", response_model=None)
def get_profile_picture(
    request: Request,
    session: SessionDep,
) -> FileResponse | Response:
    """Get the current user's profile picture.

    Serves the profile picture file if it exists.

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
    FileResponse | Response
        Profile picture file or 404 if not found.
    """
    cfg = request.app.state.config
    current_user = get_current_user(request, session)

    if not current_user.profile_picture:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Handle both relative and absolute paths
    picture_path = Path(current_user.profile_picture)
    if picture_path.is_absolute():
        full_path = picture_path
    else:
        # Relative path - construct full path from data_directory
        full_path = Path(cfg.data_directory) / current_user.profile_picture

    if not full_path.exists():
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Determine media type from extension
    ext = full_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(ext, "image/jpeg")

    return FileResponse(path=str(full_path), media_type=media_type)


@router.delete("/profile-picture", response_model=ProfileRead)
def delete_profile_picture(
    request: Request,
    session: SessionDep,
) -> ProfileRead:
    """Delete the current user's profile picture.

    Removes both the file from disk and clears the database field.

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
    current_user = get_current_user(request, session)
    try:
        user = service.delete_profile_picture(current_user.id)  # type: ignore[arg-type]
        session.commit()
        logger.info("Profile picture deleted: user_id=%s", current_user.id)
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
        logger.debug("Invite token validated: token=%s", token[:8] + "...")
        return InviteValidationResponse(valid=True, token=token)
    except ValueError as exc:
        msg = str(exc)
        if msg == AuthError.INVALID_INVITE:
            logger.debug("Invite token validation failed: invalid token")
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg in {AuthError.INVITE_EXPIRED, AuthError.INVITE_ALREADY_USED}:
            logger.debug("Invite token validation failed: %s", msg)
            raise HTTPException(status_code=400, detail=msg) from exc
        raise


@router.get("/settings", response_model=SettingsRead)
def get_settings(
    request: Request,
    session: SessionDep,
) -> SettingsRead:
    """Get all settings for the current user.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    SettingsRead
        Dictionary of user settings keyed by setting key.
    """
    service = _auth_service(request, session)
    current_user = get_current_user(request, session)
    settings = service.get_all_settings(current_user.id)  # type: ignore[arg-type]

    settings_dict = {
        setting.key: SettingRead.model_validate(setting) for setting in settings
    }
    return SettingsRead(settings=settings_dict)


@router.put("/settings/{key}", response_model=SettingRead)
def upsert_setting(
    request: Request,
    session: SessionDep,
    key: str,
    payload: SettingUpdate,
) -> SettingRead:
    """Create or update a user setting.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    key : str
        Setting key.
    payload : SettingUpdate
        Request containing setting value and optional description.

    Returns
    -------
    SettingRead
        Created or updated user setting.

    Raises
    ------
    HTTPException
        If user is not found (404) or key/value exceeds length limits (400).
    """
    service = _auth_service(request, session)
    current_user = get_current_user(request, session)
    try:
        setting = service.upsert_setting(
            current_user.id,  # type: ignore[arg-type]
            key,
            payload.value,
            payload.description,
        )
        session.commit()
        logger.info("Setting updated: user_id=%s, key=%s", current_user.id, key)
    except ValueError as exc:
        msg = str(exc)
        if msg == "user_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise
    return SettingRead.model_validate(setting)


@router.get("/email-server-config", response_model=EmailServerConfigRead)
def get_email_server_config(
    request: Request,
    session: SessionDep,
) -> EmailServerConfigRead:
    """Get the global email server configuration (admin only).

    Returns default values if configuration has not been created yet.
    """
    service = _auth_service(request, session)
    current_user = get_current_user(request, session)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="forbidden")

    config = service.get_email_server_config(decrypt=True)
    if config is None:
        # Return defaults (no persisted record yet)
        return EmailServerConfigRead(
            id=None,
            server_type=EmailServerType.SMTP,
            smtp_host=None,
            smtp_port=587,
            smtp_username=None,
            smtp_use_tls=True,
            smtp_use_ssl=False,
            smtp_from_email=None,
            smtp_from_name=None,
            max_email_size_mb=25,
            gmail_token=None,
            enabled=False,
            created_at=None,
            updated_at=None,
        )
    return EmailServerConfigRead.model_validate(config)


@router.put("/email-server-config", response_model=EmailServerConfigRead)
def upsert_email_server_config(
    request: Request,
    session: SessionDep,
    payload: EmailServerConfigUpdate,
) -> EmailServerConfigRead:
    """Create or update the global email server configuration (admin only).

    Parameters
    ----------
    payload : EmailServerConfigUpdate
        Configuration payload. SMTP password can be set but will not
        be returned in the response.
    """
    service = _auth_service(request, session)
    current_user = get_current_user(request, session)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="forbidden")

    try:
        cfg = service.upsert_email_server_config(payload)
        session.commit()
        logger.info("Email server config updated: user_id=%s", current_user.id)
        # Decrypt for API response (password won't be included in response model)
        cfg = service.get_email_server_config(decrypt=True)
        if cfg is None:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve saved config"
            )
    except ValueError as exc:
        msg = str(exc)
        if msg == "invalid_smtp_encryption":
            raise HTTPException(status_code=400, detail=msg) from exc
        if msg == "smtp_from_email_required":
            raise HTTPException(
                status_code=400,
                detail="From email is required when SMTP authentication is disabled",
            ) from exc
        raise

    return EmailServerConfigRead.model_validate(cfg)
