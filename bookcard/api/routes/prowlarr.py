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

import contextlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from bookcard.api.deps import get_admin_user, get_data_encryptor, get_db_session
from bookcard.api.schemas.prowlarr import (
    ProwlarrConfigCreate,  # noqa: F401
    ProwlarrConfigRead,
    ProwlarrConfigUpdate,
)
from bookcard.models.auth import User  # noqa: F401
from bookcard.models.config import ScheduledJobDefinition
from bookcard.models.pvr import ProwlarrConfig
from bookcard.models.tasks import TaskType
from bookcard.pvr.sync.service import ProwlarrSyncService
from bookcard.services.config_service import ScheduledTasksConfigService

router = APIRouter(prefix="/prowlarr", tags=["prowlarr"])


def minutes_to_cron(minutes: int) -> str:
    """Convert minutes to a valid cron expression.

    Parameters
    ----------
    minutes : int
        Interval in minutes.

    Returns
    -------
    str
        Valid cron expression.

    Examples
    --------
    >>> minutes_to_cron(15)
    '*/15 * * * *'
    >>> minutes_to_cron(60)
    '0 * * * *'
    >>> minutes_to_cron(120)
    '0 */2 * * *'
    >>> minutes_to_cron(90)
    '0 */1 * * *'
    """
    # Ensure minimum of 1 minute
    if minutes < 1:
        minutes = 1

    if minutes < 60:
        # For intervals < 60 minutes, use minute field
        return f"*/{minutes} * * * *"
    if minutes == 60:
        # Exactly 60 minutes = every hour
        return "0 * * * *"
    if minutes % 60 == 0:
        # Multiple of 60 minutes, convert to hours
        hours = minutes // 60
        return f"0 */{hours} * * *"
    # Not a multiple of 60, round down to nearest hour
    # Cron doesn't easily support non-hour intervals > 60 minutes
    hours = minutes // 60
    if hours == 0:
        hours = 1
    return f"0 */{hours} * * *"


@router.get(
    "/config",
    response_model=ProwlarrConfigRead,
    dependencies=[Depends(get_admin_user)],
)
def get_prowlarr_config(
    session: Annotated[Session, Depends(get_db_session)],
    request: Request,
) -> ProwlarrConfigRead:
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

    # Decrypt API key for display
    decrypted_key = config.api_key
    if config.api_key:
        with contextlib.suppress(Exception):
            encryptor = get_data_encryptor(request)
            decrypted_key = encryptor.decrypt(config.api_key)

    # Convert to Pydantic model to avoid side effects on the DB object
    # This prevents the decrypted key from being saved back to the DB
    response = ProwlarrConfigRead.model_validate(config)
    response.api_key = decrypted_key
    return response


@router.put(
    "/config",
    response_model=ProwlarrConfigRead,
    dependencies=[Depends(get_admin_user)],
)
def update_prowlarr_config(
    data: ProwlarrConfigUpdate,
    session: Annotated[Session, Depends(get_db_session)],
    request: Request,
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
        encryptor = get_data_encryptor(request)
        config.api_key = encryptor.encrypt(data.api_key)
    config.enabled = data.enabled
    config.sync_categories = data.sync_categories
    config.sync_app_profiles = data.sync_app_profiles
    config.sync_interval_minutes = data.sync_interval_minutes

    session.add(config)
    session.commit()
    session.refresh(config)

    # Update scheduled task
    scheduled_tasks_service = ScheduledTasksConfigService(session)
    if config.enabled:
        scheduled_tasks_service.register_job(
            task_type=TaskType.PROWLARR_SYNC,
            cron_expression=minutes_to_cron(config.sync_interval_minutes),
            enabled=True,
            job_name="prowlarr_sync",
        )
    else:
        scheduled_tasks_service.unregister_job("prowlarr_sync")

    # Refresh scheduler to pick up changes immediately
    if hasattr(request.app.state, "scheduler") and request.app.state.scheduler:
        request.app.state.scheduler.refresh_jobs()

    return config


@router.post(
    "/sync",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_admin_user)],
)
def sync_prowlarr_indexers(
    session: Annotated[Session, Depends(get_db_session)],
    request: Request,
) -> dict[str, int]:
    """Manually trigger Prowlarr indexer sync.

    Fetches indexers from Prowlarr and updates the local indexer definitions.

    Permissions
    -----------
    Requires admin privileges.
    """
    encryptor = get_data_encryptor(request)
    service = ProwlarrSyncService(session, encryptor=encryptor)
    try:
        result = service.sync_indexers()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prowlarr sync failed: {e}",
        ) from e

    # Register health check task if it doesn't exist
    stmt = select(ScheduledJobDefinition).where(
        ScheduledJobDefinition.job_name == "indexer_health_check"
    )
    job = session.exec(stmt).first()
    if not job:
        scheduled_tasks_service = ScheduledTasksConfigService(session)
        scheduled_tasks_service.register_job(
            task_type=TaskType.INDEXER_HEALTH_CHECK,
            cron_expression="0 4 * * *",  # Daily at 4 AM
            enabled=True,
            job_name="indexer_health_check",
        )
        if hasattr(request.app.state, "scheduler") and request.app.state.scheduler:
            request.app.state.scheduler.refresh_jobs()

    return result
