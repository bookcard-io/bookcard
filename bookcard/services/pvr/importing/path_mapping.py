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

"""Path mapping service for PVR import."""

import logging
from pathlib import Path

from bookcard.models.pvr import DownloadItem

logger = logging.getLogger(__name__)


class PathMappingService:
    """Resolves download client path mappings."""

    def resolve_download_path(self, download_item: DownloadItem) -> Path:
        """Resolve the local download path using client mappings.

        Parameters
        ----------
        download_item : DownloadItem
            Download item to resolve path for.

        Returns
        -------
        Path
            Resolved local path.
        """
        original_path = download_item.file_path
        if not original_path:
            return Path()

        client = download_item.client
        if not client or not client.additional_settings:
            return Path(original_path)

        path_mappings = client.additional_settings.get("path_mappings")
        if not path_mappings or not isinstance(path_mappings, list):
            return Path(original_path)

        for mapping in path_mappings:
            if not isinstance(mapping, dict):
                continue

            remote = mapping.get("remote")
            local = mapping.get("local")

            if not remote or not local:
                continue

            # If path starts with remote path, replace it
            if original_path.startswith(remote):
                resolved_path = original_path.replace(remote, local, 1)
                logger.debug(
                    "Mapped remote path '%s' to local path '%s'",
                    original_path,
                    resolved_path,
                )
                return Path(resolved_path)

        return Path(original_path)
