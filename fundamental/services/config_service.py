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

"""Configuration service.

Business logic for managing system configuration settings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fundamental.models.config import Library
from fundamental.repositories.calibre_book_repository import (
    CalibreBookRepository,
)
from fundamental.repositories.shelf_repository import ShelfRepository

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.repositories.config_repository import (
        LibraryRepository,
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
        session: Session,  # type: ignore[type-arg]
        library_repo: LibraryRepository,  # type: ignore[type-arg]
    ) -> None:
        self._session = session
        self._library_repo = library_repo

    def list_libraries(self) -> list[Library]:
        """List all libraries.

        Returns
        -------
        list[Library]
            All libraries.
        """
        return self._library_repo.list_all()

    def get_active_library(self) -> Library | None:
        """Get the currently active library.

        Returns
        -------
        Library | None
            The active library if one exists, None otherwise.
        """
        return self._library_repo.get_active()

    def get_library(self, library_id: int) -> Library | None:
        """Get a library by ID.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        Library | None
            Library if found, None otherwise.
        """
        return self._library_repo.get(library_id)

    def create_library(
        self,
        name: str,
        calibre_db_path: str,
        *,
        calibre_db_file: str = "metadata.db",
        use_split_library: bool = False,
        split_library_dir: str | None = None,
        auto_reconnect: bool = True,
        is_active: bool = False,
    ) -> Library:
        """Create a new library.

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
        is_active : bool
            Whether to set this as the active library (default: False).

        Returns
        -------
        Library
            Created library.

        Raises
        ------
        ValueError
            If a library with the same path already exists.
        """
        # Check if path already exists
        existing = self._library_repo.find_by_path(calibre_db_path)
        if existing is not None:
            msg = "library_path_already_exists"
            raise ValueError(msg)

        # If setting as active, deactivate all others
        if is_active:
            self._deactivate_all_libraries()

        library = Library(
            name=name,
            calibre_db_path=calibre_db_path,
            calibre_db_file=calibre_db_file,
            use_split_library=use_split_library,
            split_library_dir=split_library_dir,
            auto_reconnect=auto_reconnect,
            is_active=is_active,
        )
        self._library_repo.add(library)
        self._session.flush()
        # If library is created as active, sync any existing shelves (though unlikely)
        if is_active and library.id is not None:
            self._sync_shelves_for_library(library.id, True)
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
        is_active: bool | None = None,
    ) -> Library:
        """Update a library.

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
        is_active : bool | None
            Whether to set this as the active library.

        Returns
        -------
        Library
            Updated library.

        Raises
        ------
        ValueError
            If library not found or path conflict.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        self._validate_and_update_path(library, library_id, calibre_db_path)
        self._update_library_fields(
            library,
            name=name,
            calibre_db_file=calibre_db_file,
            calibre_uuid=calibre_uuid,
            use_split_library=use_split_library,
            split_library_dir=split_library_dir,
            auto_reconnect=auto_reconnect,
        )
        self._handle_active_status_change(library, is_active)

        self._session.flush()
        return library

    def _validate_and_update_path(
        self,
        library: Library,
        library_id: int,
        calibre_db_path: str | None,
    ) -> None:
        """Validate and update library path if provided.

        Parameters
        ----------
        library : Library
            Library to update.
        library_id : int
            Library identifier.
        calibre_db_path : str | None
            New path to set.

        Raises
        ------
        ValueError
            If path conflict exists.
        """
        if calibre_db_path is None:
            return

        if calibre_db_path == library.calibre_db_path:
            return

        existing = self._library_repo.find_by_path(calibre_db_path)
        if existing is not None and existing.id != library_id:
            msg = "library_path_already_exists"
            raise ValueError(msg)

        library.calibre_db_path = calibre_db_path

    def _update_library_fields(
        self,
        library: Library,
        *,
        name: str | None = None,
        calibre_db_file: str | None = None,
        calibre_uuid: str | None = None,
        use_split_library: bool | None = None,
        split_library_dir: str | None = None,
        auto_reconnect: bool | None = None,
    ) -> None:
        """Update library fields.

        Parameters
        ----------
        library : Library
            Library to update.
        name : str | None
            User-friendly library name.
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
        """
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

    def _handle_active_status_change(
        self,
        library: Library,
        is_active: bool | None,
    ) -> None:
        """Handle active status change for a library.

        Parameters
        ----------
        library : Library
            Library to update.
        is_active : bool | None
            Whether to set this as the active library.
        """
        if is_active is None:
            return

        if is_active and not library.is_active:
            self._deactivate_all_libraries()

        library.is_active = is_active

    def delete_library(self, library_id: int) -> None:
        """Delete a library.

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

    def set_active_library(self, library_id: int) -> Library:
        """Set a library as the active one.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        Library
            Updated library.

        Raises
        ------
        ValueError
            If library not found.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        # Deactivate all libraries first
        self._deactivate_all_libraries()

        # Activate the selected library
        library.is_active = True
        # Sync shelf statuses for the newly activated library
        self._sync_shelves_for_library(library_id, True)
        self._session.flush()
        return library

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

    def _deactivate_all_libraries(self) -> None:
        """Deactivate all libraries and sync shelf statuses."""
        libraries = self._library_repo.list_all()
        for lib in libraries:
            if lib.is_active:
                lib.is_active = False
                # Sync shelf statuses for this library
                if lib.id is not None:
                    self._sync_shelves_for_library(lib.id, False)
        self._session.flush()

    def _sync_shelves_for_library(
        self,
        library_id: int,
        is_active: bool,
    ) -> None:
        """Sync shelf active status with library active status.

        Parameters
        ----------
        library_id : int
            Library ID whose shelves should be synced.
        is_active : bool
            Active status to set for all shelves in the library.
        """
        shelf_repo = ShelfRepository(self._session)
        shelf_repo.sync_active_status_for_library(library_id, is_active)
