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

"""Ingest processor service.

Orchestrates the ingest process for file groups. Follows SRP and IOC principles.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.models.ingest import IngestHistory, IngestStatus
from bookcard.models.metadata import MetadataRecord
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.repositories.ingest_repository import (
    IngestAuditRepository,
    IngestHistoryRepository,
)
from bookcard.services.author_exceptions import NoActiveLibraryError
from bookcard.services.book_service import BookService
from bookcard.services.dedrm_service import DeDRMService
from bookcard.services.ingest.exceptions import (
    IngestHistoryCreationError,
    IngestHistoryNotFoundError,
)
from bookcard.services.ingest.file_discovery_service import FileGroup
from bookcard.services.ingest.ingest_config_service import IngestConfigService
from bookcard.services.ingest.metadata_extraction import (
    ExtractedMetadata,
    extract_metadata,
)
from bookcard.services.ingest.metadata_fetch_service import MetadataFetchService
from bookcard.services.ingest.metadata_query import MetadataQuery

logger = logging.getLogger(__name__)

# Set to True to enable DeDRM processing on ingest
ENABLE_DEDRM_ON_INGEST = False


class IngestProcessorService:
    """Service for processing file groups during ingest.

    Orchestrates the full ingest process: creates history records,
    fetches metadata, and processes files.

    Parameters
    ----------
    session : Session
        Database session.
    config_service : IngestConfigService | None
        Optional config service (creates default if None).
    history_repo : IngestHistoryRepository | None
        Optional history repository (creates default if None).
    audit_repo : IngestAuditRepository | None
        Optional audit repository (creates default if None).
    library_repo : LibraryRepository | None
        Optional library repository (creates default if None).
    book_service_factory : Callable[[Library], BookService] | None
        Optional factory for creating BookService instances.
    metadata_fetch_service : MetadataFetchService | None
        Optional metadata fetch service (creates default if None).
    dedrm_service : DeDRMService | None
        Optional DeDRM service (creates default if None).
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        config_service: IngestConfigService | None = None,
        history_repo: IngestHistoryRepository | None = None,
        audit_repo: IngestAuditRepository | None = None,
        library_repo: LibraryRepository | None = None,
        book_service_factory: Callable[[Library], BookService] | None = None,
        metadata_fetch_service: MetadataFetchService | None = None,
        dedrm_service: DeDRMService | None = None,
    ) -> None:
        """Initialize ingest processor service.

        Parameters
        ----------
        session : Session
            Database session.
        config_service : IngestConfigService | None
            Optional config service.
        history_repo : IngestHistoryRepository | None
            Optional history repository.
        audit_repo : IngestAuditRepository | None
            Optional audit repository.
        library_repo : LibraryRepository | None
            Optional library repository.
        book_service_factory : Callable[[Library], BookService] | None
            Optional factory for creating BookService instances.
        metadata_fetch_service : MetadataFetchService | None
            Optional metadata fetch service.
        dedrm_service : DeDRMService | None
            Optional DeDRM service.
        """
        self._session = session
        self._config_service = config_service or IngestConfigService(session)
        self._history_repo = history_repo or IngestHistoryRepository(session)
        self._audit_repo = audit_repo or IngestAuditRepository(session)
        self._library_repo = library_repo or LibraryRepository(session)
        self._book_service_factory = book_service_factory or (
            lambda lib: BookService(lib, session=session)
        )
        self._metadata_fetch_service = metadata_fetch_service
        self._dedrm_service = dedrm_service or DeDRMService()

    def process_file_group(
        self,
        file_group: FileGroup,
        user_id: int | None = None,
    ) -> int:
        """Process a file group and create ingest history record.

        Creates an IngestHistory record and prepares for processing.
        Actual file processing is done by IngestBookTask.

        Parameters
        ----------
        file_group : FileGroup
            File group to process.
        user_id : int | None
            Optional user ID who triggered the ingest.

        Returns
        -------
        int
            Ingest history ID.

        Raises
        ------
        IngestHistoryCreationError
            If history record creation fails.
        """
        history = self._create_history_from_file_group(file_group, user_id)
        history_id = self._persist_history(history)
        self._log_file_group_audit(file_group, history_id, user_id)

        logger.info(
            "Created ingest history %d for file group: %s (%d files)",
            history_id,
            file_group.book_key,
            len(file_group.files),
        )

        return history_id

    def fetch_and_store_metadata(
        self,
        history_id: int,
        metadata_hint: dict | None = None,
    ) -> dict | None:
        """Fetch metadata for an ingest history record.

        Parameters
        ----------
        history_id : int
            Ingest history ID.
        metadata_hint : dict | None
            Optional metadata hint from file extraction.

        Returns
        -------
        dict | None
            Fetched metadata, or None if fetch failed.

        Raises
        ------
        IngestHistoryNotFoundError
            If history record not found.
        """
        # Respect configuration flag for metadata fetching
        config = self._config_service.get_config()
        if not config.metadata_fetch_enabled:
            logger.info(
                "Metadata fetch is disabled in ingest configuration; "
                "skipping fetch for history %d",
                history_id,
            )
            return None

        history = self._get_history_or_raise(history_id)
        extracted = extract_metadata(history, metadata_hint)

        metadata_record = self._fetch_metadata_record(extracted)
        if not metadata_record:
            logger.warning("No metadata found for ingest history %d", history_id)
            return None

        fetched_dict = self._store_fetched_metadata(history, metadata_record)
        self._log_metadata_fetch_audit(history, metadata_record)

        logger.info(
            "Fetched metadata for ingest history %d from %s",
            history_id,
            metadata_record.source_id,
        )

        return fetched_dict

    def add_book_to_library(
        self,
        history_id: int,
        file_path: Path,
        file_format: str,
        title: str | None = None,
        author_name: str | None = None,
        pubdate: datetime | None = None,
        description: str | None = None,
        publisher: str | None = None,
        identifiers: list[dict[str, str]] | None = None,
        language_codes: list[str] | None = None,
        tags: list[str] | None = None,
        rating: int | None = None,
        cover_url: str | None = None,
    ) -> int:
        """Add a book file to the library.

        Parameters
        ----------
        history_id : int
            Ingest history ID.
        file_path : Path
            Path to book file.
        file_format : str
            File format extension.
        title : str | None
            Optional book title.
        author_name : str | None
            Optional author name.
        pubdate : datetime | None
            Optional publication date.
        description : str | None
            Optional book description.
        publisher : str | None
            Optional publisher name.
        identifiers : list[dict[str, str]] | None
            Optional list of identifiers (e.g. [{'type': 'isbn', 'val': '...'}]).
        language_codes : list[str] | None
            Optional list of language codes.
        tags : list[str] | None
            Optional list of tags.
        rating : int | None
            Optional rating (0-10).
        cover_url : str | None
            Optional cover URL to set.

        Returns
        -------
        int
            Book ID.

        Raises
        ------
        IngestHistoryNotFoundError
            If history record not found.
        NoActiveLibraryError
            If no active library is configured.
        """
        history = self._get_history_or_raise(history_id)
        library = self._get_active_library_or_raise()

        # Extract metadata with fallback to filename
        extracted = extract_metadata(history, fallback_title=file_path.stem)
        if not title:
            title = extracted.title
        if not author_name:
            author_name = extracted.primary_author

        # Create book using factory
        book_service = self._book_service_factory(library)

        # Attempt to strip DRM
        processed_file_path = self._process_file_drm(file_path)

        try:
            book_id = book_service.add_book(
                file_path=processed_file_path,
                file_format=file_format,
                title=title,
                author_name=author_name,
                pubdate=pubdate,
            )
        finally:
            self._cleanup_processed_file(file_path, processed_file_path)

        # Update additional metadata if provided
        if any([description, publisher, identifiers, language_codes, tags, rating]):
            try:
                book_service.update_book(
                    book_id=book_id,
                    description=description,
                    publisher_name=publisher,
                    identifiers=identifiers,
                    language_codes=language_codes,
                    tag_names=tags,
                    rating_value=rating,
                )
            except (ValueError, RuntimeError, OSError) as e:
                logger.warning(
                    "Failed to update additional metadata for book %d: %s", book_id, e
                )

        # Set cover if provided
        if cover_url:
            self.set_book_cover(book_id, cover_url)

        # Update history with book ID
        if history.book_id is None:
            history.book_id = book_id
            self._save_history(history)

        # Log audit
        self._audit_repo.log_action(
            action="book_added",
            file_path=str(file_path),
            metadata={"book_id": book_id},
            history_id=history_id,
        )

        logger.info(
            "Added book %d to library for ingest history %d",
            book_id,
            history_id,
        )

        return book_id

    def add_format_to_book(
        self,
        book_id: int,
        file_path: Path,
        file_format: str,
    ) -> None:
        """Add a format to an existing book.

        Parameters
        ----------
        book_id : int
            Book ID.
        file_path : Path
            Path to format file.
        file_format : str
            File format extension.
        """
        library = self._get_active_library_or_raise()
        book_service = self._book_service_factory(library)

        # Attempt to strip DRM
        processed_file_path = self._process_file_drm(file_path)

        try:
            book_service.add_format(
                book_id=book_id,
                file_path=processed_file_path,
                file_format=file_format,
            )
            logger.info("Added format %s to book %d", file_format, book_id)
        except Exception:
            logger.exception("Failed to add format %s to book %d", file_format, book_id)
            # We don't re-raise here to allow partial success (main book + some formats)
            # or maybe we should? The caller iterates.
            raise
        finally:
            self._cleanup_processed_file(file_path, processed_file_path)

    def _process_file_drm(self, file_path: Path) -> Path:
        """Process file for DRM removal.

        Parameters
        ----------
        file_path : Path
            Original file path.

        Returns
        -------
        Path
            Processed file path (may be same as original).
        """
        if not ENABLE_DEDRM_ON_INGEST:
            return file_path

        processed_file_path = file_path
        try:
            processed_file_path = self._dedrm_service.strip_drm(file_path)
            if processed_file_path != file_path:
                logger.info(
                    "DeDRM processed file: %s -> %s", file_path, processed_file_path
                )
        except (RuntimeError, FileNotFoundError, OSError) as e:
            logger.warning(
                "DeDRM failed for %s: %s. Proceeding with original file.", file_path, e
            )
            # Proceed with original file path
            processed_file_path = file_path
        return processed_file_path

    def _cleanup_processed_file(
        self, original_path: Path, processed_path: Path
    ) -> None:
        """Clean up processed file if it's a temporary copy.

        Parameters
        ----------
        original_path : Path
            Original file path.
        processed_path : Path
            Processed file path.
        """
        if processed_path != original_path and processed_path.exists():
            try:
                processed_path.unlink()
            except OSError:
                logger.warning("Failed to delete temp file: %s", processed_path)

    def set_book_cover(self, book_id: int, cover_url: str) -> None:
        """Set book cover from URL.

        Parameters
        ----------
        book_id : int
            Book ID.
        cover_url : str
            URL of the cover image.

        Raises
        ------
        NoActiveLibraryError
            If no active library is configured.
        """
        library = self._get_active_library_or_raise()
        book_service = self._book_service_factory(library)

        # Import lazily to avoid circular imports if any
        from bookcard.services.book_cover_service import BookCoverService

        cover_service = BookCoverService(book_service)
        try:
            cover_service.save_cover_from_url(book_id, cover_url)
            logger.info("Set cover for book %d from %s", book_id, cover_url)
        except (ValueError, RuntimeError, OSError) as e:
            logger.warning("Failed to set cover for book %d: %s", book_id, e)

    def update_history_status(
        self,
        history_id: int,
        status: IngestStatus,
        error_message: str | None = None,
    ) -> None:
        """Update ingest history status.

        Parameters
        ----------
        history_id : int
            Ingest history ID.
        status : IngestStatus
            New status.
        error_message : str | None
            Optional error message.

        Raises
        ------
        IngestHistoryNotFoundError
            If history record not found.
        """
        history = self._get_history_or_raise(history_id)

        history.status = status
        if error_message:
            history.error_message = error_message

        if status == IngestStatus.PROCESSING and history.started_at is None:
            history.started_at = datetime.now(UTC)
        elif status in (IngestStatus.COMPLETED, IngestStatus.FAILED):
            history.completed_at = datetime.now(UTC)

        self._save_history(history)

        logger.info(
            "Updated ingest history %d status to %s",
            history_id,
            status,
        )

    def finalize_history(
        self,
        history_id: int,
        book_ids: list[int],
    ) -> None:
        """Finalize ingest history with book IDs.

        Updates the history record with book IDs and sets status to COMPLETED.
        This method handles all persistence concerns, keeping the task focused
        on orchestration.

        Parameters
        ----------
        history_id : int
            Ingest history ID.
        book_ids : list[int]
            List of book IDs created during ingest.

        Raises
        ------
        IngestHistoryNotFoundError
            If history record not found.
        """
        history = self._get_history_or_raise(history_id)

        if history.ingest_metadata is None:
            history.ingest_metadata = {}
        history.ingest_metadata["book_ids"] = book_ids
        history.book_id = book_ids[0] if book_ids else None
        history.status = IngestStatus.COMPLETED
        history.completed_at = datetime.now(UTC)

        self._save_history(history)

        logger.info(
            "Finalized ingest history %d with %d book(s)",
            history_id,
            len(book_ids),
        )

    def get_history(self, history_id: int) -> IngestHistory:
        """Get ingest history record.

        Parameters
        ----------
        history_id : int
            Ingest history ID.

        Returns
        -------
        IngestHistory
            Ingest history record.

        Raises
        ------
        IngestHistoryNotFoundError
            If history not found.
        """
        return self._get_history_or_raise(history_id)

    def get_active_library(self) -> Library:
        """Get active library or raise exception if none exists.

        Returns
        -------
        Library
            Active library.

        Raises
        ------
        NoActiveLibraryError
            If no active library is configured.
        """
        return self._get_active_library_or_raise()

    # Private helper methods

    def _get_history_or_raise(self, history_id: int) -> IngestHistory:
        """Get history record or raise exception if not found.

        Parameters
        ----------
        history_id : int
            Ingest history ID.

        Returns
        -------
        IngestHistory
            Ingest history record.

        Raises
        ------
        IngestHistoryNotFoundError
            If history not found.
        """
        history = self._history_repo.get(history_id)
        if history is None:
            raise IngestHistoryNotFoundError(history_id)
        return history

    def create_book_service(self, library: Library) -> BookService:
        """Create a BookService instance for the given library.

        Parameters
        ----------
        library : Library
            Library configuration.

        Returns
        -------
        BookService
            BookService instance.
        """
        return self._book_service_factory(library)

    def _get_active_library_or_raise(self) -> Library:
        """Get active library or raise exception if none exists.

        Returns
        -------
        Library
            Active library.

        Raises
        ------
        NoActiveLibraryError
            If no active library is configured.
        """
        library = self._library_repo.get_active()
        if library is None:
            raise NoActiveLibraryError
        return library

    def _save_history(self, history: IngestHistory) -> None:
        """Save history record to database.

        Parameters
        ----------
        history : IngestHistory
            History record to save.
        """
        self._session.add(history)
        self._session.commit()

    def _create_history_from_file_group(
        self, file_group: FileGroup, user_id: int | None
    ) -> IngestHistory:
        """Create IngestHistory from FileGroup.

        Parameters
        ----------
        file_group : FileGroup
            File group to create history from.
        user_id : int | None
            Optional user ID.

        Returns
        -------
        IngestHistory
            Created history record (not yet persisted).
        """
        primary_path = file_group.files[0] if file_group.files else Path()
        return IngestHistory(
            file_path=str(primary_path),
            status=IngestStatus.PENDING,
            ingest_metadata={
                "book_key": file_group.book_key,
                "file_count": len(file_group.files),
                "files": [str(f) for f in file_group.files],
                "metadata_hint": file_group.metadata_hint,
            },
            user_id=user_id,
        )

    def _persist_history(self, history: IngestHistory) -> int:
        """Persist history and return ID.

        Parameters
        ----------
        history : IngestHistory
            History record to persist.

        Returns
        -------
        int
            History ID.

        Raises
        ------
        IngestHistoryCreationError
            If history creation fails.
        """
        self._history_repo.add(history)
        self._session.commit()
        self._session.refresh(history)

        if history.id is None:
            raise IngestHistoryCreationError

        return history.id

    def _log_file_group_audit(
        self, file_group: FileGroup, history_id: int, user_id: int | None
    ) -> None:
        """Log file group discovery audit.

        Parameters
        ----------
        file_group : FileGroup
            File group that was discovered.
        history_id : int
            Ingest history ID.
        user_id : int | None
            Optional user ID.
        """
        primary_path = file_group.files[0] if file_group.files else Path()
        self._audit_repo.log_action(
            action="file_group_discovered",
            file_path=str(primary_path),
            metadata={
                "book_key": file_group.book_key,
                "file_count": len(file_group.files),
            },
            history_id=history_id,
            user_id=user_id,
        )

    def _get_metadata_fetch_service(self) -> MetadataFetchService:
        """Get metadata fetch service, creating if needed.

        Returns
        -------
        MetadataFetchService
            Metadata fetch service instance.
        """
        if self._metadata_fetch_service is None:
            enabled_providers = self._config_service.get_enabled_providers()
            merge_strategy = self._config_service.get_merge_strategy()
            self._metadata_fetch_service = MetadataFetchService.create_default(
                enabled_providers=enabled_providers,
                merge_strategy=merge_strategy,
            )
        return self._metadata_fetch_service

    def _fetch_metadata_record(
        self, extracted: ExtractedMetadata
    ) -> MetadataRecord | None:
        """Fetch metadata record from service.

        Parameters
        ----------
        extracted : ExtractedMetadata
            Extracted metadata for query.

        Returns
        -------
        MetadataRecord | None
            Fetched metadata record, or None if not found.
        """
        service = self._get_metadata_fetch_service()
        query = MetadataQuery(
            title=extracted.title,
            authors=extracted.authors,
            isbn=extracted.isbn,
        )
        return service.fetch_metadata(query)

    def _store_fetched_metadata(
        self, history: IngestHistory, record: MetadataRecord
    ) -> dict:
        """Store fetched metadata in history record.

        Parameters
        ----------
        history : IngestHistory
            History record to update.
        record : MetadataRecord
            Metadata record to store.

        Returns
        -------
        dict
            Dictionary representation of stored metadata.
        """
        if history.ingest_metadata is None:
            history.ingest_metadata = {}

        fetched_dict = self._metadata_record_to_dict(record)
        history.ingest_metadata["fetched_metadata"] = fetched_dict

        self._save_history(history)

        return fetched_dict

    def _metadata_record_to_dict(self, record: MetadataRecord) -> dict:
        """Convert MetadataRecord to dictionary for storage.

        Parameters
        ----------
        record : MetadataRecord
            Metadata record to convert.

        Returns
        -------
        dict
            Dictionary representation.
        """
        return {
            "title": record.title,
            "authors": record.authors,
            "description": record.description,
            "cover_url": record.cover_url,
            "series": record.series,
            "series_index": record.series_index,
            "publisher": record.publisher,
            "published_date": record.published_date,
            "identifiers": record.identifiers,
        }

    def _log_metadata_fetch_audit(
        self, history: IngestHistory, record: MetadataRecord
    ) -> None:
        """Log metadata fetch audit.

        Parameters
        ----------
        history : IngestHistory
            History record.
        record : MetadataRecord
            Fetched metadata record.
        """
        self._audit_repo.log_action(
            action="metadata_fetched",
            file_path=history.file_path,
            metadata={"source": record.source_id},
            history_id=history.id,
        )
