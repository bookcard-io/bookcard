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

"""Registry modules for PVR system.

This package contains registry modules following SRP by separating
registration concerns from factory and settings concerns.
"""

from bookcard.pvr.registries.download_client_registry import (
    get_registered_download_client_types,
    register_download_client,
)
from bookcard.pvr.registries.indexer_registry import (
    get_registered_indexer_types,
    register_indexer,
)

__all__ = [
    "get_registered_download_client_types",
    "get_registered_indexer_types",
    "register_download_client",
    "register_indexer",
]
