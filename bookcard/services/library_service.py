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

"""Library service.

Business logic for managing Calibre library configurations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.models.config import Library

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.repositories.library_repository import LibraryRepository
else:
    from bookcard.repositories.calibre_book_repository import (
        CalibreBookRepository,
    )


class LibraryService:
    """Operations for managing Calibre libraries.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    library_repo : LibraryRepository
        Repository for library persistence operations.
    """

    def __init__(
        self,
        session: Session,
        library_repo: LibraryRepository,
    ) -> None:
        self._session = session
        self._library_repo = library_repo

    def create_library(
        self,
        name: str,
        calibre_db_path: str,
        *,
        calibre_db_file: str = "metadata.db",
        use_split_library: bool = False,
        split_library_dir: str | None = None,
        auto_reconnect: bool = True,
    ) -> Library:
        """Create a new library configuration.

        Parameters
        ----------
        name : str
            User-friendly library name.
        calibre_db_path : str
            Path to Calibre database directory.
        calibre_db_file : str
            Calibre database filename (default: 'metadata.db').
        use_split_library : bool
            Whether to use split library mode (default: False).
        split_library_dir : str | None
            Directory for split library mode.
        auto_reconnect : bool
            Whether to automatically reconnect on errors (default: True).

        Returns
        -------
        Library
            Created library instance.

        Raises
        ------
        ValueError
            If a library with the same path already exists.
        """
        existing = self._library_repo.find_by_path(calibre_db_path)
        if existing is not None:
            msg = "library_path_already_exists"
            raise ValueError(msg)

        library = Library(
            name=name,
            calibre_db_path=calibre_db_path,
            calibre_db_file=calibre_db_file,
            use_split_library=use_split_library,
            split_library_dir=split_library_dir,
            auto_reconnect=auto_reconnect,
        )
        self._library_repo.add(library)
        self._session.flush()
        return library

    def update_library(
        self,
        library_id: int,
        *,
        name: str | None = None,
        calibre_db_path: str | None = None,
        calibre_db_file: str | None = None,
        calibre_uuid: str | None = None,
        use_split_library: bool | None = None,
        split_library_dir: str | None = None,
        auto_reconnect: bool | None = None,
    ) -> Library:
        """Update library configuration.

        Parameters
        ----------
        library_id : int
            Library identifier.
        name : str | None
            User-friendly library name.
        calibre_db_path : str | None
            Path to Calibre database directory.
        calibre_db_file : str | None
            Calibre database filename.
        calibre_uuid : str | None
            Calibre library UUID.
        use_split_library : bool | None
            Whether to use split library mode.
        split_library_dir : str | None
            Directory for split library mode.
        auto_reconnect : bool | None
            Whether to automatically reconnect on errors.

        Returns
        -------
        Library
            Updated library instance.

        Raises
        ------
        ValueError
            If library not found or path conflict exists.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        # Check for path conflict if path is being changed
        if calibre_db_path is not None and calibre_db_path != library.calibre_db_path:
            existing = self._library_repo.find_by_path(calibre_db_path)
            if existing is not None and existing.id != library_id:
                msg = "library_path_already_exists"
                raise ValueError(msg)
            library.calibre_db_path = calibre_db_path

        if name is not None:
            library.name = name
        if calibre_db_file is not None:
            library.calibre_db_file = calibre_db_file
        if calibre_uuid is not None:
            library.calibre_uuid = calibre_uuid
        if use_split_library is not None:
            library.use_split_library = use_split_library
        if split_library_dir is not None:
            library.split_library_dir = split_library_dir
        if auto_reconnect is not None:
            library.auto_reconnect = auto_reconnect

        self._session.flush()
        return library

    def delete_library(self, library_id: int) -> None:
        """Delete a library configuration.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Raises
        ------
        ValueError
            If library not found.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        self._library_repo.delete(library)

    def get_library_stats(self, library_id: int) -> dict[str, int | float]:
        """Get statistics for a library.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        dict[str, int | float]
            Dictionary with library statistics:
            - 'total_books': Total number of books
            - 'total_series': Total number of unique series
            - 'total_authors': Total number of unique authors
            - 'total_content_size': Total file size in bytes

        Raises
        ------
        ValueError
            If library not found.
        FileNotFoundError
            If Calibre database file does not exist.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        book_repo = CalibreBookRepository(
            calibre_db_path=library.calibre_db_path,
            calibre_db_file=library.calibre_db_file,
        )
        return book_repo.get_library_stats()
