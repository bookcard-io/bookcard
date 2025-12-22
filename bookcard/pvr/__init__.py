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

"""PVR (Personal Video Recorder) system for book tracking and downloading."""

# Import indexers and download clients to trigger auto-registration
import bookcard.pvr.download_clients  # noqa: F401
import bookcard.pvr.indexers  # noqa: F401
from bookcard.pvr.base import (
    BaseDownloadClient,
    BaseIndexer,
    DownloadClientSettings,
    IndexerSettings,
    PVRProviderError,
    handle_api_error_response,
    handle_http_error_response,
)
from bookcard.pvr.factory import (
    create_download_client,
    create_indexer,
    get_registered_download_client_types,
    get_registered_indexer_types,
    register_download_client,
    register_indexer,
)
from bookcard.pvr.models import ReleaseInfo

__all__ = [
    "BaseDownloadClient",
    "BaseIndexer",
    "DownloadClientSettings",
    "IndexerSettings",
    "PVRProviderError",
    "ReleaseInfo",
    "create_download_client",
    "create_indexer",
    "get_registered_download_client_types",
    "get_registered_indexer_types",
    "handle_api_error_response",
    "handle_http_error_response",
    "register_download_client",
    "register_indexer",
]
