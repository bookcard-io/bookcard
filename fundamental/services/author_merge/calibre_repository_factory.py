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

"""Factory for creating Calibre repository instances.

Follows DIP by providing a centralized way to create Calibre repositories,
allowing for dependency injection and easier testing.
"""

import logging

from fundamental.models.config import Library
from fundamental.repositories.calibre_book_repository import CalibreBookRepository

logger = logging.getLogger(__name__)


class CalibreRepositoryFactory:
    """Factory for creating CalibreBookRepository instances.

    Centralizes the creation logic to follow DRY principles and
    makes it easier to inject dependencies for testing.
    """

    @staticmethod
    def create(library: Library | None) -> CalibreBookRepository | None:
        """Create a CalibreBookRepository for the given library.

        Parameters
        ----------
        library : Library
            Library configuration.

        Returns
        -------
        CalibreBookRepository | None
            Repository instance if library has valid Calibre path, None otherwise.
        """
        if not library or not library.calibre_db_path:
            logger.error(
                "Cannot create Calibre repository: library missing database path"
            )
            return None

        return CalibreBookRepository(
            calibre_db_path=library.calibre_db_path,
            calibre_db_file=library.calibre_db_file,
        )
