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
"""

import logging
from pathlib import Path

from lxml import etree  # type: ignore[attr-defined]

from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.epub_fixer.core.epub import (
    EPUBReader,
    EPUBWriter,
)
from fundamental.services.epub_fixer.utils.opf_locator import OPFLocator
from fundamental.services.metadata_enforcement.ebook_enforcer import (
    EbookMetadataEnforcer,
)
from fundamental.services.opf_service import OpfService

logger = logging.getLogger(__name__)

# OPF namespaces
NS_OPF = "http://www.idpf.org/2007/opf"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"


class EpubMetadataEnforcer(EbookMetadataEnforcer):
    """Enforcer for EPUB file metadata.

    Updates OPF metadata inside EPUB ZIP files to match current
    database metadata. Preserves all other EPUB contents.

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

    def enforce_metadata(
        self,
        book_with_rels: BookWithFullRelations,
        file_path: Path,
    ) -> bool:
        """Enforce metadata in EPUB file.

        Reads EPUB, updates OPF metadata, and writes back.

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
        try:
            # Read EPUB contents
            contents = self._reader.read(file_path)

            # Find OPF file in EPUB
            opf_path = self._opf_locator.find_opf_path(contents.files)
            if opf_path is None:
                logger.warning(
                    "No OPF file found in EPUB: book_id=%d, path=%s",
                    book_with_rels.book.id,
                    file_path,
                )
                return False

            # Generate new OPF metadata
            opf_result = self._opf_service.generate_opf(book_with_rels)

            # Parse existing OPF to preserve structure (manifest, spine, etc.)
            existing_opf_content = contents.files.get(opf_path)
            if existing_opf_content is None:
                logger.warning(
                    "OPF file not found in EPUB contents: book_id=%d, path=%s",
                    book_with_rels.book.id,
                    file_path,
                )
                return False

            # Parse existing OPF to extract manifest and spine
            existing_opf_root = etree.fromstring(existing_opf_content.encode("utf-8"))

            # Parse new OPF metadata
            new_opf_root = etree.fromstring(opf_result.xml_content.encode("utf-8"))

            # Replace metadata section while preserving manifest and spine
            # Find metadata element in existing OPF
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

            if existing_metadata is not None and new_metadata is not None:
                # Replace metadata element
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

                # Write EPUB back
                self._writer.write(contents, file_path)

                logger.info(
                    "EPUB metadata updated: book_id=%d, path=%s",
                    book_with_rels.book.id,
                    file_path,
                )
                return True
            logger.warning(
                "Could not find metadata element in OPF: book_id=%d, path=%s",
                book_with_rels.book.id,
                file_path,
            )
        except FileNotFoundError:
            raise
        except (ValueError, TypeError, OSError):
            logger.exception(
                "Failed to enforce EPUB metadata: book_id=%d, path=%s",
                book_with_rels.book.id,
                file_path,
            )
            return False
        except etree.XMLSyntaxError:
            logger.exception(
                "Invalid XML in EPUB OPF: book_id=%d, path=%s",
                book_with_rels.book.id,
                file_path,
            )
            return False
        else:
            return False
