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

"""KCC profile service for managing user KCC conversion profiles.

Handles CRUD operations for user-level KCC conversion configuration profiles.
"""

import logging
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from fundamental.models.kcc_config import KCCConversionProfile

if TYPE_CHECKING:
    from pydantic import BaseModel

logger = logging.getLogger(__name__)


class KCCProfileService:
    """Service for managing KCC conversion profiles.

    Provides operations for creating, reading, updating, and deleting
    user-level KCC conversion profiles.

    Parameters
    ----------
    session : Session
        Database session.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize KCC profile service.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def _convert_to_dict(self, profile_data: "BaseModel | dict") -> dict:
        """Convert profile data to dictionary.

        Parameters
        ----------
        profile_data : BaseModel | dict
            Profile data to convert.

        Returns
        -------
        dict
            Dictionary representation of profile data.
        """
        if isinstance(profile_data, dict):
            return profile_data

        # Try model_dump (Pydantic v2)
        if hasattr(profile_data, "model_dump"):
            method = profile_data.model_dump
            if callable(method):
                return method(exclude_unset=True)  # type: ignore[call-arg]

        # Try dict (Pydantic v1) - deprecated but kept for compatibility
        method = getattr(profile_data, "dict", None)
        if callable(method):
            return method(exclude_unset=True)  # type: ignore[call-arg]

        # Fallback to dict() constructor
        return dict(profile_data)

    def get_user_profiles(self, user_id: int) -> list[KCCConversionProfile]:
        """Get all KCC profiles for a user.

        Parameters
        ----------
        user_id : int
            User ID.

        Returns
        -------
        list[KCCConversionProfile]
            List of user's KCC profiles.
        """
        stmt = select(KCCConversionProfile).where(
            KCCConversionProfile.user_id == user_id
        )
        profiles = self._session.exec(stmt).all()
        return list(profiles)

    def get_default_profile(self, user_id: int) -> KCCConversionProfile | None:
        """Get user's default KCC profile.

        Parameters
        ----------
        user_id : int
            User ID.

        Returns
        -------
        KCCConversionProfile | None
            Default profile if found, None otherwise.
        """
        stmt = (
            select(KCCConversionProfile)
            .where(KCCConversionProfile.user_id == user_id)
            .where(KCCConversionProfile.is_default == True)  # noqa: E712
        )
        return self._session.exec(stmt).first()

    def get_profile(self, profile_id: int, user_id: int) -> KCCConversionProfile | None:
        """Get a specific KCC profile by ID.

        Parameters
        ----------
        profile_id : int
            Profile ID.
        user_id : int
            User ID (for authorization check).

        Returns
        -------
        KCCConversionProfile | None
            Profile if found and owned by user, None otherwise.
        """
        stmt = (
            select(KCCConversionProfile)
            .where(KCCConversionProfile.id == profile_id)
            .where(KCCConversionProfile.user_id == user_id)
        )
        return self._session.exec(stmt).first()

    def create_profile(
        self,
        user_id: int,
        profile_data: "BaseModel | dict",
    ) -> KCCConversionProfile:
        """Create a new KCC profile.

        Parameters
        ----------
        user_id : int
            User ID who owns the profile.
        profile_data : BaseModel | dict
            Profile data (can be Pydantic model or dict).

        Returns
        -------
        KCCConversionProfile
            Created profile.

        Raises
        ------
        ValueError
            If profile data is invalid or if setting as default conflicts
            with existing default profile.
        """
        # Convert to dict if needed
        data = self._convert_to_dict(profile_data)

        # Check if setting as default
        is_default = data.get("is_default", False)
        if is_default:
            # Unset existing default
            self._unset_default_profile(user_id)

        # Create profile
        profile = KCCConversionProfile(
            user_id=user_id,
            **data,
        )

        self._session.add(profile)
        self._session.commit()
        self._session.refresh(profile)

        logger.info("Created KCC profile %d for user %d", profile.id, user_id)
        return profile

    def update_profile(
        self,
        profile_id: int,
        user_id: int,
        profile_data: "BaseModel | dict",
    ) -> KCCConversionProfile:
        """Update an existing KCC profile.

        Parameters
        ----------
        profile_id : int
            Profile ID to update.
        user_id : int
            User ID (for authorization check).
        profile_data : BaseModel | dict
            Updated profile data.

        Returns
        -------
        KCCConversionProfile
            Updated profile.

        Raises
        ------
        ValueError
            If profile not found, not owned by user, or if setting as default
            conflicts with existing default profile.
        """
        profile = self.get_profile(profile_id, user_id)
        if profile is None:
            msg = f"KCC profile {profile_id} not found or not owned by user {user_id}"
            raise ValueError(msg)

        # Convert to dict if needed
        data = self._convert_to_dict(profile_data)

        # Check if setting as default
        is_default = data.get("is_default")
        if is_default is True and not profile.is_default:
            # Unset existing default
            self._unset_default_profile(user_id)

        # Update fields
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        self._session.add(profile)
        self._session.commit()
        self._session.refresh(profile)

        logger.info("Updated KCC profile %d for user %d", profile_id, user_id)
        return profile

    def delete_profile(self, profile_id: int, user_id: int) -> None:
        """Delete a KCC profile.

        Parameters
        ----------
        profile_id : int
            Profile ID to delete.
        user_id : int
            User ID (for authorization check).

        Raises
        ------
        ValueError
            If profile not found or not owned by user.
        """
        profile = self.get_profile(profile_id, user_id)
        if profile is None:
            msg = f"KCC profile {profile_id} not found or not owned by user {user_id}"
            raise ValueError(msg)

        self._session.delete(profile)
        self._session.commit()

        logger.info("Deleted KCC profile %d for user %d", profile_id, user_id)

    def set_default_profile(
        self, user_id: int, profile_id: int
    ) -> KCCConversionProfile:
        """Set a profile as the user's default.

        Parameters
        ----------
        user_id : int
            User ID.
        profile_id : int
            Profile ID to set as default.

        Returns
        -------
        KCCConversionProfile
            Updated profile.

        Raises
        ------
        ValueError
            If profile not found or not owned by user.
        """
        profile = self.get_profile(profile_id, user_id)
        if profile is None:
            msg = f"KCC profile {profile_id} not found or not owned by user {user_id}"
            raise ValueError(msg)

        # Unset existing default
        self._unset_default_profile(user_id)

        # Set new default
        profile.is_default = True
        self._session.add(profile)
        self._session.commit()
        self._session.refresh(profile)

        logger.info("Set KCC profile %d as default for user %d", profile_id, user_id)
        return profile

    def _unset_default_profile(self, user_id: int) -> None:
        """Unset the current default profile for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        """
        current_default = self.get_default_profile(user_id)
        if current_default:
            current_default.is_default = False
            self._session.add(current_default)
