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

"""KCC profile endpoints for managing user KCC conversion profiles."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from fundamental.api.deps import get_current_user, get_db_session
from fundamental.api.schemas.kcc import (
    KCCProfileCreate,
    KCCProfileRead,
    KCCProfileUpdate,
)
from fundamental.models.auth import User
from fundamental.services.kcc_profile_service import KCCProfileService

router = APIRouter(prefix="/kcc", tags=["kcc"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get("/profiles", response_model=list[KCCProfileRead])
def list_kcc_profiles(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[KCCProfileRead]:
    """List all KCC profiles for the current user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    list[KCCProfileRead]
        List of user's KCC profiles.
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    profile_service = KCCProfileService(session)
    profiles = profile_service.get_user_profiles(current_user.id)
    return [KCCProfileRead.model_validate(profile) for profile in profiles]


@router.post(
    "/profiles", response_model=KCCProfileRead, status_code=status.HTTP_201_CREATED
)
def create_kcc_profile(
    session: SessionDep,
    current_user: CurrentUserDep,
    payload: KCCProfileCreate,
) -> KCCProfileRead:
    """Create a new KCC profile for the current user.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    payload : KCCProfileCreate
        Profile creation payload.

    Returns
    -------
    KCCProfileRead
        Created profile.

    Raises
    ------
    HTTPException
        If profile creation fails (400).
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    profile_service = KCCProfileService(session)
    try:
        profile = profile_service.create_profile(current_user.id, payload)
        return KCCProfileRead.model_validate(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/profiles/{profile_id}", response_model=KCCProfileRead)
def get_kcc_profile(
    profile_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> KCCProfileRead:
    """Get a KCC profile by ID.

    Parameters
    ----------
    profile_id : int
        Profile ID.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    KCCProfileRead
        Profile details.

    Raises
    ------
    HTTPException
        If profile not found (404) or not owned by user (403).
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    profile_service = KCCProfileService(session)
    profile = profile_service.get_profile(profile_id, current_user.id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="profile_not_found",
        )

    return KCCProfileRead.model_validate(profile)


@router.put("/profiles/{profile_id}", response_model=KCCProfileRead)
def update_kcc_profile(
    profile_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    payload: KCCProfileUpdate,
) -> KCCProfileRead:
    """Update a KCC profile.

    Parameters
    ----------
    profile_id : int
        Profile ID to update.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.
    payload : KCCProfileUpdate
        Profile update payload.

    Returns
    -------
    KCCProfileRead
        Updated profile.

    Raises
    ------
    HTTPException
        If profile not found (404) or update fails (400).
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    profile_service = KCCProfileService(session)
    try:
        profile = profile_service.update_profile(profile_id, current_user.id, payload)
        return KCCProfileRead.model_validate(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kcc_profile(
    profile_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> None:
    """Delete a KCC profile.

    Parameters
    ----------
    profile_id : int
        Profile ID to delete.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Raises
    ------
    HTTPException
        If profile not found (404) or not owned by user (403).
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    profile_service = KCCProfileService(session)
    try:
        profile_service.delete_profile(profile_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/profiles/{profile_id}/set-default", response_model=KCCProfileRead)
def set_default_kcc_profile(
    profile_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> KCCProfileRead:
    """Set a KCC profile as the user's default.

    Parameters
    ----------
    profile_id : int
        Profile ID to set as default.
    session : SessionDep
        Database session dependency.
    current_user : CurrentUserDep
        Current authenticated user.

    Returns
    -------
    KCCProfileRead
        Updated profile.

    Raises
    ------
    HTTPException
        If profile not found (404) or not owned by user (403).
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_missing_id",
        )

    profile_service = KCCProfileService(session)
    try:
        profile = profile_service.set_default_profile(current_user.id, profile_id)
        return KCCProfileRead.model_validate(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
