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

"""Download service module exports."""

from bookcard.services.download.client_selector import (
    DownloadClientSelector,
    FirstEnabledSelector,
    ProtocolBasedSelector,
)
from bookcard.services.download.factory import (
    DefaultDownloadClientFactory,
    DownloadClientFactory,
)
from bookcard.services.download.item_updater import DownloadItemUpdater
from bookcard.services.download.repository import (
    DownloadItemRepository,
    SQLModelDownloadItemRepository,
)
from bookcard.services.download.status_mapper import (
    ClientStatusMapper,
    DefaultStatusMapper,
    DownloadStatusMapper,
)
from bookcard.services.download.types import ClientItemInfo

__all__ = [
    "ClientItemInfo",
    "ClientStatusMapper",
    "DefaultDownloadClientFactory",
    "DefaultStatusMapper",
    "DownloadClientFactory",
    "DownloadClientSelector",
    "DownloadItemRepository",
    "DownloadItemUpdater",
    "DownloadStatusMapper",
    "FirstEnabledSelector",
    "ProtocolBasedSelector",
    "SQLModelDownloadItemRepository",
]
