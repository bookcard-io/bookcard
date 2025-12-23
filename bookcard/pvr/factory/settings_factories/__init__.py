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

"""Settings factories for PVR system.

This package contains settings factory modules, following SRP by separating
settings creation from factory logic.
"""

# Import to trigger registration
from bookcard.pvr.factory.settings_factories import (  # noqa: F401
    download_client_settings,
    indexer_settings,
)

__all__ = []
