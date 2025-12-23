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

"""Factory for creating PVR indexers and download clients from database definitions.

This package provides factory functions for creating indexers and download clients,
following SRP by separating concerns into focused modules.
"""

# Import to trigger registration
from bookcard.pvr.factory import (  # noqa: F401
    download_client_registry_init,
    settings_factories,
)
from bookcard.pvr.factory.download_client_factory import create_download_client
from bookcard.pvr.factory.indexer_factory import create_indexer

__all__ = [
    "create_download_client",
    "create_indexer",
]
