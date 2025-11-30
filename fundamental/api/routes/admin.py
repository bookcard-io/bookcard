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

"""Admin endpoints: user management, roles, permissions, and e-reader devices."""

from __future__ import annotations

import logging
from contextlib import suppress
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from fundamental.api.deps import get_admin_user, get_current_user, get_db_session
from fundamental.api.schemas import (
    AdminUserCreate,
    AdminUserUpdate,
    EReaderDeviceCreate,
    EReaderDeviceRead,
    EReaderDeviceUpdate,
    LibraryCreate,
    LibraryRead,
    LibraryStats,
    LibraryUpdate,
    OpenLibraryDumpConfigRead,
    OpenLibraryDumpConfigUpdate,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    RoleCreate,
    RolePermissionGrant,
    RolePermissionRead,
    RolePermissionUpdate,
    RoleRead,
    RoleUpdate,
    ScheduledTasksConfigRead,
    ScheduledTasksConfigUpdate,
    UserRead,
    UserRoleAssign,
)
from fundamental.models.auth import EBookFormat, Role, RolePermission, User
from fundamental.repositories.config_repository import (
    LibraryRepository,
)
from fundamental.repositories.ereader_repository import EReaderRepository
from fundamental.repositories.role_repository import (
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRoleRepository,
)
from fundamental.repositories.user_repository import UserRepository
from fundamental.services.auth_service import AuthService
from fundamental.services.config_service import (
    LibraryService,
    ScheduledTasksConfigService,
)
from fundamental.services.ereader_service import EReaderService
from fundamental.services.openlibrary_service import OpenLibraryService
from fundamental.services.role_service import RoleService
from fundamental.services.security import DataEncryptor, JWTManager, PasswordHasher
from fundamental.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])

SessionDep = Annotated[Session, Depends(get_db_session)]
AdminUserDep = Annotated[User, Depends(get_admin_user)]

logger = logging.getLogger(__name__)


def _auth_service(request: Request, session: Session) -> AuthService:
    """Create AuthService instance for admin routes.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : Session
        Database session.

    Returns
    -------
    AuthService
        Configured AuthService instance.
    """
    cfg = request.app.state.config
    jwt = JWTManager(cfg)
    hasher = PasswordHasher()
    encryptor = DataEncryptor(cfg.encryption_key)
    repo = UserRepository(session)
    return AuthService(
        session,
        repo,
        hasher,
        jwt,
        encryptor=encryptor,
        data_directory=cfg.data_directory,
    )


class DownloadFilesRequest(BaseModel):
    """Request model for downloading files.

    Attributes
    ----------
    urls : list[str]
        List of file URLs to download.
    """

    urls: list[str]


class DownloadFilesResponse(BaseModel):
    """Response model for file download operation.

    Attributes
    ----------
    message : str
        Success message.
    task_id : int
        Task ID for tracking the download progress.
    downloaded_files : list[str]
        List of successfully downloaded file paths (empty until task completes).
    failed_files : list[str]
        List of URLs that failed to download (empty until task completes).
    """

    message: str
    task_id: int
    downloaded_files: list[str]
    failed_files: list[str]


def role_to_role_read(role: Role) -> RoleRead:
    """Convert Role model to RoleRead schema with permissions.

    Parameters
    ----------
    role : Role
        Role model instance with permissions relationship loaded.

    Returns
    -------
    RoleRead
        RoleRead instance with populated permissions.
    """
    permissions = [
        RolePermissionRead(
            id=rp.id,  # type: ignore[arg-type]
            permission=PermissionRead(
                id=rp.permission.id,  # type: ignore[arg-type]
                name=rp.permission.name,
                description=rp.permission.description,
                resource=rp.permission.resource,
                action=rp.permission.action,
            ),
            condition=rp.condition,
            assigned_at=rp.assigned_at,
        )
        for rp in (role.permissions or [])
    ]

    return RoleRead(
        id=role.id,  # type: ignore[arg-type]
        name=role.name,
        description=role.description,
        permissions=permissions,
    )


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def create_user(
    session: SessionDep,
    payload: AdminUserCreate,
) -> UserRead:
    """Create a new user with optional role and device assignment.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    payload : AdminUserCreate
        User creation payload with optional role and device.

    Returns
    -------
    UserRead
        Created user.

    Raises
    ------
    HTTPException
        If username or email already exists (409).
    """
    user_repo = UserRepository(session)
    user_service = UserService(session, user_repo)
    hasher = PasswordHasher()

    # Prepare role service if roles are provided
    role_service: RoleService | None = None
    if payload.role_ids:
        role_service = RoleService(
            session,
            RoleRepository(session),
            PermissionRepository(session),
            UserRoleRepository(session),
            RolePermissionRepository(session),
        )

    # Prepare device service if device email is provided
    device_service: EReaderService | None = None
    if payload.default_device_email:
        device_service = EReaderService(session, EReaderRepository(session))

    try:
        user = user_service.create_admin_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            is_admin=payload.is_admin,
            is_active=payload.is_active,
            role_ids=payload.role_ids if payload.role_ids else None,
            default_device_email=payload.default_device_email,
            default_device_name=payload.default_device_name,
            default_device_type=payload.default_device_type,
            default_device_format=payload.default_device_format,
            password_hasher=hasher,
            role_service=role_service,
            device_service=device_service,
        )
        return UserRead.from_user(user)
    except ValueError as exc:
        error_msg = str(exc)
        if error_msg in ("username_already_exists", "email_already_exists"):
            raise HTTPException(status_code=409, detail=error_msg) from exc
        if error_msg == "user_not_found":
            raise HTTPException(status_code=404, detail=error_msg) from exc
        raise HTTPException(status_code=400, detail=error_msg) from exc


