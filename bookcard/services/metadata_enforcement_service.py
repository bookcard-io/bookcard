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

"""Metadata enforcement service.

Orchestrates automatic enforcement of metadata and cover changes to ebook files.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from bookcard.models.config import Library
from bookcard.models.media import Data
from bookcard.models.metadata_enforcement import (
    EnforcementStatus,
    MetadataEnforcementOperation,
)
from bookcard.repositories.metadata_enforcement_repository import (
    MetadataEnforcementRepository,
)
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.metadata_enforcement.cover_enforcer import (
    CoverEnforcementService,
)
from bookcard.services.metadata_enforcement.ebook_enforcer import (
    EbookMetadataEnforcer,
)
from bookcard.services.metadata_enforcement.epub_enforcer import (
    EpubMetadataEnforcer,
)
from bookcard.services.metadata_enforcement.library_path_resolver import (
    LibraryPathResolver,
)
from bookcard.services.metadata_enforcement.opf_enforcer import (
    OpfEnforcementService,
)

logger = logging.getLogger(__name__)


@dataclass
class MetadataEnforcementResult:
    """Result of metadata enforcement operation.

    Attributes
    ----------
    success : bool
        True if enforcement completed successfully.
    opf_updated : bool
        True if OPF file was updated.
    cover_updated : bool
        True if cover file was updated.
    ebook_files_updated : bool
        True if ebook files were updated.
    supported_formats : list[str]
        List of formats that were processed.
    error_message : str | None
        Error message if enforcement failed.
    """

    success: bool
    opf_updated: bool
    cover_updated: bool
    ebook_files_updated: bool
    supported_formats: list[str]
    error_message: str | None = None


class MetadataEnforcementService:
    """Service for enforcing metadata and cover changes to ebook files.

    Orchestrates OPF, cover, and ebook file updates. Follows SRP by
    coordinating enforcement operations without implementing them directly.

    Parameters
    ----------
    session : Session
        Database session for tracking operations.
    library : Library
        Library configuration.
    opf_enforcer : OpfEnforcementService | None
        OPF enforcement service. If None, creates a new instance.
    cover_enforcer : CoverEnforcementService | None
        Cover enforcement service. If None, creates a new instance.
    ebook_enforcers : list[EbookMetadataEnforcer] | None
        List of ebook format enforcers. If None, creates default set.
    repository : MetadataEnforcementRepository | None
        Repository for tracking operations. If None, creates a new instance.
    """

    def __init__(
        self,
        session: Session,
        library: Library,
        opf_enforcer: OpfEnforcementService | None = None,
        cover_enforcer: CoverEnforcementService | None = None,
        ebook_enforcers: list[EbookMetadataEnforcer] | None = None,
        repository: MetadataEnforcementRepository | None = None,
    ) -> None:
        """Initialize metadata enforcement service.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration.
        opf_enforcer : OpfEnforcementService | None
            OPF enforcement service.
        cover_enforcer : CoverEnforcementService | None
            Cover enforcement service.
        ebook_enforcers : list[EbookMetadataEnforcer] | None
            Ebook format enforcers.
        repository : MetadataEnforcementRepository | None
            Repository for tracking.
        """
        self._session = session
        self._library = library
        self._opf_enforcer = opf_enforcer or OpfEnforcementService(library)
        self._cover_enforcer = cover_enforcer or CoverEnforcementService(library)
        self._ebook_enforcers = ebook_enforcers or [EpubMetadataEnforcer()]
        self._repository = repository or MetadataEnforcementRepository(session)
        self._path_resolver = LibraryPathResolver(library)

    def enforce_metadata(
        self,
        book_id: int,
        book_with_rels: BookWithFullRelations,
        user_id: int | None = None,
    ) -> MetadataEnforcementResult:
        """Enforce metadata and cover for a book.

        Updates OPF files, cover images, and embedded metadata in ebook files
        to match current database metadata.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        book_with_rels : BookWithFullRelations
            Book with all related metadata.
        user_id : int | None
            User ID who triggered the update (optional).

        Returns
        -------
        MetadataEnforcementResult
            Result of enforcement operation.
        """
        # Create tracking record
        operation = MetadataEnforcementOperation(
            book_id=book_id,
            library_id=self._library.id,
            user_id=user_id,
            status=EnforcementStatus.IN_PROGRESS,
        )
        self._repository.add(operation)
        self._session.flush()

        try:
            # Enforce OPF file
            opf_updated = self._opf_enforcer.enforce_opf(book_with_rels)

            # Enforce cover file
            cover_updated = self._cover_enforcer.enforce_cover(book_with_rels)

            # Enforce ebook files
            ebook_files_updated, supported_formats = self._enforce_ebook_files(
                book_with_rels
            )

            # Update tracking record
            operation.status = EnforcementStatus.COMPLETED
            operation.enforced_at = datetime.now(UTC)
            operation.opf_updated = opf_updated
            operation.cover_updated = cover_updated
            operation.ebook_files_updated = ebook_files_updated
            operation.supported_formats = supported_formats
            self._session.commit()

            logger.info(
                "Metadata enforcement completed: book_id=%d, opf=%s, cover=%s, ebooks=%s",
                book_id,
                opf_updated,
                cover_updated,
                ebook_files_updated,
            )

            return MetadataEnforcementResult(
                success=True,
                opf_updated=opf_updated,
                cover_updated=cover_updated,
                ebook_files_updated=ebook_files_updated,
                supported_formats=supported_formats,
            )
        except Exception as e:
            # Update tracking record with error
            error_message = str(e)
            operation.status = EnforcementStatus.FAILED
            operation.enforced_at = datetime.now(UTC)
            operation.error_message = error_message
            self._session.commit()

            logger.exception(
                "Metadata enforcement failed: book_id=%d, error=%s",
                book_id,
                error_message,
            )

            return MetadataEnforcementResult(
                success=False,
                opf_updated=False,
                cover_updated=False,
                ebook_files_updated=False,
                supported_formats=[],
                error_message=error_message,
            )

    def _enforce_ebook_files(
        self, book_with_rels: BookWithFullRelations
    ) -> tuple[bool, list[str]]:
        """Enforce metadata in ebook files.

        Finds all supported ebook files for the book and updates their
        embedded metadata.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        tuple[bool, list[str]]
            Tuple of (success flag, list of processed formats).
        """
        book = book_with_rels.book
        library_path = self._path_resolver.get_library_root()
        book_dir = library_path / book.path

        if not book_dir.exists():
            logger.warning(
                "Book directory does not exist: book_id=%d, path=%s",
                book.id,
                book_dir,
            )
            return False, []

        # Get book formats from database
        # Use Calibre repository session to query Data table
        from bookcard.repositories.calibre_book_repository import (
            CalibreBookRepository,
        )

        book_repo = CalibreBookRepository(
            calibre_db_path=self._library.calibre_db_path,
            calibre_db_file=self._library.calibre_db_file,
        )

        with book_repo.get_session() as calibre_session:
            data_stmt = select(Data).where(Data.book == book.id)
            data_records = list(calibre_session.exec(data_stmt).all())

        supported_formats: list[str] = []
        any_updated = False

        for data_record in data_records:
            format_lower = data_record.format.lower()

            # Find enforcer for this format
            enforcer = None
            for e in self._ebook_enforcers:
                if e.can_handle(format_lower):
                    enforcer = e
                    break

            if enforcer is None:
                logger.debug(
                    "No enforcer available for format: book_id=%d, format=%s",
                    book.id,
                    format_lower,
                )
                continue

            # Find ebook file
            if book.id is None:
                logger.warning(
                    "Book ID is None, skipping ebook enforcement: format=%s",
                    format_lower,
                )
                continue
            file_path = self._find_ebook_file(book_dir, book.id, data_record)
            if file_path is None:
                logger.warning(
                    "Ebook file not found: book_id=%d, format=%s",
                    book.id,
                    format_lower,
                )
                continue

            # Enforce metadata
            try:
                updated = enforcer.enforce_metadata(book_with_rels, file_path)
                if updated:
                    any_updated = True
                    supported_formats.append(format_lower)
                    logger.info(
                        "Ebook metadata enforced: book_id=%d, format=%s, path=%s",
                        book.id,
                        format_lower,
                        file_path,
                    )
            except Exception as e:
                logger.exception(
                    "Failed to enforce ebook metadata: book_id=%d, format=%s",
                    book.id,
                    format_lower,
                )

        return any_updated, supported_formats

    def _find_ebook_file(
        self, book_dir: Path, book_id: int, data_record: Data
    ) -> Path | None:
        """Find ebook file path.

        Parameters
        ----------
        book_dir : Path
            Book directory path.
        book_id : int
            Book ID.
        data_record : Data
            Data record for the format.

        Returns
        -------
        Path | None
            Path to ebook file if found, None otherwise.
        """
        file_name = data_record.name or str(book_id)
        format_lower = data_record.format.lower()

        # Try primary path: {name}.{format}
        primary = book_dir / f"{file_name}.{format_lower}"
        if primary.exists():
            return primary

        # Try alternative path: {book_id}.{format}
        alt = book_dir / f"{book_id}.{format_lower}"
        if alt.exists():
            return alt

        # Try to find by extension
        for file_path in book_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == f".{format_lower}":
                return file_path

        return None
