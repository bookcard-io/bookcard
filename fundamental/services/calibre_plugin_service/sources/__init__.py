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

"""Plugin sources."""

from fundamental.services.calibre_plugin_service.sources.base import (
    DefaultTempDirectoryFactory,
    PluginSource,
    TempDirectoryFactory,
)
from fundamental.services.calibre_plugin_service.sources.git import (
    GitRepositoryZipSource,
)
from fundamental.services.calibre_plugin_service.sources.local import LocalZipSource

__all__ = [
    "DefaultTempDirectoryFactory",
    "GitRepositoryZipSource",
    "LocalZipSource",
    "PluginSource",
    "TempDirectoryFactory",
]
