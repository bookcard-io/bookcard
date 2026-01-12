# Copyright (C) 2026 knguyen and others
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

"""Merge strategies for different book merge scenarios.

Follows OCP by using strategy pattern to allow extension without
modifying existing code.
"""

import logging
from typing import Protocol

from bookcard.services.book_merge.mergers import (
    CleanupService,
    CoverMerger,
    FileMerger,
    MetadataMerger,
)
from bookcard.services.book_merge.protocols import BookRepository
from bookcard.services.book_merge.value_objects import MergeContext

logger = logging.getLogger(__name__)


class MergeStrategy(Protocol):
    """Protocol for merge strategies."""

    def can_handle(self, merge_context: MergeContext) -> bool:
        """Check if this strategy can handle the merge context."""
        ...

    def execute(self, merge_context: MergeContext) -> None:
        """Execute the merge strategy."""
        ...


class DefaultBookMergeStrategy:
    """Default strategy for merging books.

    Orchestrates the merge process using specialized component mergers.
    """

    def __init__(
        self,
        repository: BookRepository,
        metadata_merger: MetadataMerger,
        cover_merger: CoverMerger,
        file_merger: FileMerger,
        cleanup_service: CleanupService,
    ) -> None:
        self._repository = repository
        self._metadata_merger = metadata_merger
        self._cover_merger = cover_merger
        self._file_merger = file_merger
        self._cleanup_service = cleanup_service

    def can_handle(self, merge_context: MergeContext) -> bool:  # noqa: ARG002
        """Check if this strategy can handle the merge context."""
        return True

    def execute(self, merge_context: MergeContext) -> None:
        """Execute merge."""
        keep_book = merge_context.keep_book
        merge_book = merge_context.merge_book

        logger.info("Merging book %s into %s", merge_book.id, keep_book.id)

        # 1. Merge Metadata
        self._metadata_merger.merge(keep_book, merge_book)

        # 2. Merge Cover
        self._cover_merger.merge(keep_book, merge_book)

        # 3. Merge Files
        # Need to fetch data records first
        if not keep_book.id or not merge_book.id:
            # Should not happen as books are persisted
            return

        keep_data_result = self._repository.get_with_data(keep_book.id)
        if not keep_data_result:
            # Should be impossible given keep_book exists, but handle type safety
            keep_data = []
        else:
            _, keep_data = keep_data_result

        merge_data_result = self._repository.get_with_data(merge_book.id)
        if not merge_data_result:
            merge_data = []
        else:
            _, merge_data = merge_data_result

        self._file_merger.merge(keep_book, merge_book, keep_data, merge_data)

        # 4. Cleanup
        self._cleanup_service.cleanup(merge_book)
