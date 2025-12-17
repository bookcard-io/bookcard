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

"""Library location service.

Handles library path resolution following Single Responsibility Principle.
Accepts dependencies via constructor (Inversion of Control).
"""

from pathlib import Path

from bookcard.models.config import Library


class LibraryLocator:
    """Service for locating Calibre library directory.

    Accepts library configuration via dependency injection.
    No hardcoded paths or database connections.

    Parameters
    ----------
    library : Library
        Library configuration object.
    """

    def __init__(self, library: Library) -> None:
        """Initialize library locator.

        Parameters
        ----------
        library : Library
            Library configuration object.
        """
        self._library = library

    def get_location(self) -> Path:
        """Get library root directory path.

        Returns
        -------
        Path
            Path to library root directory.

        Raises
        ------
        ValueError
            If library configuration is invalid.
        """
        # Use library_root if provided
        if self._library.library_root:
            return Path(self._library.library_root)

        # Use split_library_dir if split library mode is enabled
        if self._library.use_split_library and self._library.split_library_dir:
            return Path(self._library.split_library_dir)

        # Default: derive from calibre_db_path
        library_db_path = Path(self._library.calibre_db_path)
        if library_db_path.is_dir():
            return library_db_path

        # If calibre_db_path is a file, use parent directory
        return library_db_path.parent
