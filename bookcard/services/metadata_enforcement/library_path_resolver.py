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

"""Library path resolver for metadata enforcement.

Resolves library and book directory paths for enforcement operations.
"""

from pathlib import Path

from bookcard.models.config import Library
from bookcard.services.epub_fixer.services.library import LibraryLocator


class LibraryPathResolver:
    """Service for resolving library and book paths.

    Follows SRP by handling only path resolution logic.
    Uses IOC by accepting Library configuration.

    Parameters
    ----------
    library : Library
        Library configuration object.
    """

    def __init__(self, library: Library) -> None:
        """Initialize library path resolver.

        Parameters
        ----------
        library : Library
            Library configuration.
        """
        self._library = library
        self._locator = LibraryLocator(library)

    def get_library_root(self) -> Path:
        """Get library root directory path.

        Returns
        -------
        Path
            Path to library root directory.
        """
        return self._locator.get_location()

    def get_book_directory(self, book_path: str) -> Path:
        """Get book directory path.

        Parameters
        ----------
        book_path : str
            Book path from Calibre database (relative to library root).

        Returns
        -------
        Path
            Path to book directory.
        """
        library_root = self.get_library_root()
        return library_root / book_path