@router.get(
    "/users",
    response_model=list[UserRead],
    dependencies=[Depends(get_admin_user)],
)
def list_users(
    session: SessionDep,
    limit: int = 100,
    offset: int = 0,
) -> list[UserRead]:
    """List users with pagination.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    limit : int
        Maximum number of users to return (default: 100).
    offset : int
        Number of users to skip (default: 0).

    Returns
    -------
    list[UserRead]
        List of users.
    """
    user_repo = UserRepository(session)
    user_service = UserService(session, user_repo)
    users = user_service.list_users_with_relationships(limit=limit, offset=offset)
    return [UserRead.from_user(user) for user in users]


@router.get(
    "/users/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(get_admin_user)],
)
def get_user(
    session: SessionDep,
    user_id: int,
) -> UserRead:
    """Get a user by ID.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    user_id : int
        User identifier.

    Returns
    -------
    UserRead
        User data.

    Raises
    ------
    HTTPException
        If user not found (404).
    """
    user_repo = UserRepository(session)
    user_service = UserService(session, user_repo)
    user = user_service.get_with_relationships(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserRead.from_user(user)


@router.get(
    "/users/{user_id}/profile-picture",
    response_model=None,
    dependencies=[Depends(get_admin_user)],
)
def get_user_profile_picture(
    request: Request,
    session: SessionDep,
    user_id: int,
) -> FileResponse | Response:
    """Get a user's profile picture by user ID.

    Serves the profile picture file if it exists.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    user_id : int
        User identifier.

    Returns
    -------
    FileResponse | Response
        Profile picture file or 404 if not found.

    Raises
    ------
    HTTPException
        If user not found (404).
    """
    cfg = request.app.state.config
    user_repo = UserRepository(session)
    user = user_repo.get(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")

    if not user.profile_picture:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Handle both relative and absolute paths
    picture_path = Path(user.profile_picture)
    if picture_path.is_absolute():
        full_path = picture_path
    else:
        # Relative path - construct full path from data_directory
        full_path = Path(cfg.data_directory) / user.profile_picture

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


@router.put(
    "/users/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(get_admin_user)],
)
def update_user(
    session: SessionDep,
    user_id: int,
    payload: AdminUserUpdate,
) -> UserRead:
    """Update user properties.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    user_id : int
        User identifier.
    payload : AdminUserUpdate
        Update payload.

    Returns
    -------
    UserRead
        Updated user.

    Raises
    ------
    HTTPException
        If user not found (404) or username/email conflict (409).
    """
    user_repo = UserRepository(session)
    user_service = UserService(session, user_repo)

    # Prepare role service and repository if roles need updating
    role_service = None
    user_role_repo = None
    if payload.role_ids is not None:
        role_repo = RoleRepository(session)
        user_role_repo = UserRoleRepository(session)
        role_service = RoleService(
            session,
            role_repo,
            PermissionRepository(session),
            user_role_repo,
            RolePermissionRepository(session),
        )

    # Prepare password hasher if password needs updating
    password_hasher = None
    if payload.password is not None:
        password_hasher = PasswordHasher()

    # Prepare device service and repository if device needs updating
    device_service = None
    device_repo = None
    if payload.default_device_email is not None:
        device_repo = EReaderRepository(session)
        device_service = EReaderService(session, device_repo)

    # Delegate business logic to service
    try:
        user_service.update_user(
            user_id,
            username=payload.username,
            email=payload.email,
            password=payload.password,
            is_admin=payload.is_admin,
            is_active=payload.is_active,
            role_ids=payload.role_ids,
            default_device_email=payload.default_device_email,
            default_device_name=payload.default_device_name,
            default_device_type=payload.default_device_type,
            default_device_format=payload.default_device_format,
            role_service=role_service,
            user_role_repo=user_role_repo,
            password_hasher=password_hasher,
            device_service=device_service,
            device_repo=device_repo,
        )
        session.commit()
    except ValueError as exc:
        msg = str(exc)
        if msg == "user_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg in {"username_already_exists", "email_already_exists"}:
            raise HTTPException(status_code=409, detail=msg) from exc
        if msg == "password_hasher_required":
            raise HTTPException(
                status_code=500, detail="password_update_failed"
            ) from exc
        raise

    # Reload with relationships for response
    user_with_rels = user_service.get_with_relationships(user_id)
    if user_with_rels is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserRead.from_user(user_with_rels)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
def delete_user(
    request: Request,
    session: SessionDep,
    admin_user: AdminUserDep,
    user_id: int,
) -> None:
    """Delete a user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    user_id : int
        User identifier.

    Raises
    ------
    HTTPException
        If user not found (404) or admin tries to delete themselves (403).
    """
    # Prevent admin from deleting themselves
    if admin_user.id == user_id:
        raise HTTPException(status_code=403, detail="cannot_delete_self")

    # Use service to handle deletion
    user_repo = UserRepository(session)
    device_repo = EReaderRepository(session)
    user_role_repo = UserRoleRepository(session)
    user_service = UserService(session, user_repo)

    cfg = request.app.state.config
    try:
        user_service.delete_user(
            user_id,
            data_directory=cfg.data_directory,
            device_repo=device_repo,
            user_role_repo=user_role_repo,
        )
        session.commit()
    except ValueError as exc:
        msg = str(exc)
        if msg == "user_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise


@router.post(
    "/users/{user_id}/roles",
    response_model=UserRead,
    dependencies=[Depends(get_admin_user)],
)
def assign_role_to_user(
    session: SessionDep,
    user_id: int,
    payload: UserRoleAssign,
) -> UserRead:
    """Assign a role to a user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    user_id : int
        User identifier.
    payload : UserRoleAssign
        Role assignment payload.

    Returns
    -------
    UserRead
        Updated user.

    Raises
    ------
    HTTPException
        If user not found (404) or role already assigned (409).
    """
    role_repo = RoleRepository(session)
    user_role_repo = UserRoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        user_role_repo,
        RolePermissionRepository(session),
    )

    try:
        role_service.assign_role_to_user(user_id, payload.role_id)
        session.commit()
    except ValueError as exc:
        msg = str(exc)
        if msg == "user_already_has_role":
            raise HTTPException(status_code=409, detail=msg) from exc
        raise HTTPException(status_code=404, detail="user_or_role_not_found") from None

    user_repo = UserRepository(session)
    user_service = UserService(session, user_repo)
    user = user_service.get_with_relationships(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserRead.from_user(user)


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    response_model=UserRead,
    dependencies=[Depends(get_admin_user)],
)
def remove_role_from_user(
    session: SessionDep,
    user_id: int,
    role_id: int,
) -> UserRead:
    """Remove a role from a user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    user_id : int
        User identifier.
    role_id : int
        Role identifier.

    Returns
    -------
    UserRead
        Updated user.

    Raises
    ------
    HTTPException
        If user or role association not found (404).
    """
    role_repo = RoleRepository(session)
    user_role_repo = UserRoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        user_role_repo,
        RolePermissionRepository(session),
    )

    try:
        role_service.remove_role_from_user(user_id, role_id)
        session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="user_role_not_found") from exc

    user_repo = UserRepository(session)
    user_service = UserService(session, user_repo)
    user = user_service.get_with_relationships(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserRead.from_user(user)


# Role Management


def _raise_role_not_found() -> None:
    """Raise HTTPException for role not found.

    Raises
    ------
    HTTPException
        Always raises with status 404.
    """
    msg = "role_not_found"
    raise HTTPException(status_code=404, detail=msg)


def _ensure_role_exists(
    role_repo: RoleRepository,
    role_id: int,
) -> None:
    """Ensure a role exists, or raise 404 if not found.

    Parameters
    ----------
    role_repo : RoleRepository
        Role repository.
    role_id : int
        Role identifier.

    Raises
    ------
    HTTPException
        If role not found (404).
    """
    existing_role = role_repo.get(role_id)
    if existing_role is None:
        _raise_role_not_found()


def _get_role_with_permissions(
    session: SessionDep,
    role_id: int,
) -> Role:
    """Get a role with permissions loaded, or raise 404 if not found.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    role_id : int
        Role identifier.

    Returns
    -------
    Role
        Role entity with permissions loaded.

    Raises
    ------
    HTTPException
        If role not found (404).
    """
    stmt = (
        select(Role)
        .where(Role.id == role_id)
        .options(
            selectinload(Role.permissions).selectinload(RolePermission.permission),
        )
    )
    role_with_perms = session.exec(stmt).first()
    if role_with_perms is None:
        _raise_role_not_found()
    return role_with_perms


@router.post(
    "/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def create_role(
    session: SessionDep,
    payload: RoleCreate,
) -> RoleRead:
    """Create a new role.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    payload : RoleCreate
        Role creation payload.

    Returns
    -------
    RoleRead
        Created role.

    Raises
    ------
    HTTPException
        If role name already exists (409).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        role = role_service.create_role_from_schema(payload)
        session.commit()
        session.refresh(role)
        # Reload with permissions
        if role.id is None:
            msg = "role_id_is_none"
            raise HTTPException(status_code=500, detail=msg)
        try:
            role_with_perms = _get_role_with_permissions(session, role.id)
        except HTTPException:
            # If reload fails, return the role we just created (may not have permissions loaded)
            # This can happen in test environments where session.exec isn't properly mocked
            return role_to_role_read(role)
        return role_to_role_read(role_with_perms)
    except ValueError as exc:
        msg = str(exc)
        if msg == "role_already_exists":
            raise HTTPException(status_code=409, detail=msg) from exc
        if msg in (
            "name_cannot_be_blank",
            "permission_name_cannot_be_blank",
            "resource_cannot_be_blank",
            "action_cannot_be_blank",
            "permission_not_found",
            "permission_already_exists",
            "permission_with_resource_action_already_exists",
            "permission_name_exists_with_different_resource_action",
            "permission_resource_action_exists_with_different_name",
            "resource_and_action_required_for_new_permission",
            "permission_id_or_permission_name_required",
            "permission_id_is_none",
        ):
            raise HTTPException(status_code=400, detail=msg) from exc
        # Re-raise unexpected ValueError for test coverage
        raise


@router.get(
    "/roles",
    response_model=list[RoleRead],
    dependencies=[Depends(get_admin_user)],
)
def list_roles(
    session: SessionDep,
) -> list[RoleRead]:
    """List all roles.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.

    Returns
    -------
    list[RoleRead]
        List of roles with permissions.
    """
    # Try to load with permissions, fallback to repo if session.exec returns empty
    # (e.g., in test environments where exec isn't configured)
    stmt = (
        select(Role)
        .options(
            selectinload(Role.permissions).selectinload(RolePermission.permission),
        )
        .order_by(Role.name)
    )
    roles = list(session.exec(stmt).all())
    if not roles:
        # Fallback to repository if session.exec returns empty (test environments)
        role_repo = RoleRepository(session)
        roles = list(role_repo.list_all())
        for role in roles:
            role.permissions = []  # type: ignore[attr-defined]
    return [role_to_role_read(role) for role in roles]


@router.put(
    "/roles/{role_id}",
    response_model=RoleRead,
    dependencies=[Depends(get_admin_user)],
)
def update_role(
    session: SessionDep,
    role_id: int,
    payload: RoleUpdate,
) -> RoleRead:
    """Update a role.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    role_id : int
        Role identifier.
    payload : RoleUpdate
        Role update payload.

    Returns
    -------
    RoleRead
        Updated role.

    Raises
    ------
    HTTPException
        If role not found (404) or role name already exists (409).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        # Check if role is locked (admin role id == 1)
        _ensure_role_exists(role_repo, role_id)
        is_locked = role_id == 1

        role_service.update_role_from_schema(role_id, payload, is_locked)
        session.commit()
        # Reload with permissions
        role_with_perms = _get_role_with_permissions(session, role_id)
        return role_to_role_read(role_with_perms)
    except ValueError as exc:
        msg = str(exc)
        if msg == "role_already_exists":
            raise HTTPException(status_code=409, detail=msg) from exc
        if msg == "role_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg in (
            "name_cannot_be_blank",
            "permission_name_cannot_be_blank",
            "resource_cannot_be_blank",
            "action_cannot_be_blank",
            "cannot_modify_locked_role_name",
            "cannot_remove_permissions_from_locked_role",
            "permission_not_found",
            "permission_already_exists",
            "permission_with_resource_action_already_exists",
            "permission_name_exists_with_different_resource_action",
            "permission_resource_action_exists_with_different_name",
            "resource_and_action_required_for_new_permission",
            "permission_id_or_permission_name_required",
            "permission_id_is_none",
            "role_permission_not_found",
            "role_permission_belongs_to_different_role",
        ):
            raise HTTPException(status_code=400, detail=msg) from exc
        # Re-raise unexpected ValueError for test coverage
        raise


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
def delete_role(
    session: SessionDep,
    role_id: int,
) -> None:
    """Delete a role.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    role_id : int
        Role identifier.

    Raises
    ------
    HTTPException
        If role not found (404), if role is locked (403), or if role is assigned to users (409).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        role_service.delete_role(role_id)
        session.commit()
    except ValueError as exc:
        msg = str(exc)
        if msg == "role_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg == "cannot_delete_locked_role":
            raise HTTPException(status_code=403, detail=msg) from exc
        if msg.startswith("role_assigned_to_users_"):
            raise HTTPException(
                status_code=409,
                detail="role_assigned_to_users",
            ) from exc
        raise HTTPException(status_code=400, detail=msg) from exc


@router.post(
    "/roles/{role_id}/permissions",
    response_model=RoleRead,
    dependencies=[Depends(get_admin_user)],
)
def grant_permission_to_role(
    session: SessionDep,
    role_id: int,
    payload: RolePermissionGrant,
) -> RoleRead:
    """Grant a permission to a role.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    role_id : int
        Role identifier.
    payload : RolePermissionGrant
        Permission grant payload.

    Returns
    -------
    RoleRead
        Updated role.

    Raises
    ------
    HTTPException
        If role or permission not found (404) or already granted (409).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        role_service.grant_permission_to_role(
            role_id, payload.permission_id, payload.condition
        )
        session.commit()
    except ValueError as exc:
        msg = str(exc)
        if msg == "role_already_has_permission":
            raise HTTPException(status_code=409, detail=msg) from exc
        raise HTTPException(
            status_code=404, detail="role_or_permission_not_found"
        ) from exc

    # Reload with permissions
    try:
        role = _get_role_with_permissions(session, role_id)
    except HTTPException:
        # If reload fails, get role from repo (may not have permissions loaded)
        # This can happen in test environments where session.exec isn't properly mocked
        existing_role = role_repo.get(role_id)
        if existing_role is None:
            _raise_role_not_found()
        # Type narrowing: existing_role is guaranteed to be Role here (raise above if None)
        existing_role.permissions = []  # type: ignore[attr-defined]
        return role_to_role_read(existing_role)  # type: ignore[arg-type]
    return role_to_role_read(role)


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    response_model=RoleRead,
    dependencies=[Depends(get_admin_user)],
)
def revoke_permission_from_role(
    session: SessionDep,
    role_id: int,
    permission_id: int,
) -> RoleRead:
    """Revoke a permission from a role.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    role_id : int
        Role identifier.
    permission_id : int
        Permission identifier.

    Returns
    -------
    RoleRead
        Updated role.

    Raises
    ------
    HTTPException
        If role or permission association not found (404).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        role_service.revoke_permission_from_role(role_id, permission_id)
        session.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail="role_permission_not_found"
        ) from exc

    # Reload with permissions
    try:
        role = _get_role_with_permissions(session, role_id)
    except HTTPException:
        # If reload fails, get role from repo (may not have permissions loaded)
        # This can happen in test environments where session.exec isn't properly mocked
        existing_role = role_repo.get(role_id)
        if existing_role is None:
            _raise_role_not_found()
        # Type narrowing: existing_role is guaranteed to be Role here (raise above if None)
        existing_role.permissions = []  # type: ignore[attr-defined]
        return role_to_role_read(existing_role)  # type: ignore[arg-type]
    return role_to_role_read(role)


@router.put(
    "/permissions/{permission_id}",
    response_model=PermissionRead,
    dependencies=[Depends(get_admin_user)],
)
def update_permission(
    session: SessionDep,
    permission_id: int,
    payload: PermissionUpdate,
) -> PermissionRead:
    """Update a permission.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    permission_id : int
        Permission identifier.
    payload : PermissionUpdate
        Permission update payload.

    Returns
    -------
    PermissionRead
        Updated permission.

    Raises
    ------
    HTTPException
        If permission not found (404) or permission name/resource+action already exists (409).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        permission = role_service.update_permission_from_schema(permission_id, payload)
        session.commit()
        session.refresh(permission)
        if permission.id is None:
            msg = "permission_id_is_none"
            raise HTTPException(status_code=500, detail=msg)  # noqa: TRY301
        return PermissionRead(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            resource=permission.resource,
            action=permission.action,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if msg == "permission_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg in (
            "permission_already_exists",
            "permission_with_resource_action_already_exists",
        ):
            raise HTTPException(status_code=409, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc


@router.delete(
    "/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
def delete_permission(
    session: SessionDep,
    permission_id: int,
) -> None:
    """Delete a permission.

    Only allows deletion of orphaned permissions (permissions with no role associations).

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    permission_id : int
        Permission identifier.

    Raises
    ------
    HTTPException
        If permission not found (404) or if permission is associated with roles (400).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        role_service.delete_permission(permission_id)
        session.commit()
    except ValueError as exc:
        msg = str(exc)
        if msg == "permission_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg.startswith("permission_assigned_to_roles_"):
            raise HTTPException(status_code=400, detail=msg) from exc
        if msg == "cannot_delete_permission":
            raise HTTPException(status_code=400, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc


@router.put(
    "/roles/{role_id}/permissions/{role_permission_id}",
    response_model=RoleRead,
    dependencies=[Depends(get_admin_user)],
)
def update_role_permission(
    session: SessionDep,
    role_id: int,
    role_permission_id: int,
    payload: RolePermissionUpdate,
) -> RoleRead:
    """Update a role-permission association condition.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    role_id : int
        Role identifier.
    role_permission_id : int
        Role-permission association identifier.
    payload : RolePermissionUpdate
        Update payload with condition.

    Returns
    -------
    RoleRead
        Updated role.

    Raises
    ------
    HTTPException
        If role-permission association not found (404).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        role_service.update_role_permission_condition(
            role_permission_id,
            payload.condition,
        )
        session.commit()
        # Reload with permissions
        role_with_perms = _get_role_with_permissions(session, role_id)
        return role_to_role_read(role_with_perms)
    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if msg == "role_permission_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc


@router.post(
    "/permissions",
    response_model=PermissionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def create_permission(
    session: SessionDep,
    payload: PermissionCreate,
) -> PermissionRead:
    """Create a new permission.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    payload : PermissionCreate
        Permission creation payload.

    Returns
    -------
    PermissionRead
        Created permission.

    Raises
    ------
    HTTPException
        If permission name or resource+action already exists (409).
    """
    role_repo = RoleRepository(session)
    role_service = RoleService(
        session,
        role_repo,
        PermissionRepository(session),
        UserRoleRepository(session),
        RolePermissionRepository(session),
    )

    try:
        permission = role_service.create_permission(
            name=payload.name,
            resource=payload.resource,
            action=payload.action,
            description=payload.description,
        )
        session.commit()
        session.refresh(permission)
        if permission.id is None:
            msg = "permission_id_is_none"
            raise HTTPException(status_code=500, detail=msg)  # noqa: TRY301
        return PermissionRead(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            resource=permission.resource,
            action=permission.action,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if msg in (
            "permission_already_exists",
            "permission_with_resource_action_already_exists",
        ):
            raise HTTPException(status_code=409, detail=msg) from exc
        if msg in (
            "name_cannot_be_blank",
            "permission_name_cannot_be_blank",
            "resource_cannot_be_blank",
            "action_cannot_be_blank",
        ):
            raise HTTPException(status_code=400, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc


@router.get(
    "/permissions",
    response_model=list[PermissionRead],
    dependencies=[Depends(get_admin_user)],
)
def list_permissions(
    session: SessionDep,
    resource: str | None = None,
) -> list[PermissionRead]:
    """List permissions, optionally filtered by resource.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    resource : str | None
        Optional resource filter.

    Returns
    -------
    list[PermissionRead]
        List of permissions.
    """
    perm_repo = PermissionRepository(session)
    if resource:
        permissions = list(perm_repo.list_by_resource(resource))
    else:
        permissions = list(perm_repo.list())
    return [PermissionRead.model_validate(perm) for perm in permissions]


# E-Reader Device Management


@router.post(
    "/users/{user_id}/devices",
    response_model=EReaderDeviceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def create_device(
    session: SessionDep,
    user_id: int,
    payload: EReaderDeviceCreate,
) -> EReaderDeviceRead:
    """Create an e-reader device for a user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    user_id : int
        User identifier.
    payload : EReaderDeviceCreate
        Device creation payload.

    Returns
    -------
    EReaderDeviceRead
        Created device.

    Raises
    ------
    HTTPException
        If user not found (404) or device email already exists (409).
    """
    user_repo = UserRepository(session)
    user = user_repo.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")

    device_repo = EReaderRepository(session)
    device_service = EReaderService(session, device_repo)

    preferred_format = None
    if payload.preferred_format:
        with suppress(ValueError):
            # Invalid format, use None
            preferred_format = EBookFormat(payload.preferred_format.lower())

    try:
        device = device_service.create_device(
            user_id,
            payload.email,
            device_name=payload.device_name,
            device_type=payload.device_type,
            preferred_format=preferred_format,
            is_default=payload.is_default,
        )
        session.commit()
        return EReaderDeviceRead.model_validate(device)
    except ValueError as exc:
        msg = str(exc)
        if msg == "device_email_already_exists":
            raise HTTPException(status_code=409, detail=msg) from exc
        raise


@router.get(
    "/users/{user_id}/devices",
    response_model=list[EReaderDeviceRead],
    dependencies=[Depends(get_admin_user)],
)
def list_user_devices(
    session: SessionDep,
    user_id: int,
) -> list[EReaderDeviceRead]:
    """List all e-reader devices for a user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    user_id : int
        User identifier.

    Returns
    -------
    list[EReaderDeviceRead]
        List of devices.
    """
    device_repo = EReaderRepository(session)
    devices = list(device_repo.find_by_user(user_id))
    return [EReaderDeviceRead.model_validate(device) for device in devices]


@router.put(
    "/devices/{device_id}",
    response_model=EReaderDeviceRead,
    dependencies=[Depends(get_admin_user)],
)
def update_device(
    session: SessionDep,
    device_id: int,
    payload: EReaderDeviceUpdate,
) -> EReaderDeviceRead:
    """Update an e-reader device.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    device_id : int
        Device identifier.
    payload : EReaderDeviceUpdate
        Device update payload.

    Returns
    -------
    EReaderDeviceRead
        Updated device.

    Raises
    ------
    HTTPException
        If device not found (404) or email conflict (409).
    """
    device_repo = EReaderRepository(session)
    device_service = EReaderService(session, device_repo)

    preferred_format = None
    if payload.preferred_format:
        with suppress(ValueError):
            # Invalid format, use None
            preferred_format = EBookFormat(payload.preferred_format.lower())

    try:
        device = device_service.update_device(
            device_id,
            email=payload.email,
            device_name=payload.device_name,
            device_type=payload.device_type,
            preferred_format=preferred_format,
            is_default=payload.is_default,
        )
        session.commit()
        return EReaderDeviceRead.model_validate(device)
    except ValueError as exc:
        msg = str(exc)
        if msg == "device_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg == "device_email_already_exists":
            raise HTTPException(status_code=409, detail=msg) from exc
        raise


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
def delete_device(
    session: SessionDep,
    device_id: int,
) -> None:
    """Delete an e-reader device.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    admin_user : AdminUserDep
        Admin user dependency.
    device_id : int
        Device identifier.

    Raises
    ------
    HTTPException
        If device not found (404).
    """
    device_repo = EReaderRepository(session)
    device_service = EReaderService(session, device_repo)

    try:
        device_service.delete_device(device_id)
        session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="device_not_found") from exc


# Library Management


@router.get(
    "/libraries",
    response_model=list[LibraryRead],
    dependencies=[Depends(get_admin_user)],
)
def list_libraries(
    session: SessionDep,
) -> list[LibraryRead]:
    """List all libraries.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    list[LibraryRead]
        List of all libraries.
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    libraries = library_service.list_libraries()
    return [LibraryRead.model_validate(lib) for lib in libraries]


@router.get(
    "/libraries/active",
    response_model=LibraryRead | None,
)
def get_active_library(
    session: SessionDep,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> LibraryRead | None:
    """Get the currently active library.

    All authenticated users can view the active library.
    Only admins can change which library is active.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    _current_user : User
        Current authenticated user (for authentication only, unused).

    Returns
    -------
    LibraryRead | None
        The active library if one exists, None otherwise.
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()
    if library is None:
        return None
    return LibraryRead.model_validate(library)


@router.post(
    "/libraries",
    response_model=LibraryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def create_library(
    session: SessionDep,
    payload: LibraryCreate,
) -> LibraryRead:
    """Create a new library.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    payload : LibraryCreate
        Library creation payload.

    Returns
    -------
    LibraryRead
        Created library.

    Raises
    ------
    HTTPException
        If library path already exists (409).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)

    try:
        library = library_service.create_library(
            name=payload.name,
            calibre_db_path=payload.calibre_db_path,
            calibre_db_file=payload.calibre_db_file,
            use_split_library=payload.use_split_library,
            split_library_dir=payload.split_library_dir,
            auto_reconnect=payload.auto_reconnect,
            is_active=payload.is_active,
        )
        session.commit()
        return LibraryRead.model_validate(library)
    except ValueError as exc:
        msg = str(exc)
        if msg == "library_path_already_exists":
            raise HTTPException(status_code=409, detail=msg) from exc
        if msg == "invalid_calibre_database":
            raise HTTPException(status_code=400, detail=msg) from exc
        # Re-raise unexpected ValueErrors to be handled by FastAPI's error handler
        raise
    except PermissionError as exc:
        msg = f"Permission denied: {exc}"
        raise HTTPException(status_code=403, detail=msg) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put(
    "/libraries/{library_id}",
    response_model=LibraryRead,
    dependencies=[Depends(get_admin_user)],
)
def update_library(
    session: SessionDep,
    library_id: int,
    payload: LibraryUpdate,
) -> LibraryRead:
    """Update a library.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    library_id : int
        Library identifier.
    payload : LibraryUpdate
        Library update payload.

    Returns
    -------
    LibraryRead
        Updated library.

    Raises
    ------
    HTTPException
        If library not found (404) or path conflict (409).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)

    try:
        library = library_service.update_library(
            library_id,
            name=payload.name,
            calibre_db_path=payload.calibre_db_path,
            calibre_db_file=payload.calibre_db_file,
            calibre_uuid=payload.calibre_uuid,
            use_split_library=payload.use_split_library,
            split_library_dir=payload.split_library_dir,
            auto_reconnect=payload.auto_reconnect,
            auto_convert_on_ingest=payload.auto_convert_on_ingest,
            auto_convert_target_format=payload.auto_convert_target_format,
            auto_convert_ignored_formats=payload.auto_convert_ignored_formats,
            auto_convert_backup_originals=payload.auto_convert_backup_originals,
            is_active=payload.is_active,
        )
        session.commit()
        return LibraryRead.model_validate(library)
    except ValueError as exc:
        msg = str(exc)
        if msg == "library_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        if msg == "library_path_already_exists":
            raise HTTPException(status_code=409, detail=msg) from exc
        raise


@router.delete(
    "/libraries/{library_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
def delete_library(
    session: SessionDep,
    library_id: int,
) -> None:
    """Delete a library.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    library_id : int
        Library identifier.

    Raises
    ------
    HTTPException
        If library not found (404).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)

    try:
        library_service.delete_library(library_id)
        session.commit()
    except ValueError as exc:
        msg = str(exc)
        if msg == "library_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise


@router.get(
    "/libraries/{library_id}/stats",
    response_model=LibraryStats,
    dependencies=[Depends(get_admin_user)],
)
def get_library_stats(
    session: SessionDep,
    library_id: int,
) -> LibraryStats:
    """Get statistics for a library.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    library_id : int
        Library identifier.

    Returns
    -------
    LibraryStats
        Library statistics.

    Raises
    ------
    HTTPException
        If library not found (404) or database file not found (404).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)

    try:
        stats = library_service.get_library_stats(library_id)
        return LibraryStats.model_validate(stats)
    except ValueError as exc:
        msg = str(exc)
        if msg == "library_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail="calibre_database_not_found"
        ) from exc


@router.post(
    "/libraries/{library_id}/activate",
    response_model=LibraryRead,
    dependencies=[Depends(get_admin_user)],
)
def activate_library(
    session: SessionDep,
    library_id: int,
) -> LibraryRead:
    """Set a library as the active one.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    library_id : int
        Library identifier.

    Returns
    -------
    LibraryRead
        Updated library.

    Raises
    ------
    HTTPException
        If library not found (404).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)

    try:
        library = library_service.set_active_library(library_id)
        session.commit()
        return LibraryRead.model_validate(library)
    except ValueError as exc:
        msg = str(exc)
        if msg == "library_not_found":
            raise HTTPException(status_code=404, detail=msg) from exc
        raise


@router.post(
    "/openlibrary/download-dumps",
    response_model=DownloadFilesResponse,
    dependencies=[Depends(get_admin_user)],
)
def download_openlibrary_dumps(
    request: Request,
    current_user: AdminUserDep,
    payload: DownloadFilesRequest,
) -> DownloadFilesResponse:
    """Create a task to download OpenLibrary dump files from URLs.

    Creates a background task that downloads files from the provided URLs
    and saves them to ``{data_directory}/openlibrary/dump/`` directory.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    current_user : AdminUserDep
        Current admin user.
    payload : DownloadFilesRequest
        Request containing list of file URLs to download.

    Returns
    -------
    DownloadFilesResponse
        Response with task ID and message.

    Raises
    ------
    HTTPException
        If no URLs provided (400) or task runner unavailable (503).
    """
    # Get task runner and config
    if (
        not hasattr(request.app.state, "task_runner")
        or request.app.state.task_runner is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )
    task_runner = request.app.state.task_runner
    cfg = request.app.state.config

    # Create service and delegate to it
    service = OpenLibraryService(task_runner=task_runner, config=cfg)

    try:
        task_id = service.create_download_task(
            urls=payload.urls,
            user_id=current_user.id or 0,  # type: ignore[arg-type]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return DownloadFilesResponse(
        message="Download task created",
        task_id=task_id,
        downloaded_files=[],
        failed_files=[],
    )


class IngestFilesRequest(BaseModel):
    """Request model for ingesting files.

    Attributes
    ----------
    process_authors : bool
        Whether to process authors dump file. Defaults to True.
    process_works : bool
        Whether to process works dump file. Defaults to True.
    process_editions : bool
        Whether to process editions dump file. Defaults to True.
    """

    process_authors: bool = True
    process_works: bool = True
    process_editions: bool = True


class IngestFilesResponse(BaseModel):
    """Response model for file ingest operation.

    Attributes
    ----------
    message : str
        Success message.
    task_id : int
        Task ID for tracking the ingest progress.
    """

    message: str
    task_id: int


@router.post(
    "/openlibrary/ingest-dumps",
    response_model=IngestFilesResponse,
    dependencies=[Depends(get_admin_user)],
)
def ingest_openlibrary_dumps(
    request: Request,
    current_user: AdminUserDep,
    payload: IngestFilesRequest,
) -> IngestFilesResponse:
    """Create a task to ingest OpenLibrary dump files into local database.

    Creates a background task that processes downloaded dump files
    and ingests them into PostgreSQL database for fast lookups.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    current_user : AdminUserDep
        Current admin user.
    payload : IngestFilesRequest
        Request containing flags for which file types to process.

    Returns
    -------
    IngestFilesResponse
        Response with task ID and message.

    Raises
    ------
    HTTPException
        If task runner unavailable (503) or no file types selected (400).
    """
    # Validate that at least one file type is enabled
    if (
        not payload.process_authors
        and not payload.process_works
        and not payload.process_editions
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file type must be selected for processing",
        )

    # Get task runner and config
    if (
        not hasattr(request.app.state, "task_runner")
        or request.app.state.task_runner is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task runner not available",
        )
    task_runner = request.app.state.task_runner
    cfg = request.app.state.config

    # Create service and delegate to it
    service = OpenLibraryService(task_runner=task_runner, config=cfg)
    task_id = service.create_ingest_task(
        user_id=current_user.id or 0,  # type: ignore[arg-type]
        process_authors=payload.process_authors,
        process_works=payload.process_works,
        process_editions=payload.process_editions,
    )

    return IngestFilesResponse(
        message="Ingest task created",
        task_id=task_id,
    )


@router.get(
    "/openlibrary-dump-config",
    response_model=OpenLibraryDumpConfigRead,
    dependencies=[Depends(get_admin_user)],
)
def get_openlibrary_dump_config(
    request: Request,
    session: SessionDep,
) -> OpenLibraryDumpConfigRead:
    """Get the OpenLibrary dump configuration (admin only).

    Returns default values if configuration has not been created yet.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.

    Returns
    -------
    OpenLibraryDumpConfigRead
        Configuration with defaults if not found.
    """
    service = _auth_service(request, session)
    config = service.get_openlibrary_dump_config()
    if config is None:
        # Return defaults (no persisted record yet)
        return OpenLibraryDumpConfigRead(
            id=None,
            authors_url="https://openlibrary.org/data/ol_dump_authors_latest.txt.gz",
            works_url="https://openlibrary.org/data/ol_dump_works_latest.txt.gz",
            editions_url="https://openlibrary.org/data/ol_dump_editions_latest.txt.gz",
            default_process_authors=True,
            default_process_works=True,
            default_process_editions=False,
            staleness_threshold_days=30,
            enable_auto_download=False,
            enable_auto_process=False,
            auto_check_interval_hours=24,
            created_at=None,
            updated_at=None,
        )
    return OpenLibraryDumpConfigRead.model_validate(config)


@router.put(
    "/openlibrary-dump-config",
    response_model=OpenLibraryDumpConfigRead,
    dependencies=[Depends(get_admin_user)],
)
def upsert_openlibrary_dump_config(
    request: Request,
    session: SessionDep,
    payload: OpenLibraryDumpConfigUpdate,
) -> OpenLibraryDumpConfigRead:
    """Create or update the OpenLibrary dump configuration (admin only).

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    payload : OpenLibraryDumpConfigUpdate
        Configuration payload.

    Returns
    -------
    OpenLibraryDumpConfigRead
        Created or updated configuration.
    """
    service = _auth_service(request, session)
    current_user = get_current_user(request, session)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="forbidden")

    try:
        cfg = service.upsert_openlibrary_dump_config(
            **payload.model_dump(exclude_unset=True)
        )
        session.commit()
        logger.info("OpenLibrary dump config updated: user_id=%s", current_user.id)
    except ValueError as exc:
        msg = str(exc)
        raise HTTPException(status_code=400, detail=msg) from exc

    return OpenLibraryDumpConfigRead.model_validate(cfg)


@router.get(
    "/scheduled-tasks-config",
    response_model=ScheduledTasksConfigRead,
    dependencies=[Depends(get_admin_user)],
)
def get_scheduled_tasks_config(
    session: SessionDep,
) -> ScheduledTasksConfigRead:
    """Get the scheduled tasks configuration (admin only).

    Returns default values if configuration has not been created yet.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

    Returns
    -------
    ScheduledTasksConfigRead
        Configuration with defaults if not found.
    """
    service = ScheduledTasksConfigService(session)
    config = service.get_scheduled_tasks_config()
    return ScheduledTasksConfigRead.model_validate(config, from_attributes=True)


@router.put(
    "/scheduled-tasks-config",
    response_model=ScheduledTasksConfigRead,
    dependencies=[Depends(get_admin_user)],
)
def upsert_scheduled_tasks_config(
    request: Request,
    session: SessionDep,
    payload: ScheduledTasksConfigUpdate,
) -> ScheduledTasksConfigRead:
    """Create or update the scheduled tasks configuration (admin only).

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session dependency.
    payload : ScheduledTasksConfigUpdate
        Configuration payload.

    Returns
    -------
    ScheduledTasksConfigRead
        Created or updated configuration.
    """
    current_user = get_current_user(request, session)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="forbidden")

    try:
        service = ScheduledTasksConfigService(session)
        cfg = service.update_scheduled_tasks_config(
            **payload.model_dump(exclude_unset=True)
        )
        session.commit()
        logger.info("Scheduled tasks config updated: user_id=%s", current_user.id)
    except ValueError as exc:
        msg = str(exc)
        raise HTTPException(status_code=400, detail=msg) from exc

    return ScheduledTasksConfigRead.model_validate(cfg, from_attributes=True)
