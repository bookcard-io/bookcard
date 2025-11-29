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
Uses ebook-polish to properly embed metadata at the book level.
"""

import logging
import shutil
import subprocess  # noqa: S404
from pathlib import Path

from lxml import etree  # type: ignore[attr-defined]

from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.epub_fixer.core.epub import EPUBReader, EPUBWriter
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

    Uses ebook-polish to embed metadata from OPF file into EPUB files
    at the book level. This ensures metadata is properly embedded for
    device compatibility (Kindle, etc.).

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

        Uses ebook-polish to embed metadata from OPF file into EPUB.
        This ensures metadata is properly embedded at the book level
        for device compatibility.

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

        # Get ebook-polish binary path
        polish_path = self._get_ebook_polish_path()
        if polish_path is None:
            logger.warning(
                "ebook-polish not found, falling back to manual OPF update: book_id=%d",
                book.id,
            )
            return self._enforce_metadata_manual(book_with_rels, file_path)

        # Generate OPF metadata
        opf_result = self._opf_service.generate_opf(book_with_rels)

        # Get book directory path to find metadata.opf
        book_dir = file_path.parent
        opf_file_path = book_dir / "metadata.opf"

        # Ensure OPF file exists (should have been created by OpfEnforcementService)
        if not opf_file_path.exists():
            # Write OPF file if it doesn't exist
            opf_file_path.write_text(opf_result.xml_content, encoding="utf-8")

        # Use ebook-polish to embed metadata from OPF file
        try:
            success = self._run_ebook_polish_metadata(
                polish_path, opf_file_path, file_path
            )
            if success:
                logger.info(
                    "EPUB metadata embedded: book_id=%d, path=%s",
                    book.id,
                    file_path,
                )
        except Exception:
            logger.exception(
                "Failed to embed EPUB metadata with ebook-polish, falling back to manual: book_id=%d, path=%s",
                book.id,
                file_path,
            )
            return self._enforce_metadata_manual(book_with_rels, file_path)
        else:
            return success

    def _get_ebook_polish_path(self) -> str | None:
        """Get path to Calibre ebook-polish binary.

        Returns
        -------
        str | None
            Path to ebook-polish if found, None otherwise.
        """
        # Check Docker installation path first
        docker_path = Path("/app/calibre/ebook-polish")
        if docker_path.exists():
            return str(docker_path)

        # Fallback to PATH lookup
        polish = shutil.which("ebook-polish")
        if polish:
            return polish

        return None

    def _run_ebook_polish_metadata(
        self, polish_path: str, opf_path: Path, ebook_path: Path
    ) -> bool:
        """Run ebook-polish to embed metadata from OPF file into ebook.

        Parameters
        ----------
        polish_path : str
            Path to ebook-polish binary.
        opf_path : Path
            Path to OPF metadata file.
        ebook_path : Path
            Path to ebook file to update.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        try:
            # ebook-polish -o metadata.opf -U file.epub file.epub
            # -o: OPF metadata file path
            # -U: update file in place
            cmd = [
                polish_path,
                "-o",
                str(opf_path),
                "-U",
                str(ebook_path),
                str(ebook_path),
            ]

            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                return True

            logger.warning(
                "ebook-polish failed: path=%s, returncode=%d, stderr=%s",
                ebook_path,
                result.returncode,
                result.stderr[:500] if result.stderr else "",
            )
        except subprocess.TimeoutExpired:
            logger.exception(
                "ebook-polish timed out after 5 minutes: path=%s",
                ebook_path,
            )
            return False
        except Exception:
            logger.exception(
                "Error running ebook-polish: path=%s",
                ebook_path,
            )
            return False
        else:
            return False

    def _enforce_metadata_manual(
        self,
        book_with_rels: BookWithFullRelations,
        file_path: Path,
    ) -> bool:
        """Fallback: manually update OPF metadata inside EPUB.

        Used when ebook-polish is not available. This method manually
        edits the OPF file inside the EPUB ZIP archive.

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
                    "EPUB metadata updated manually: book_id=%d, path=%s",
                    book_with_rels.book.id,
                    file_path,
                )
                return True

            logger.warning(
                "Could not find metadata element in OPF: book_id=%d, path=%s",
                book_with_rels.book.id,
                file_path,
            )
        except Exception:
            logger.exception(
                "Failed to enforce EPUB metadata manually: book_id=%d, path=%s",
                book_with_rels.book.id,
                file_path,
            )
            return False
        else:
            return False
