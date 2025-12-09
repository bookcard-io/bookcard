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

"""Import service for read lists.

Orchestrates the import flow: parsing files, matching books, and
returning results for user review or automatic addition.
"""

import logging
from pathlib import Path

from fundamental.models.config import Library
from fundamental.services.readlist.book_matcher import BookMatcherService
from fundamental.services.readlist.comicrack_importer import ComicRackImporter
from fundamental.services.readlist.interfaces import (
    BookMatchResult,
    BookReference,
    ReadListData,
    ReadListImporter,
)

logger = logging.getLogger(__name__)


class ImportResult:
    """Result of a read list import operation.

    Attributes
    ----------
    total_books : int
        Total number of books in the read list.
    matched : list[BookMatchResult]
        Successfully matched books.
    unmatched : list[BookReference]
        Books that could not be matched.
    errors : list[str]
        List of error messages encountered during import.
    read_list_data : ReadListData | None
        Original parsed read list data.
    """

    def __init__(self) -> None:
        """Initialize import result."""
        self.total_books = 0
        self.matched: list[BookMatchResult] = []
        self.unmatched: list[BookReference] = []
        self.errors: list[str] = []
        self.read_list_data: ReadListData | None = None


class ReadListImportService:
    """Service for importing read lists from various formats.

    Orchestrates the import process:
    1. Select appropriate importer based on file format
    2. Parse file to ReadListData
    3. Match books using BookMatcherService
    4. Return results for user review or automatic addition
    """

    def __init__(self, library: Library) -> None:
        """Initialize import service.

        Parameters
        ----------
        library : Library
            Library configuration for accessing Calibre database.
        """
        self._library = library
        self._importers: dict[str, ReadListImporter] = {
            "comicrack": ComicRackImporter(),
        }
        self._matcher = BookMatcherService(library)

    def register_importer(self, name: str, importer: ReadListImporter) -> None:
        """Register a new importer.

        Parameters
        ----------
        name : str
            Importer name (e.g., "comicrack", "json").
        importer : ReadListImporter
            Importer instance.
        """
        self._importers[name] = importer

    def get_available_importers(self) -> list[str]:
        """Get list of available importer names.

        Returns
        -------
        list[str]
            List of importer names.
        """
        return list(self._importers.keys())

    def import_read_list(
        self,
        file_path: Path,
        importer_name: str = "comicrack",
    ) -> ImportResult:
        """Import a read list from a file.

        Parameters
        ----------
        file_path : Path
            Path to the read list file.
        importer_name : str
            Name of the importer to use (default: "comicrack").

        Returns
        -------
        ImportResult
            Import result with matched and unmatched books.

        Raises
        ------
        ValueError
            If importer not found or file cannot be parsed.
        """
        result = ImportResult()

        # Get importer
        if importer_name not in self._importers:
            msg = f"Importer '{importer_name}' not found. Available: {list(self._importers.keys())}"
            raise ValueError(msg)

        importer = self._importers[importer_name]

        # Verify file can be imported
        if not importer.can_import(file_path):
            msg = f"File {file_path} cannot be imported by {importer.get_format_name()}"
            raise ValueError(msg)

        # Parse file
        try:
            read_list_data = importer.parse(file_path)
            result.read_list_data = read_list_data
        except Exception as e:
            msg = f"Failed to parse file: {e}"
            logger.exception("Import parse error")
            raise ValueError(msg) from e

        result.total_books = len(read_list_data.books)

        # Match books
        try:
            match_results = self._matcher.match_books(
                read_list_data.books,
                library_id=0,  # Not used by matcher currently
            )
        except Exception as e:
            msg = f"Failed to match books: {e}"
            logger.exception("Book matching error")
            result.errors.append(msg)
            # Return partial results
            for ref in read_list_data.books:
                result.unmatched.append(ref)
            return result

        # Categorize results
        for match_result in match_results:
            if match_result.book_id is not None and match_result.confidence > 0.0:
                result.matched.append(match_result)
            else:
                result.unmatched.append(match_result.reference)

        return result
