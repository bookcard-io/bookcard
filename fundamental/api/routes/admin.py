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

from contextlib import suppress
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, Response
from sqlmodel import Session

from fundamental.api.deps import get_admin_user, get_db_session
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
    PermissionRead,
    RoleCreate,
    RolePermissionGrant,
    RoleRead,
    UserRead,
    UserRoleAssign,
)
from fundamental.models.auth import EBookFormat, User
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
from fundamental.services.config_service import LibraryService
from fundamental.services.ereader_service import EReaderService
from fundamental.services.role_service import RoleService
from fundamental.services.security import PasswordHasher
from fundamental.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])

SessionDep = Annotated[Session, Depends(get_db_session)]
AdminUserDep = Annotated[User, Depends(get_admin_user)]


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
        role = role_service.create_role(payload.name, payload.description)
        session.commit()
        return RoleRead.model_validate(role)
    except ValueError as exc:
        if str(exc) == "role_already_exists":
            raise HTTPException(status_code=409, detail=str(exc)) from exc
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
        List of roles.
    """
    role_repo = RoleRepository(session)
    roles = list(role_repo.list_all())
    return [RoleRead.model_validate(role) for role in roles]


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
        If role not found (404).
    """
    role_repo = RoleRepository(session)
    role = role_repo.get(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="role_not_found")

    role_repo.delete(role)
    session.commit()


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

    role = role_repo.get(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="role_not_found")
    return RoleRead.model_validate(role)


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

    role = role_repo.get(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="role_not_found")
    return RoleRead.model_validate(role)


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
    dependencies=[Depends(get_admin_user)],
)
def get_active_library(
    session: SessionDep,
) -> LibraryRead | None:
    """Get the currently active library.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.

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
        raise


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
