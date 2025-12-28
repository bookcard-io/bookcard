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

"""Prowlarr configuration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from bookcard.api.deps import get_admin_user, get_db_session
from bookcard.api.schemas.prowlarr import (
    ProwlarrConfigCreate,  # noqa: F401
    ProwlarrConfigRead,
    ProwlarrConfigUpdate,
)
from bookcard.models.auth import User  # noqa: F401
from bookcard.models.pvr import ProwlarrConfig
from bookcard.pvr.sync.service import ProwlarrSyncService

router = APIRouter(prefix="/prowlarr", tags=["prowlarr"])


@router.get(
    "/config",
    response_model=ProwlarrConfigRead,
    dependencies=[Depends(get_admin_user)],
)
def get_prowlarr_config(
    session: Annotated[Session, Depends(get_db_session)],
) -> ProwlarrConfig:
    """Get Prowlarr configuration.

    Returns the current Prowlarr configuration. If none exists, creates
    default configuration.

    Permissions
    -----------
    Requires admin privileges.
    """
    config = session.exec(select(ProwlarrConfig)).first()
    if not config:
        config = ProwlarrConfig()
        session.add(config)
        session.commit()
        session.refresh(config)
    return config


@router.put(
    "/config",
    response_model=ProwlarrConfigRead,
    dependencies=[Depends(get_admin_user)],
)
def update_prowlarr_config(
    data: ProwlarrConfigUpdate,
    session: Annotated[Session, Depends(get_db_session)],
) -> ProwlarrConfig:
    """Update Prowlarr configuration.

    Permissions
    -----------
    Requires admin privileges.
    """
    config = session.exec(select(ProwlarrConfig)).first()
    if not config:
        config = ProwlarrConfig()
        session.add(config)

    # Update fields
    config.url = data.url
    if data.api_key is not None:
        config.api_key = data.api_key
    config.enabled = data.enabled
    config.sync_categories = data.sync_categories
    config.sync_app_profiles = data.sync_app_profiles
    config.sync_interval_minutes = data.sync_interval_minutes

    session.add(config)
    session.commit()
    session.refresh(config)
    return config


@router.post(
    "/sync",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_admin_user)],
)
def sync_prowlarr_indexers(
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, int]:
    """Manually trigger Prowlarr indexer sync.

    Fetches indexers from Prowlarr and updates the local indexer definitions.

    Permissions
    -----------
    Requires admin privileges.
    """
    service = ProwlarrSyncService(session)
    try:
        return service.sync_indexers()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prowlarr sync failed: {e}",
        ) from e
