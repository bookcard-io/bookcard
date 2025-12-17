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

"""OPF file enforcement service.

Updates metadata.opf files in book directories with current metadata.
"""

import logging

from bookcard.models.config import Library
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.metadata_enforcement.library_path_resolver import (
    LibraryPathResolver,
)
from bookcard.services.opf_service import OpfService

logger = logging.getLogger(__name__)


class OpfEnforcementService:
    """Service for enforcing OPF metadata files.

    Updates metadata.opf files in book directories to reflect current
    database metadata. Follows SRP by focusing solely on OPF file updates.

    Parameters
    ----------
    library : Library
        Library configuration for path resolution.
    opf_service : OpfService | None
        OPF generation service. If None, creates a new instance.
    """

    def __init__(
        self,
        library: Library,
        opf_service: OpfService | None = None,
    ) -> None:
        """Initialize OPF enforcement service.

        Parameters
        ----------
        library : Library
            Library configuration.
        opf_service : OpfService | None
            OPF service instance. If None, creates a new instance.
        """
        self._library = library
        self._opf_service = opf_service or OpfService()
        self._path_resolver = LibraryPathResolver(library)

    def enforce_opf(self, book_with_rels: BookWithFullRelations) -> bool:
        """Enforce OPF metadata file for a book.

        Generates OPF XML from current book metadata and writes it to
        the book's directory as metadata.opf.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        bool
            True if OPF file was successfully updated, False otherwise.
        """
        try:
            # Generate OPF XML
            opf_result = self._opf_service.generate_opf(book_with_rels)

            # Get book directory path
            library_path = self._path_resolver.get_library_root()
            book_path = library_path / book_with_rels.book.path

            # Ensure book directory exists
            book_path.mkdir(parents=True, exist_ok=True)

            # Write OPF file
            opf_file_path = book_path / "metadata.opf"
            opf_file_path.write_text(opf_result.xml_content, encoding="utf-8")

            logger.info(
                "OPF file updated: book_id=%d, path=%s",
                book_with_rels.book.id,
                opf_file_path,
            )
        except OSError:
            logger.exception(
                "Failed to write OPF file for book_id=%d",
                book_with_rels.book.id,
            )
            return False
        except (ValueError, TypeError):
            logger.exception(
                "Unexpected error updating OPF file for book_id=%d",
                book_with_rels.book.id,
            )
            return False
        else:
            return True
