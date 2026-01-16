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

"""Settings and constants for Direct HTTP download client."""

import tempfile

from bookcard.pvr.base import DownloadClientSettings


class DirectHttpSettings(DownloadClientSettings):
    """Settings for Direct HTTP download client."""


class DownloadConstants:
    """Constants for download operations."""

    RETENTION_SECONDS = 86400  # 24 hours
    DOWNLOAD_CHUNK_SIZE = 8192  # 8KB
    MAX_COUNTDOWN_SECONDS = 600  # 10 minutes
    DEFAULT_TEMP_DIR = tempfile.gettempdir()
    UPDATE_INTERVAL = 0.5  # 500ms
