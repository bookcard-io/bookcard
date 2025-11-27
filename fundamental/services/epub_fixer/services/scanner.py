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

"""EPUB scanner service.

Scans Calibre library for EPUB files following Single Responsibility Principle.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import func
from sqlmodel import select

if TYPE_CHECKING:
    from fundamental.models.config import Library
    from fundamental.models.core import Book
    from fundamental.models.media import Data

from fundamental.models.core import Book
from fundamental.models.media import Data
from fundamental.repositories.calibre_book_repository import CalibreBookRepository
from fundamental.services.epub_fixer.services.library import LibraryLocator


@dataclass
class EPUBFileInfo:
    """Information about an EPUB file in the library.

    Attributes
    ----------
    book_id : int
        Book ID from Calibre database.
    book_title : str
        Book title.
    file_path : Path
        Full path to EPUB file.
    """

    book_id: int
    book_title: str
    file_path: Path


class EPUBScanner:
    """Service for scanning Calibre library for EPUB files.

    Accepts dependencies via constructor (Inversion of Control).
    No hardcoded paths or database connections.

    Parameters
    ----------
    library : Library
        Library configuration.
    calibre_repo : CalibreBookRepository
        Calibre book repository for querying books.
    """

    def __init__(
        self,
        library: "Library",
        calibre_repo: CalibreBookRepository,
    ) -> None:
        """Initialize EPUB scanner.

        Parameters
        ----------
        library : Library
            Library configuration.
        calibre_repo : CalibreBookRepository
            Calibre book repository.
        """
        self._library = library
        self._calibre_repo = calibre_repo
        self._library_locator = LibraryLocator(library)

    def scan_epub_files(
        self,
        book_id: int | None = None,
    ) -> list[EPUBFileInfo]:
        """Scan library for EPUB files.

        Parameters
        ----------
        book_id : int | None
            Optional book ID to filter by.

        Returns
        -------
        list[EPUBFileInfo]
            List of EPUB file information.
        """
        library_path = self._library_locator.get_location()
        epub_files: list[EPUBFileInfo] = []

        with self._calibre_repo.get_session() as session:
            # Query for books with EPUB format
            stmt = (
                select(Book, Data)
                .join(Data, Book.id == Data.book)
                .where(func.upper(Data.format) == "EPUB")
            )

            if book_id is not None:
                stmt = stmt.where(Book.id == book_id)  # type: ignore[attr-defined]

            results = session.exec(stmt).all()

            for result in results:
                book: Book = result[0]  # type: ignore[index]
                data: Data = result[1]  # type: ignore[index]

                # Build file path
                book_path = library_path / book.path
                file_name = data.name or f"{book.id}"
                format_lower = data.format.lower()

                # Try pattern 1: {name}.{format}
                file_path = book_path / f"{file_name}.{format_lower}"
                if not file_path.exists():
                    # Try pattern 2: {book_id}.{format}
                    file_path = book_path / f"{book.id}.{format_lower}"

                if file_path.exists() and file_path.suffix.lower() == ".epub":
                    epub_files.append(
                        EPUBFileInfo(
                            book_id=book.id,
                            book_title=book.title,
                            file_path=file_path,
                        )
                    )

        return epub_files
