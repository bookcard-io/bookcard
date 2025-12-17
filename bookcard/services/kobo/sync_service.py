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

"""Kobo sync service.

Orchestrates library sync operations, queries books that need syncing,
and generates sync responses.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.kobo import KoboReadingState
    from bookcard.repositories.kobo_repository import (
        KoboArchivedBookRepository,
        KoboReadingStateRepository,
        KoboSyncedBookRepository,
    )
    from bookcard.repositories.models import BookWithFullRelations, BookWithRelations
    from bookcard.repositories.reading_repository import ReadStatusRepository
    from bookcard.services.book_service import BookService
    from bookcard.services.kobo.metadata_service import KoboMetadataService
    from bookcard.services.kobo.sync_token_service import SyncToken
    from bookcard.services.shelf_service import ShelfService

SYNC_ITEM_LIMIT = 100


class KoboSyncService:
    """Service for orchestrating Kobo library sync operations.

    Handles querying books that need syncing, generating sync responses,
    and tracking synced books.

    Parameters
    ----------
    session : Session
        Database session.
    book_service : BookService
        Book service for querying books.
    metadata_service : KoboMetadataService
        Metadata service for formatting book data.
    reading_state_repo : KoboReadingStateRepository
        Repository for reading states.
    synced_book_repo : KoboSyncedBookRepository
        Repository for synced books.
    archived_book_repo : KoboArchivedBookRepository
        Repository for archived books.
    read_status_repo : ReadStatusRepository
        Repository for read status.
    shelf_service : ShelfService | None
        Optional shelf service for shelf filtering.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        book_service: BookService,
        metadata_service: KoboMetadataService,
        reading_state_repo: KoboReadingStateRepository,
        synced_book_repo: KoboSyncedBookRepository,
        archived_book_repo: KoboArchivedBookRepository,
        read_status_repo: ReadStatusRepository,
        shelf_service: ShelfService | None = None,
    ) -> None:
        self._session = session
        self._book_service = book_service
        self._metadata_service = metadata_service
        self._reading_state_repo = reading_state_repo
        self._synced_book_repo = synced_book_repo
        self._archived_book_repo = archived_book_repo
        self._read_status_repo = read_status_repo
        self._shelf_service = shelf_service

    def sync_library(
        self,
        user_id: int,
        library_id: int,
        sync_token: SyncToken,
        only_shelves: bool = False,
    ) -> tuple[list[dict[str, object]], bool]:
        """Sync library for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        sync_token : SyncToken
            Sync token with last sync timestamps.
        only_shelves : bool
            If True, only sync books in Kobo-synced shelves.

        Returns
        -------
        tuple[list[dict[str, object]], bool]
            Tuple of (sync results list, continue sync flag).
        """
        sync_results: list[dict[str, object]] = []

        # Get books to sync
        books_to_sync = self._get_books_to_sync(
            user_id, library_id, sync_token, only_shelves
        )

        # Track which books have reading states in new entitlements
        reading_states_in_new_entitlements: list[int] = []

        # Process books
        new_books_last_modified = sync_token.books_last_modified
        new_books_last_created = sync_token.books_last_created
        new_reading_state_last_modified = sync_token.reading_state_last_modified

        for book_with_rels in books_to_sync[:SYNC_ITEM_LIMIT]:
            book = book_with_rels.book
            if book.id is None:
                continue

            # Check if archived
            archived_book = self._archived_book_repo.find_by_user_and_book(
                user_id, book.id
            )
            is_archived = archived_book.is_archived if archived_book else False

            # Get or create reading state
            reading_state = self._reading_state_repo.find_by_user_and_book(
                user_id, book.id
            )

            # Create entitlement and metadata
            entitlement = {
                "BookEntitlement": self._metadata_service.create_book_entitlement(
                    book, is_archived
                ),
                "BookMetadata": self._metadata_service.get_book_metadata(
                    book_with_rels
                ),
            }

            # Add reading state if modified
            if (
                reading_state
                and reading_state.last_modified > sync_token.reading_state_last_modified
            ):
                find_method = getattr(
                    self._read_status_repo, "find_by_user_library_book", None
                )
                read_status = (
                    find_method(user_id, library_id, book.id) if find_method else None
                )
                entitlement["ReadingState"] = (
                    self._metadata_service.get_reading_state_response(
                        book, reading_state, read_status
                    )
                )
                new_reading_state_last_modified = max(
                    new_reading_state_last_modified, reading_state.last_modified
                )
                reading_states_in_new_entitlements.append(book.id)

            # Determine if new or changed
            book_timestamp = book.timestamp or datetime.min.replace(tzinfo=UTC)
            if book_timestamp > sync_token.books_last_created:
                sync_results.append({"NewEntitlement": entitlement})
            else:
                sync_results.append({"ChangedEntitlement": entitlement})

            # Update timestamps
            book_last_modified = book.last_modified or datetime.min.replace(tzinfo=UTC)
            new_books_last_modified = max(new_books_last_modified, book_last_modified)
            new_books_last_created = max(new_books_last_created, book_timestamp)

            # Mark as synced
            self._mark_book_synced(user_id, book.id)

        # Update sync token
        sync_token.books_last_modified = new_books_last_modified
        sync_token.books_last_created = new_books_last_created
        sync_token.reading_state_last_modified = new_reading_state_last_modified

        # Get changed reading states (not in new entitlements)
        changed_reading_states = self._get_reading_states_to_sync(
            user_id, sync_token, reading_states_in_new_entitlements
        )

        for reading_state in changed_reading_states[:SYNC_ITEM_LIMIT]:
            # Get book for reading state
            book_with_rels = self._book_service.get_book(reading_state.book_id)
            if book_with_rels is None:
                continue

            book = book_with_rels.book
            find_method = getattr(
                self._read_status_repo, "find_by_user_library_book", None
            )
            read_status = (
                find_method(user_id, library_id, reading_state.book_id)
                if find_method
                else None
            )

            sync_results.append({
                "ChangedReadingState": {
                    "ReadingState": self._metadata_service.get_reading_state_response(
                        book, reading_state, read_status
                    )
                }
            })
            new_reading_state_last_modified = max(
                new_reading_state_last_modified, reading_state.last_modified
            )

        sync_token.reading_state_last_modified = new_reading_state_last_modified

        # Check if more items to sync
        continue_sync = (
            len(books_to_sync) > SYNC_ITEM_LIMIT
            or len(changed_reading_states) > SYNC_ITEM_LIMIT
        )

        return sync_results, continue_sync

    def _get_books_to_sync(
        self,
        user_id: int,
        library_id: int,
        sync_token: SyncToken,
        only_shelves: bool,
    ) -> list[BookWithRelations | BookWithFullRelations]:
        """Get books that need to be synced.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        sync_token : SyncToken
            Sync token with last sync timestamps.
        only_shelves : bool
            If True, only return books in Kobo-synced shelves.

        Returns
        -------
        list[BookWithRelations | BookWithFullRelations]
            List of books to sync.
        """
        synced_book_ids = self._synced_book_repo.find_book_ids_by_user(user_id)
        shelf_book_ids = self._get_shelf_book_ids(user_id, library_id, only_shelves)
        books, _total = self._book_service.list_books(
            page=1,
            page_size=1000,  # Large page size for sync
            full=True,
        )

        filtered_books = self._filter_books_for_sync(
            books, synced_book_ids, shelf_book_ids, sync_token
        )

        filtered_books.sort(
            key=lambda b: b.book.last_modified or datetime.min.replace(tzinfo=UTC),
            reverse=False,
        )

        return filtered_books

    def _get_shelf_book_ids(
        self, user_id: int, library_id: int, only_shelves: bool
    ) -> set[int] | None:
        """Get shelf book IDs if filtering by shelves.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        only_shelves : bool
            If True, get shelf book IDs.

        Returns
        -------
        set[int] | None
            Set of book IDs in shelves, or None if not filtering.
        """
        if not only_shelves or not self._shelf_service:
            return None

        shelves = self._shelf_service.list_user_shelves(
            library_id=library_id,
            user_id=user_id,
            include_public=True,
        )
        shelf_book_ids = set()
        for shelf in shelves:
            for book_link in shelf.book_links:
                if book_link.book_id:
                    shelf_book_ids.add(book_link.book_id)
        return shelf_book_ids

    def _filter_books_for_sync(
        self,
        books: list[BookWithRelations | BookWithFullRelations],
        synced_book_ids: set[int],
        shelf_book_ids: set[int] | None,
        sync_token: SyncToken,
    ) -> list[BookWithRelations | BookWithFullRelations]:
        """Filter books that need syncing.

        Parameters
        ----------
        books : list[BookWithRelations | BookWithFullRelations]
            All books to filter.
        synced_book_ids : set[int]
            Already synced book IDs.
        shelf_book_ids : set[int] | None
            Shelf book IDs if filtering by shelves.
        sync_token : SyncToken
            Sync token with last sync timestamps.

        Returns
        -------
        list[BookWithRelations | BookWithFullRelations]
            Filtered books to sync.
        """
        filtered_books: list[BookWithRelations | BookWithFullRelations] = []
        for book_with_rels in books:
            book = book_with_rels.book
            if book.id is None:
                continue

            if not self._should_sync_book(
                book, book_with_rels, synced_book_ids, shelf_book_ids, sync_token
            ):
                continue

            filtered_books.append(book_with_rels)
        return filtered_books

    def _should_sync_book(
        self,
        book: object,
        book_with_rels: BookWithRelations | BookWithFullRelations,
        synced_book_ids: set[int],
        shelf_book_ids: set[int] | None,
        sync_token: SyncToken,
    ) -> bool:
        """Check if a book should be synced.

        Parameters
        ----------
        book : object
            Book object.
        book_with_rels : BookWithRelations | BookWithFullRelations
            Book with relations.
        synced_book_ids : set[int]
            Already synced book IDs.
        shelf_book_ids : set[int] | None
            Shelf book IDs if filtering by shelves.
        sync_token : SyncToken
            Sync token with last sync timestamps.

        Returns
        -------
        bool
            True if book should be synced.
        """
        if not hasattr(book, "id") or book.id is None:
            return False

        if synced_book_ids and book.id in synced_book_ids:
            book_last_modified = getattr(
                book, "last_modified", None
            ) or datetime.min.replace(tzinfo=UTC)
            if book_last_modified <= sync_token.books_last_modified:
                return False

        if shelf_book_ids is not None and book.id not in shelf_book_ids:
            return False

        formats = getattr(book_with_rels, "formats", []) or []
        return any(f.get("format", "").upper() in ("KEPUB", "EPUB") for f in formats)

    def _get_reading_states_to_sync(
        self,
        user_id: int,
        sync_token: SyncToken,
        exclude_book_ids: list[int],
    ) -> list[KoboReadingState]:
        """Get reading states that need to be synced.

        Parameters
        ----------
        user_id : int
            User ID.
        sync_token : SyncToken
            Sync token with last sync timestamps.
        exclude_book_ids : list[int]
            Book IDs to exclude (already in new entitlements).

        Returns
        -------
        list[KoboReadingState]
            List of reading states to sync.
        """
        reading_states = self._reading_state_repo.find_by_user(
            user_id, sync_token.reading_state_last_modified
        )

        # Filter out excluded book IDs
        return [rs for rs in reading_states if rs.book_id not in exclude_book_ids]

    def _mark_book_synced(self, user_id: int, book_id: int) -> None:
        """Mark a book as synced.

        Parameters
        ----------
        user_id : int
            User ID.
        book_id : int
            Book ID.
        """
        existing = self._synced_book_repo.find_by_user_and_book(user_id, book_id)
        if existing:
            existing.synced_at = datetime.now(UTC)
        else:
            from bookcard.models.kobo import KoboSyncedBook

            synced_book = KoboSyncedBook(
                user_id=user_id,
                book_id=book_id,
            )
            self._synced_book_repo.add(synced_book)
        self._session.flush()
