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

"""Batch processors for OpenLibrary dump ingestion.

Handles batching and committing of objects with deduplication support.
"""

from typing import TypeVar

from bookcard.models.openlibrary import (
    OpenLibraryAuthorWork,
    OpenLibraryEditionIsbn,
)
from bookcard.services.tasks.openlibrary.protocols import DatabaseRepository

T = TypeVar("T")


class BatchProcessor[T]:
    """Handles batching and committing of objects.

    Follows the Single Responsibility Principle by focusing solely on
    batch management and committing.

    Parameters
    ----------
    repository : DatabaseRepository
        Database repository for committing batches.
    batch_size : int
        Maximum number of items before auto-flushing. Defaults to 10000.
    """

    def __init__(
        self,
        repository: DatabaseRepository,
        batch_size: int = 10000,
    ) -> None:
        """Initialize batch processor.

        Parameters
        ----------
        repository : DatabaseRepository
            Database repository for committing batches.
        batch_size : int
            Maximum number of items before auto-flushing.
        """
        self.repository = repository
        self.batch_size = batch_size
        self._current_batch: list[T] = []

    def add(self, items: list[T]) -> None:
        """Add items to current batch.

        Automatically flushes if batch size is reached.

        Parameters
        ----------
        items : list[T]
            Items to add to the batch.
        """
        self._current_batch.extend(items)
        if len(self._current_batch) >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        """Commit current batch to database.

        Deduplicates items if needed before committing.
        """
        if self._current_batch:
            # Deduplicate if needed
            unique_items = self._deduplicate(self._current_batch)
            if unique_items:
                self.repository.bulk_save(unique_items)
                self.repository.commit()
            self._current_batch.clear()

    def _deduplicate(self, items: list[T]) -> list[T]:
        """Remove duplicates from batch.

        Override in subclasses if deduplication is needed.

        Parameters
        ----------
        items : list[T]
            Items to deduplicate.

        Returns
        -------
        list[T]
            Deduplicated items.
        """
        return items


class AuthorWorkBatchProcessor(BatchProcessor[OpenLibraryAuthorWork]):
    """Batch processor for author-work relationships with deduplication.

    Removes duplicate author-work pairs to prevent unique constraint violations.
    """

    def _deduplicate(
        self, items: list[OpenLibraryAuthorWork]
    ) -> list[OpenLibraryAuthorWork]:
        """Remove duplicate author-work pairs.

        Parameters
        ----------
        items : list[OpenLibraryAuthorWork]
            Author-work relationships to deduplicate.

        Returns
        -------
        list[OpenLibraryAuthorWork]
            Deduplicated relationships.
        """
        seen: set[tuple[str, str]] = set()
        unique: list[OpenLibraryAuthorWork] = []

        for item in items:
            pair = (item.author_key, item.work_key)
            if pair not in seen:
                seen.add(pair)
                unique.append(item)

        return unique


class IsbnBatchProcessor(BatchProcessor[OpenLibraryEditionIsbn]):
    """Batch processor for ISBNs with deduplication.

    Removes duplicate edition-ISBN pairs to prevent unique constraint violations.
    """

    def _deduplicate(
        self, items: list[OpenLibraryEditionIsbn]
    ) -> list[OpenLibraryEditionIsbn]:
        """Remove duplicate edition-ISBN pairs.

        Parameters
        ----------
        items : list[OpenLibraryEditionIsbn]
            ISBN relationships to deduplicate.

        Returns
        -------
        list[OpenLibraryEditionIsbn]
            Deduplicated relationships.
        """
        seen: set[tuple[str, str]] = set()
        unique: list[OpenLibraryEditionIsbn] = []

        for item in items:
            pair = (item.edition_key, item.isbn)
            if pair not in seen:
                seen.add(pair)
                unique.append(item)

        return unique
