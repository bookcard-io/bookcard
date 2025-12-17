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

"""Helper functions for author services.

Extracts repeated patterns following DRY principle.
"""

from bookcard.models.config import Library
from bookcard.services.author_exceptions import NoActiveLibraryError
from bookcard.services.config_service import LibraryService


def ensure_active_library(library_service: LibraryService) -> Library:
    """Get active library or raise NoActiveLibraryError.

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.

    Returns
    -------
    Library
        Active library object.

    Raises
    ------
    NoActiveLibraryError
        If no active library is found.
    """
    active_library = library_service.get_active_library()
    if not active_library or active_library.id is None:
        msg = "No active library found"
        raise NoActiveLibraryError(msg)
    return active_library
