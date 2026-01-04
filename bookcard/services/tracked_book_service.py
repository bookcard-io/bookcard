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

"""Service for tracked book management operations.

Follows SOLID principles:
- SRP: Focuses solely on tracked book CRUD and library matching logic.
- IOC: Accepts repositories and services as dependencies.
"""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlmodel import Session, select

from bookcard.models.pvr import TrackedBook, TrackedBookStatus
from bookcard.repositories.base import Repository
from bookcard.repositories.calibre.repository import CalibreBookRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import LibraryService

if TYPE_CHECKING:
    from bookcard.api.schemas.tracked_books import (
        TrackedBookCreate,
        TrackedBookUpdate,
    )

logger = logging.getLogger(__name__)


class TrackedBookRepository(Repository[TrackedBook]):
    """Repository for tracked book definitions."""

    def __init__(self, session: Session) -> None:
        """Initialize tracked book repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        super().__init__(session, TrackedBook)

    def list_by_status(self, status: TrackedBookStatus) -> list[TrackedBook]:
        """List tracked books by status.

        Parameters
        ----------
        status : TrackedBookStatus
            Status to filter by.

        Returns
        -------
        list[TrackedBook]
            List of tracked books with the specified status.
        """
        stmt = select(TrackedBook).where(TrackedBook.status == status)
        return list(self._session.exec(stmt).all())

    def get_by_metadata_id(
        self, source_id: str, external_id: str
    ) -> TrackedBook | None:
        """Get tracked book by metadata ID.

        Parameters
        ----------
        source_id : str
            Metadata source ID (e.g., 'google').
        external_id : str
            External ID from provider.

        Returns
        -------
        TrackedBook | None
            Tracked book if found, None otherwise.
        """
        stmt = select(TrackedBook).where(
            TrackedBook.metadata_source_id == source_id,
            TrackedBook.metadata_external_id == external_id,
        )
        return self._session.exec(stmt).first()


class TrackedBookService:
    """Service for tracked book management operations.

    Handles CRUD operations and library matching for tracked books.

    Parameters
    ----------
    session : Session
        Database session.
    library_service : LibraryService | None
        Library service for accessing Calibre library.
    repository : TrackedBookRepository | None
        Tracked book repository. If None, creates a new instance.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        library_service: LibraryService | None = None,
        repository: TrackedBookRepository | None = None,
    ) -> None:
        """Initialize tracked book service.

        Parameters
        ----------
        session : Session
            Database session.
        library_service : LibraryService | None
            Library service. If None, creates a new instance.
        repository : TrackedBookRepository | None
            Tracked book repository. If None, creates a new instance.
        """
        self._session = session
        self._repository = repository or TrackedBookRepository(session)
        # We need LibraryService to get the active library configuration
        # but we instantiate CalibreBookRepository on demand based on that config
        if library_service:
            self._library_service = library_service
        else:
            library_repo = LibraryRepository(session)
            self._library_service = LibraryService(session, library_repo)

    def create_tracked_book(self, data: "TrackedBookCreate") -> TrackedBook:
        """Create a new tracked book.

        Checks for existing tracking and library matches before creating.

        Parameters
        ----------
        data : TrackedBookCreate
            Tracked book creation data.

        Returns
        -------
        TrackedBook
            Created tracked book.

        Raises
        ------
        ValueError
            If book is already being tracked.
        """
        # Check if already tracked by metadata ID
        if data.metadata_source_id and data.metadata_external_id:
            existing = self._repository.get_by_metadata_id(
                data.metadata_source_id, data.metadata_external_id
            )
            if existing:
                msg = (
                    f"Book is already being tracked "
                    f"(id={existing.id}, title='{existing.title}')"
                )
                raise ValueError(msg)

        # Initialize status
        status = TrackedBookStatus.WANTED

        # Check for match in library
        matched_book_id, has_files = self._find_library_match(
            data.title, data.author, data.library_id
        )

        if matched_book_id:
            logger.info(
                "Found library match for '%s' by %s: book_id=%s, has_files=%s",
                data.title,
                data.author,
                matched_book_id,
                has_files,
            )
            if has_files:
                # If matched and has files, it's completed
                status = TrackedBookStatus.COMPLETED
            # If matched but no files (empty book entry), keep as WANTED
            # or maybe we consider it partially complete? sticking to WANTED for now
            # as logic says "if matched AND... has a format... no need to download"

        tracked_book = TrackedBook(
            title=data.title,
            author=data.author,
            isbn=data.isbn,
            library_id=data.library_id,
            metadata_source_id=data.metadata_source_id,
            metadata_external_id=data.metadata_external_id,
            status=status,
            monitor_mode=data.monitor_mode,
            auto_search_enabled=data.auto_search_enabled,
            auto_download_enabled=data.auto_download_enabled,
            preferred_formats=data.preferred_formats,
            matched_book_id=matched_book_id,
            matched_library_id=data.library_id,  # Assume match is in target library
            cover_url=data.cover_url,
            description=data.description,
            publisher=data.publisher,
            published_date=data.published_date,
            rating=data.rating,
            tags=data.tags,
        )

        self._repository.add(tracked_book)
        self._session.commit()
        self._session.refresh(tracked_book)
        logger.info(
            "Created tracked book: %s (id=%s, status=%s)",
            tracked_book.title,
            tracked_book.id,
            tracked_book.status,
        )
        return tracked_book

    def get_tracked_book(self, tracked_book_id: int) -> TrackedBook | None:
        """Get a tracked book by ID.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.

        Returns
        -------
        TrackedBook | None
            Tracked book if found, None otherwise.
        """
        return self._repository.get(tracked_book_id)

    def list_tracked_books(
        self, status: TrackedBookStatus | None = None
    ) -> list[TrackedBook]:
        """List tracked books.

        Parameters
        ----------
        status : TrackedBookStatus | None
            Optional status filter.

        Returns
        -------
        list[TrackedBook]
            List of tracked books.
        """
        if status:
            return self._repository.list_by_status(status)
        return list(self._repository.list())

    def update_tracked_book(
        self, tracked_book_id: int, data: "TrackedBookUpdate"
    ) -> TrackedBook | None:
        """Update a tracked book.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.
        data : TrackedBookUpdate
            Update data (partial).

        Returns
        -------
        TrackedBook | None
            Updated tracked book if found, None otherwise.
        """
        tracked_book = self._repository.get(tracked_book_id)
        if tracked_book is None:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tracked_book, key, value)

        tracked_book.updated_at = datetime.now(UTC)
        self._session.add(tracked_book)
        self._session.commit()
        self._session.refresh(tracked_book)
        return tracked_book

    def delete_tracked_book(self, tracked_book_id: int) -> bool:
        """Delete a tracked book.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        tracked_book = self._repository.get(tracked_book_id)
        if tracked_book is None:
            return False

        self._repository.delete(tracked_book)
        self._session.commit()
        logger.info(
            "Deleted tracked book: %s (id=%s)", tracked_book.title, tracked_book.id
        )
        return True

    def check_status(self, tracked_book_id: int) -> TrackedBook | None:
        """Check status of a tracked book (re-check library match).

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.

        Returns
        -------
        TrackedBook | None
            Updated tracked book if found, None otherwise.
        """
        tracked_book = self._repository.get(tracked_book_id)
        if tracked_book is None:
            return None

        # Re-check library match
        matched_book_id, has_files = self._find_library_match(
            tracked_book.title, tracked_book.author, tracked_book.library_id
        )

        if matched_book_id != tracked_book.matched_book_id:
            tracked_book.matched_book_id = matched_book_id
            tracked_book.matched_library_id = tracked_book.library_id
            if has_files and tracked_book.status != TrackedBookStatus.COMPLETED:
                tracked_book.status = TrackedBookStatus.COMPLETED

            tracked_book.updated_at = datetime.now(UTC)
            self._session.add(tracked_book)
            self._session.commit()
            self._session.refresh(tracked_book)

        return tracked_book

    def update_search_status(
        self, tracked_book_id: int, searched_at: datetime, status: TrackedBookStatus
    ) -> None:
        """Update search status of a tracked book.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.
        searched_at : datetime
            Timestamp of search.
        status : TrackedBookStatus
            New status.
        """
        tracked_book = self._repository.get(tracked_book_id)
        if tracked_book:
            tracked_book.last_searched_at = searched_at
            tracked_book.status = status
            tracked_book.updated_at = datetime.now(UTC)
            self._session.add(tracked_book)
            self._session.commit()

    def get_book_files(self, book: TrackedBook) -> list[dict[str, Any]]:
        """Get files for a tracked book.

        Prioritizes persisted TrackedBookFile records.
        Falls back to querying Calibre if matched_book_id is present.

        Parameters
        ----------
        book : TrackedBook
            The tracked book instance.

        Returns
        -------
        list[dict[str, Any]]
            List of file dictionaries with keys: name, format, size, path.
        """
        # 1. Use persisted files if available
        if book.files:
            return [
                {
                    "name": f.filename,
                    "format": f.file_type,
                    "size": f.size_bytes,
                    "path": f.path,
                }
                for f in book.files
            ]

        # 2. Fallback to Calibre
        if book.matched_book_id:
            try:
                # Import here to avoid circular dependencies
                from bookcard.services.book_service import BookService

                if book.matched_library_id:
                    library = self._library_service.get_library(book.matched_library_id)
                else:
                    library = self._library_service.get_active_library()

                if library:
                    book_service = BookService(library, self._session)
                    full_book = book_service.get_book_full(book.matched_book_id)

                    if full_book and full_book.formats:
                        files = []
                        for fmt in full_book.formats:
                            file_format = str(fmt.get("format", "")).upper()
                            try:
                                path = book_service.get_format_file_path(
                                    book.matched_book_id, file_format
                                )
                                files.append({
                                    "name": str(path.name),
                                    "format": file_format,
                                    "size": int(fmt.get("size", 0)),
                                    "path": str(path),
                                })
                            except (ValueError, RuntimeError) as e:
                                logger.debug(
                                    "Failed to get file info for format %s: %s",
                                    file_format,
                                    e,
                                )
                                continue
                        return files
            except (ValueError, RuntimeError, OSError) as e:
                logger.warning(
                    "Failed to fetch files for tracked book %d: %s", book.id, e
                )

        return []

    def _find_library_match(
        self, title: str, author: str, library_id: int | None
    ) -> tuple[int | None, bool]:
        """Find matching book in Calibre library.

        Parameters
        ----------
        title : str
            Title to match (case-insensitive exact match).
        author : str
            Author to match (case-insensitive exact match).
        library_id : int | None
            Target library ID (None uses active library).

        Returns
        -------
        tuple[int | None, bool]
            Tuple of (book_id, has_files). book_id is None if no match.
        """
        # Get library config
        if library_id:
            library = self._library_service.get_library(library_id)
        else:
            library = self._library_service.get_active_library()

        if not library:
            logger.warning("No library available for matching")
            return None, False

        # Create repository for this library
        calibre_repo = CalibreBookRepository(library.calibre_db_path)

        try:
            # Search for books with similar title
            # list_books uses generic search, so we search for title and filter results
            books = calibre_repo.list_books(search_query=title, full=False)

            title_lower = title.lower().strip()
            author_lower = author.lower().strip()

            for book_rel in books:
                # Check title match
                if book_rel.book.title.lower().strip() != title_lower:
                    continue

                # Check author match (any author matches)
                authors = [a.lower().strip() for a in book_rel.authors]
                if author_lower in authors:
                    # Found match! Check for formats
                    has_files = bool(book_rel.formats)
                    return book_rel.book.id, has_files

        except Exception:
            logger.exception("Error searching library for match")
            return None, False
        finally:
            calibre_repo.dispose()

        return None, False
