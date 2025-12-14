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

"""Calibre plugin management service.

This package is intentionally split into small modules to keep responsibilities
focused and make the service easy to test via dependency injection.
"""

from fundamental.services.calibre_plugin_service.exceptions import (
    CalibreCommandError,
    CalibreNotFoundError,
    PluginSourceError,
)
from fundamental.services.calibre_plugin_service.models import PluginInfo
from fundamental.services.calibre_plugin_service.service import (
    CalibrePluginService,
    create_default_calibre_plugin_service,
)

__all__ = [
    "CalibreCommandError",
    "CalibreNotFoundError",
    "CalibrePluginService",
    "PluginInfo",
    "PluginSourceError",
    "create_default_calibre_plugin_service",
]
