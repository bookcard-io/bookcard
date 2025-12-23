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

"""Factory for creating PVR download clients from database definitions.

This module provides factory functions for creating download clients, following SRP
by separating download client creation from indexer creation.
"""

from collections.abc import Callable

from bookcard.models.pvr import DownloadClientDefinition, DownloadClientType
from bookcard.pvr.base import BaseDownloadClient, DownloadClientSettings
from bookcard.pvr.base.interfaces import HttpClientProtocol
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.http.client import HttpxClient
from bookcard.pvr.registries.download_client_registry import get_download_client_class
from bookcard.pvr.services.file_fetcher import FileFetcher
from bookcard.pvr.utils.url_router import DownloadUrlRouter

# Registry of download client type to settings factory function
_download_client_settings_factories: dict[
    DownloadClientType, Callable[[DownloadClientDefinition], DownloadClientSettings]
] = {}


def register_download_client_settings_factory(
    client_type: DownloadClientType,
    factory: Callable[[DownloadClientDefinition], DownloadClientSettings],
) -> None:
    """Register a settings factory for a download client type.

    Parameters
    ----------
    client_type : DownloadClientType
        Download client type to register factory for.
    factory : Callable[[DownloadClientDefinition], DownloadClientSettings]
        Factory function that creates settings from definition.
    """
    _download_client_settings_factories[client_type] = factory


def create_download_client(client_def: DownloadClientDefinition) -> BaseDownloadClient:
    """Create a download client instance from a database definition.

    Parameters
    ----------
    client_def : DownloadClientDefinition
        Download client definition from database.

    Returns
    -------
    BaseDownloadClient
        Download client instance.

    Raises
    ------
    PVRProviderError
        If client type is not registered or creation fails.
    """
    client_class = get_download_client_class(client_def.client_type)
    if client_class is None:
        msg = f"Download client type not registered: {client_def.client_type}"
        raise PVRProviderError(msg)

    # Get settings factory for this client type, or use default
    settings_factory = _download_client_settings_factories.get(
        client_def.client_type, _create_default_download_client_settings
    )
    settings = settings_factory(client_def)

    try:
        # Create dependencies
        file_fetcher = FileFetcher(timeout=settings.timeout_seconds)
        url_router = DownloadUrlRouter()

        # Create HTTP client factory using settings
        def http_client_factory() -> HttpClientProtocol:
            # We return HttpxClient which satisfies HttpClientProtocol
            return HttpxClient(
                timeout=settings.timeout_seconds,
                verify=True,  # Default verification
                follow_redirects=True,
            )

        return client_class(
            settings=settings,
            file_fetcher=file_fetcher,
            url_router=url_router,
            http_client_factory=http_client_factory,
            enabled=client_def.enabled,
        )
    except Exception as e:
        msg = f"Failed to create download client {client_def.name}: {e}"
        raise PVRProviderError(msg) from e


def _create_default_download_client_settings(
    client_def: DownloadClientDefinition,
) -> DownloadClientSettings:
    """Create default DownloadClientSettings from client definition.

    Parameters
    ----------
    client_def : DownloadClientDefinition
        Download client definition.

    Returns
    -------
    DownloadClientSettings
        DownloadClientSettings instance.
    """
    from bookcard.pvr.base import DownloadClientSettings

    settings = DownloadClientSettings(
        host=client_def.host,
        port=client_def.port,
        username=client_def.username,
        password=client_def.password,
        use_ssl=client_def.use_ssl,
        timeout_seconds=client_def.timeout_seconds,
        category=client_def.category,
        download_path=client_def.download_path,
    )

    # Allow subclasses to extend settings with additional_settings
    if client_def.additional_settings:
        for key, value in client_def.additional_settings.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

    return settings
