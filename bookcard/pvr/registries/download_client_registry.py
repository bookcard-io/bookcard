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

"""Download client registry for PVR system.

This module manages the registration of download client implementations,
following SRP by separating registry concerns from factory logic.
"""

import logging

from bookcard.models.pvr import DownloadClientType
from bookcard.pvr.base import BaseDownloadClient

logger = logging.getLogger(__name__)

# Registry of download client type to class mapping
_download_client_registry: dict[DownloadClientType, type[BaseDownloadClient]] = {}


def register_download_client(
    client_type: DownloadClientType, client_class: type[BaseDownloadClient]
) -> None:
    """Register a download client implementation class.

    Parameters
    ----------
    client_type : DownloadClientType
        Type of download client (QBittorrent, Transmission, etc.).
    client_class : type[BaseDownloadClient]
        Download client class to register.

    Raises
    ------
    TypeError
        If client_class is not a subclass of BaseDownloadClient.
    """
    if not issubclass(client_class, BaseDownloadClient):
        msg = f"Download client class must subclass BaseDownloadClient: {client_class}"
        raise TypeError(msg)

    _download_client_registry[client_type] = client_class
    logger.info(
        "Registered download client type: %s -> %s", client_type, client_class.__name__
    )


def get_registered_download_client_types() -> list[DownloadClientType]:
    """Get list of registered download client types.

    Returns
    -------
    list[DownloadClientType]
        List of registered download client types.
    """
    return list(_download_client_registry.keys())


def get_download_client_class(
    client_type: DownloadClientType,
) -> type[BaseDownloadClient] | None:
    """Get registered download client class for type.

    Parameters
    ----------
    client_type : DownloadClientType
        Download client type.

    Returns
    -------
    type[BaseDownloadClient] | None
        Registered download client class or None if not registered.
    """
    return _download_client_registry.get(client_type)
