# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Library service.

Business logic for managing Calibre library configurations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fundamental.models.config import Library

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.repositories.library_repository import LibraryRepository


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

    def create_library(
        self,
        name: str,
        calibre_db_path: str,
        *,
        calibre_db_file: str = "metadata.db",
        use_split_library: bool = False,
        split_library_dir: str | None = None,
        auto_reconnect: bool = True,
        set_as_active: bool = False,
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
        set_as_active : bool
            Whether to set this library as active (default: False).
            If True, deactivates all other libraries.

        Returns
        -------
        Library
            Created library instance.

        Raises
        ------
        ValueError
            If a library with the same path already exists.
        """
        # Check for duplicate path
        existing = self._library_repo.find_by_path(calibre_db_path)
        if existing is not None:
            msg = "library_path_already_exists"
            raise ValueError(msg)

        # If setting as active, deactivate all others
        if set_as_active:
            self._deactivate_all()

        library = Library(
            name=name,
            calibre_db_path=calibre_db_path,
            calibre_db_file=calibre_db_file,
            use_split_library=use_split_library,
            split_library_dir=split_library_dir,
            auto_reconnect=auto_reconnect,
            is_active=set_as_active,
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

    def set_active_library(self, library_id: int) -> Library:
        """Set a library as the active library.

        Deactivates all other libraries and activates the specified one.

        Parameters
        ----------
        library_id : int
            Library identifier to activate.

        Returns
        -------
        Library
            Activated library instance.

        Raises
        ------
        ValueError
            If library not found.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        self._deactivate_all()
        library.is_active = True
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

    def _deactivate_all(self) -> None:
        """Deactivate all libraries."""
        from sqlmodel import select

        stmt = select(Library).where(Library.is_active == True)  # noqa: E712
        active_libraries = self._session.exec(stmt).all()
        for lib in active_libraries:
            lib.is_active = False
