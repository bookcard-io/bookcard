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

"""EPUB metadata enforcer.

Updates OPF metadata inside EPUB files to match current database metadata.
Uses in-archive modification to embed metadata and cover images.
"""

import logging
from pathlib import Path

from lxml import etree  # type: ignore[attr-defined]

from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.epub_fixer.core.epub import EPUBContents, EPUBReader, EPUBWriter
from bookcard.services.epub_fixer.utils.opf_locator import OPFLocator
from bookcard.services.metadata_enforcement.ebook_enforcer import (
    EbookMetadataEnforcer,
)
from bookcard.services.metadata_enforcement.epub_cover_embedder import EpubCoverEmbedder
from bookcard.services.opf_service import OpfService

logger = logging.getLogger(__name__)

# OPF namespaces
NS_OPF = "http://www.idpf.org/2007/opf"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"


class EpubMetadataEnforcer(EbookMetadataEnforcer):
    """Enforcer for EPUB file metadata.

    Embeds metadata and cover images directly into EPUB files by
    modifying the OPF and updating archive contents.

    Parameters
    ----------
    opf_service : OpfService | None
        OPF generation service. If None, creates a new instance.
    """

    def __init__(self, opf_service: OpfService | None = None) -> None:
        """Initialize EPUB metadata enforcer.

        Parameters
        ----------
        opf_service : OpfService | None
            OPF service instance. If None, creates a new instance.
        """
        super().__init__(supported_formats=["epub"])
        self._opf_service = opf_service or OpfService()
        self._reader = EPUBReader()
        self._writer = EPUBWriter()
        self._opf_locator = OPFLocator()
        self._cover_embedder = EpubCoverEmbedder()

    def enforce_metadata(
        self,
        book_with_rels: BookWithFullRelations,
        file_path: Path,
    ) -> bool:
        """Enforce metadata in EPUB file.

        Updates embedded metadata in the ebook file to match current
        database metadata. Also embeds cover image if present.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.
        file_path : Path
            Path to EPUB file.

        Returns
        -------
        bool
            True if metadata was successfully updated, False otherwise.

        Raises
        ------
        FileNotFoundError
            If EPUB file does not exist.
        ValueError
            If EPUB is invalid or OPF cannot be updated.
        """
        book = book_with_rels.book
        if book.id is None:
            logger.warning("Book ID is None, cannot enforce EPUB metadata")
            return False

        try:
            # Read EPUB contents
            contents = self._reader.read(file_path)

            # Find OPF file in EPUB
            opf_path = self._opf_locator.find_opf_path(contents.files)
            if opf_path is None:
                logger.warning(
                    "No OPF file found in EPUB: book_id=%d, path=%s",
                    book.id,
                    file_path,
                )
                return False

            # Generate new OPF metadata
            opf_result = self._opf_service.generate_opf(book_with_rels)

            # Update OPF content
            if not self._update_opf_content(contents, opf_path, opf_result.xml_content):
                logger.warning(
                    "Failed to update OPF content: book_id=%d, path=%s",
                    book.id,
                    file_path,
                )
                return False

            # Embed cover if available
            # Check for cover.jpg in book directory
            cover_path = file_path.parent / "cover.jpg"
            if cover_path.exists():
                self._cover_embedder.embed_cover(
                    contents, cover_path, opf_path=opf_path
                )

            # Write EPUB back
            self._writer.write(contents, file_path)

            logger.info(
                "EPUB metadata embedded: book_id=%d, path=%s",
                book.id,
                file_path,
            )
        except Exception:
            logger.exception(
                "Failed to enforce EPUB metadata: book_id=%d, path=%s",
                book.id,
                file_path,
            )
            return False
        else:
            return True

    def _update_opf_content(
        self, contents: EPUBContents, opf_path: str, new_opf_xml: str
    ) -> bool:
        """Update OPF content in EPUB contents.

        Replaces metadata section while preserving manifest and spine.
        """
        try:
            existing_opf_content = contents.files.get(opf_path)
            if existing_opf_content is None:
                return False

            # Parse existing OPF
            existing_opf_root = etree.fromstring(existing_opf_content.encode("utf-8"))

            # Parse new OPF metadata
            new_opf_root = etree.fromstring(new_opf_xml.encode("utf-8"))

            # Replace metadata section
            existing_metadata = existing_opf_root.find(
                "metadata",
                namespaces={
                    None: NS_OPF,
                    "dc": NS_DC,
                    "dcterms": NS_DCTERMS,
                },
            )
            new_metadata = new_opf_root.find(
                "metadata",
                namespaces={
                    None: NS_OPF,
                    "dc": NS_DC,
                    "dcterms": NS_DCTERMS,
                },
            )

            if existing_metadata is None or new_metadata is None:
                logger.warning("Failed to find metadata in OPF")
                return False

            existing_opf_root.remove(existing_metadata)
            existing_opf_root.insert(0, new_metadata)
            # Update OPF content in EPUB
            updated_opf_content = etree.tostring(
                existing_opf_root,
                encoding="utf-8",
                xml_declaration=True,
                pretty_print=True,
            ).decode("utf-8")
            contents.files[opf_path] = updated_opf_content
        except Exception:
            logger.exception("Error updating OPF content")
            return False
        else:
            return True
