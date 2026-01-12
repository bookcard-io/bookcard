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

"""Book merge service for consolidating duplicate book records.

Follows SRP by focusing solely on book merge orchestration.
"""

import logging
from typing import Any

from sqlmodel import Session

from bookcard.services.book_merge.config import ScoringConfig
from bookcard.services.book_merge.infrastructure import (
    LocalFileStorage,
    SQLBookRepository,
)
from bookcard.services.book_merge.merge_strategies import DefaultBookMergeStrategy
from bookcard.services.book_merge.mergers import (
    CleanupService,
    CoverMerger,
    FileMerger,
    MetadataMerger,
)
from bookcard.services.book_merge.scorer import BookScorer
from bookcard.services.book_merge.validators import BookMergeValidator
from bookcard.services.book_merge.value_objects import MergeContext

logger = logging.getLogger(__name__)


class BookMergeService:
    """Service for merging duplicate book records."""

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        library_path: str,
    ) -> None:
        """Initialize book merge service.

        Parameters
        ----------
        session : Session
            Database session.
        library_path : str
            Path to the library root.
        """
        self._session = session
        self._library_path = library_path

        # Initialize infrastructure
        self._repository = SQLBookRepository(session)
        self._file_storage = LocalFileStorage(library_path)

        # Initialize domain services
        self._validator = BookMergeValidator()
        self._scorer = BookScorer(ScoringConfig())

        # Initialize component mergers
        self._metadata_merger = MetadataMerger(self._repository)
        self._cover_merger = CoverMerger(
            self._file_storage,
            self._file_storage._library_path,  # type: ignore[attr-defined] # noqa: SLF001
        )
        self._file_merger = FileMerger(
            self._file_storage,
            self._repository,
            self._file_storage._library_path,  # type: ignore[attr-defined] # noqa: SLF001
        )
        self._cleanup_service = CleanupService(
            self._repository,
            self._file_storage,
            self._file_storage._library_path,  # type: ignore[attr-defined] # noqa: SLF001
        )

    def recommend_keep_book(self, book_ids: list[int]) -> dict[str, Any]:
        """Recommend which book to keep when merging.

        Parameters
        ----------
        book_ids : list[int]
            List of book IDs to merge.

        Returns
        -------
        dict[str, Any]
            Dictionary with:
            - recommended_keep_id: Recommended book ID to keep
            - books: List of book details for modal display
        """
        self._validator.validate_recommendation_request(book_ids)

        books = self._repository.get_many_or_raise(book_ids)

        # Calculate scores to determine best book
        scored_books = []
        for book in books:
            if not book.id:
                continue
            data_result = self._repository.get_with_data(book.id)
            if not data_result:
                continue
            _, data_records = data_result
            score = self._scorer.score_book(book, data_records)
            scored_books.append((score, book, data_records))

        # Sort by score descending
        scored_books.sort(key=lambda x: x[0], reverse=True)
        recommended_book = scored_books[0][1]

        # Build details for response
        book_details = []
        for _, book, data_records in scored_books:
            formats = [
                {"format": d.format, "size": d.uncompressed_size, "name": d.name}
                for d in data_records
            ]

            book_details.append({
                "id": book.id,
                "title": book.title,
                "author": book.author_sort,  # Using author_sort as proxy for author display
                "year": book.pubdate.year if book.pubdate else None,
                "publisher": book.publisher
                if hasattr(book, "publisher")
                else None,  # Check if publisher attr exists on Book (it's in linked tables usually, but Book model might have cached it or not)
                "has_cover": book.has_cover,
                "formats": formats,
                "path": book.path,
            })

        return {"recommended_keep_id": recommended_book.id, "books": book_details}

    def merge_books(self, book_ids: list[int], keep_book_id: int) -> dict[str, Any]:
        """Merge multiple books into one.

        Parameters
        ----------
        book_ids : list[int]
            List of book IDs to merge.
        keep_book_id : int
            Book ID to keep.

        Returns
        -------
        dict[str, Any]
            Dictionary with merged book details.
        """
        self._validator.validate_merge_request(book_ids, keep_book_id)

        keep_book = self._repository.get_or_raise(keep_book_id)
        if not keep_book.id:
            # Should not happen as we got it from DB
            msg = "Keep book has no ID"
            raise ValueError(msg)

        # Get merge books
        merge_books = []
        for bid in book_ids:
            if bid == keep_book_id:
                continue
            book = self._repository.get_or_raise(bid)
            if not book.id:
                msg = f"Book {bid} has no ID"
                raise ValueError(msg)
            merge_books.append(book)

        # Initialize strategy
        strategy = DefaultBookMergeStrategy(
            repository=self._repository,
            metadata_merger=self._metadata_merger,
            cover_merger=self._cover_merger,
            file_merger=self._file_merger,
            cleanup_service=self._cleanup_service,
        )

        # Execute merge for each book
        for merge_book in merge_books:
            context = MergeContext(keep_book=keep_book, merge_book=merge_book)
            strategy.execute(context)

        self._repository.commit()

        return {
            "id": keep_book.id,
            "title": keep_book.title,
            "message": "Books merged successfully",
        }
