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

"""API routes for managing Calibre plugins."""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session, select

from fundamental.api.deps import get_admin_user, get_db_session
from fundamental.api.schemas.plugins import PluginInfo, PluginInstallRequest
from fundamental.models.auth import EReaderDevice
from fundamental.services.calibre_plugin_service import (
    CalibreNotFoundError,
    CalibrePluginService,
)
from fundamental.services.dedrm_service import DeDRMService

router = APIRouter(prefix="/plugins", tags=["plugins"])
logger = logging.getLogger(__name__)


def get_plugin_service() -> CalibrePluginService:
    """Dependency for CalibrePluginService."""
    return CalibrePluginService()


def get_dedrm_service() -> DeDRMService:
    """Dependency for DeDRMService."""
    return DeDRMService()


@router.get(
    "/",
    response_model=list[PluginInfo],
    dependencies=[Depends(get_admin_user)],
)
def list_plugins(
    service: Annotated[CalibrePluginService, Depends(get_plugin_service)],
) -> list[PluginInfo]:
    """List installed Calibre plugins.

    Requires superuser privileges.
    """
    try:
        return service.list_plugins()
    except CalibreNotFoundError as e:
        logger.warning("Calibre not found: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_type": "calibre_not_found",
                "message": str(e),
                "message_type": "warning",
            },
        ) from e
    except Exception as e:
        logger.exception("Failed to list plugins")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def install_plugin_upload(
    file: Annotated[UploadFile, File(...)],
    service: Annotated[CalibrePluginService, Depends(get_plugin_service)],
) -> dict[str, str]:
    """Install a plugin from an uploaded ZIP file.

    Requires superuser privileges.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP files are supported.",
        )

    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        try:
            shutil.copyfileobj(file.file, temp_file)
            temp_file.close()

            service.install_plugin(temp_path)
        except CalibreNotFoundError as e:
            logger.warning("Calibre not found: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error_type": "calibre_not_found",
                    "message": str(e),
                    "message_type": "warning",
                },
            ) from e
        except Exception as e:
            logger.exception("Failed to install plugin from upload")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            ) from e
        else:
            return {"message": "Plugin installed successfully"}
        finally:
            if temp_path.exists():
                temp_path.unlink()


@router.post(
    "/git",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
def install_plugin_git(
    request: PluginInstallRequest,
    service: Annotated[CalibrePluginService, Depends(get_plugin_service)],
) -> dict[str, str]:
    """Install a plugin from a Git repository.

    Requires superuser privileges.
    """
    try:
        service.install_plugin_from_git(
            repo_url=request.repo_url,
            plugin_path_in_repo=request.plugin_path,
            branch=request.branch,
        )
    except CalibreNotFoundError as e:
        logger.warning("Calibre not found: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_type": "calibre_not_found",
                "message": str(e),
                "message_type": "warning",
            },
        ) from e
    except Exception as e:
        logger.exception("Failed to install plugin from Git")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    else:
        return {"message": "Plugin installed successfully from Git"}


@router.delete(
    "/{plugin_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
def remove_plugin(
    plugin_name: str,
    service: Annotated[CalibrePluginService, Depends(get_plugin_service)],
) -> None:
    """Remove an installed plugin.

    Requires superuser privileges.
    """
    try:
        service.remove_plugin(plugin_name)
    except CalibreNotFoundError as e:
        logger.warning("Calibre not found: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_type": "calibre_not_found",
                "message": str(e),
                "message_type": "warning",
            },
        ) from e
    except Exception as e:
        logger.exception("Failed to remove plugin")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/dedrm/sync",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_admin_user)],
)
def sync_dedrm_config(
    dedrm_service: Annotated[DeDRMService, Depends(get_dedrm_service)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    """Sync DeDRM configuration with device serial numbers.

    Requires superuser privileges.
    """
    try:
        # Fetch all devices with serial numbers
        stmt = select(EReaderDevice.serial_number).where(
            EReaderDevice.serial_number is not None
        )
        serial_numbers = list(session.exec(stmt).all())

        # Filter out empty strings if any
        valid_serials = [s for s in serial_numbers if s and s.strip()]

        if not valid_serials:
            return {"message": "No serial numbers found to sync."}

        dedrm_service.update_configuration(valid_serials)

        return {
            "message": f"Successfully synced {len(valid_serials)} serial numbers to DeDRM configuration."
        }
    except Exception as e:
        logger.exception("Failed to sync DeDRM configuration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
