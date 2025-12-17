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

"""Book repository protocol and adapter for conversion operations.

Provides an abstraction layer for accessing book data from Calibre database,
following DIP by depending on abstractions rather than concrete implementations.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from bookcard.models.core import Book
from bookcard.models.media import Data

if TYPE_CHECKING:
    from bookcard.repositories import CalibreBookRepository


class BookRepository(Protocol):
    """Abstract interface for book data access.

    This protocol defines the interface for accessing book data,
    allowing different implementations to be used interchangeably.
    """

    def get_book(self, book_id: int) -> Book:
        """Get book from Calibre database.

        Parameters
        ----------
        book_id : int
            Book ID.

        Returns
        -------
        Book
            Book record.

        Raises
        ------
        BookNotFoundError
            If book not found.
        """
        ...

    def get_format_data(self, book_id: int, format_name: str) -> Data | None:
        """Get format data for a book.

        Parameters
        ----------
        book_id : int
            Book ID.
        format_name : str
            Format in uppercase.

        Returns
        -------
        Data | None
            Format data if found, None otherwise.
        """
        ...

    def format_exists(self, book_id: int, format_name: str) -> bool:
        """Check if a format exists for a book.

        Parameters
        ----------
        book_id : int
            Book ID.
        format_name : str
            Format in uppercase.

        Returns
        -------
        bool
            True if format exists, False otherwise.
        """
        ...

    def get_book_file_path(
        self, book: Book, book_id: int, format_name: str, library_root: Path
    ) -> Path | None:
        """Get file path for a book format.

        Parameters
        ----------
        book : Book
            Book record.
        book_id : int
            Book ID.
        format_name : str
            Format in uppercase.
        library_root : Path
            Library root path.

        Returns
        -------
        Path | None
            File path if found, None otherwise.
        """
        ...

    def add_format_to_calibre(
        self, book_id: int, file_path: Path, format_name: str
    ) -> None:
        """Add format to Calibre database.

        Parameters
        ----------
        book_id : int
            Book ID.
        file_path : Path
            Path to file.
        format_name : str
            Format in uppercase.
        """
        ...


class CalibreBookRepositoryAdapter:
    """Adapter for CalibreBookRepository to implement BookRepository protocol.

    Adapts the existing CalibreBookRepository to the BookRepository protocol,
    providing a clean interface for conversion operations.

    Parameters
    ----------
    calibre_repo : CalibreBookRepository
        Calibre book repository instance.
    """

    def __init__(self, calibre_repo: "CalibreBookRepository") -> None:
        """Initialize adapter.

        Parameters
        ----------
        calibre_repo : CalibreBookRepository
            Calibre book repository instance.
        """
        self._calibre_repo = calibre_repo

    def get_book(self, book_id: int) -> Book:
        """Get book from Calibre database.

        Parameters
        ----------
        book_id : int
            Book ID.

        Returns
        -------
        Book
            Book record.

        Raises
        ------
        BookNotFoundError
            If book not found.
        """
        from sqlmodel import select

        from bookcard.services.conversion.exceptions import (
            BookNotFoundError,
        )

        with self._calibre_repo.get_session() as session:
            stmt = select(Book).where(Book.id == book_id)
            book = session.exec(stmt).first()
            if book is None:
                raise BookNotFoundError(book_id)
            return book

    def get_format_data(self, book_id: int, format_name: str) -> Data | None:
        """Get format data for a book.

        Parameters
        ----------
        book_id : int
            Book ID.
        format_name : str
            Format in uppercase.

        Returns
        -------
        Data | None
            Format data if found, None otherwise.
        """
        from sqlmodel import select

        with self._calibre_repo.get_session() as session:
            stmt = (
                select(Data)
                .where(Data.book == book_id)
                .where(Data.format == format_name.upper())
            )
            return session.exec(stmt).first()

    def format_exists(self, book_id: int, format_name: str) -> bool:
        """Check if a format exists for a book.

        Parameters
        ----------
        book_id : int
            Book ID.
        format_name : str
            Format in uppercase.

        Returns
        -------
        bool
            True if format exists, False otherwise.
        """
        return self.get_format_data(book_id, format_name) is not None

    def get_book_file_path(
        self, book: Book, book_id: int, format_name: str, library_root: Path
    ) -> Path | None:
        """Get file path for a book format.

        Parameters
        ----------
        book : Book
            Book record.
        book_id : int
            Book ID.
        format_name : str
            Format in uppercase.
        library_root : Path
            Library root path.

        Returns
        -------
        Path | None
            File path if found, None otherwise.
        """
        book_dir = library_root / book.path

        # Get format data to determine filename
        data = self.get_format_data(book_id, format_name)
        if data is None:
            return None

        file_name = data.name or str(book_id)
        # Primary path: {name}.{format}
        primary = book_dir / f"{file_name}.{format_name.lower()}"
        if primary.exists():
            return primary

        # Alternative path: {book_id}.{format}
        alt = book_dir / f"{book_id}.{format_name.lower()}"
        if alt.exists():
            return alt

        return None

    def add_format_to_calibre(
        self, book_id: int, file_path: Path, format_name: str
    ) -> None:
        """Add format to Calibre database.

        Parameters
        ----------
        book_id : int
            Book ID.
        file_path : Path
            Path to file.
        format_name : str
            Format in uppercase.
        """
        from sqlmodel import select

        file_size = file_path.stat().st_size
        file_name = file_path.stem

        with self._calibre_repo.get_session() as session:
            # Check if format already exists
            stmt = (
                select(Data)
                .where(Data.book == book_id)
                .where(Data.format == format_name.upper())
            )
            existing = session.exec(stmt).first()

            if existing:
                # Update existing record
                existing.uncompressed_size = file_size
                existing.name = file_name
                session.add(existing)
            else:
                # Create new Data record
                data = Data(
                    book=book_id,
                    format=format_name.upper(),
                    uncompressed_size=file_size,
                    name=file_name,
                )
                session.add(data)

            session.commit()
