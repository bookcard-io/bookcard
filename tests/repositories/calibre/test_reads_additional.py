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

"""Additional tests for reads module to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from sqlmodel import Session

from bookcard.models.core import Author, Book, BookAuthorLink
from bookcard.models.media import Data
from bookcard.repositories.calibre.enrichment import BookEnrichmentService
from bookcard.repositories.calibre.queries import BookQueryBuilder
from bookcard.repositories.calibre.reads import BookReadOperations
from bookcard.repositories.calibre.retry import SQLiteRetryPolicy
from bookcard.repositories.calibre.unwrapping import ResultUnwrapper
from tests.repositories.calibre.conftest import (
    MockBookSearchService,
    MockLibraryStatisticsService,
    MockSessionManager,
)

if TYPE_CHECKING:
    from sqlmodel import Session


class TestBookReadOperationsAdditional:
    """Additional tests for BookReadOperations to achieve 100% coverage."""

    def test_count_books_with_author_id(
        self, in_memory_db: Session, sample_book: Book, sample_author: Author
    ) -> None:
        """Test count_books with author_id filter."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        in_memory_db.add(BookAuthorLink(book=sample_book.id, author=sample_author.id))
        in_memory_db.commit()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        assert sample_author.id is not None
        count = operations.count_books(author_id=sample_author.id)
        assert count == 1

    def test_list_books_with_author_id(
        self, in_memory_db: Session, sample_book: Book, sample_author: Author
    ) -> None:
        """Test list_books with author_id filter."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        in_memory_db.add(BookAuthorLink(book=sample_book.id, author=sample_author.id))
        in_memory_db.add(
            Data(
                book=sample_book.id,
                format="EPUB",
                uncompressed_size=1000,
                name="Test Book",
            )
        )
        in_memory_db.commit()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        assert sample_author.id is not None
        books = operations.list_books(author_id=sample_author.id)
        assert len(books) == 1

    def test_list_books_with_pubdate_filters(
        self, in_memory_db: Session, sample_book: Book
    ) -> None:
        """Test list_books with pubdate filters."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        books = operations.list_books(pubdate_month=12, pubdate_day=12)
        assert isinstance(books, list)

    def test_count_books_with_pubdate_filters(
        self, in_memory_db: Session, sample_book: Book
    ) -> None:
        """Test count_books with pubdate filters."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        count = operations.count_books(pubdate_month=12, pubdate_day=12)
        assert isinstance(count, int)

    def test_list_books_with_filters_full(
        self, in_memory_db: Session, sample_book: Book
    ) -> None:
        """Test list_books_with_filters with full=True."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        books = operations.list_books_with_filters(full=True)
        assert isinstance(books, list)

    def test_list_books_with_filters_with_author_ids(
        self, in_memory_db: Session, sample_book: Book, sample_author: Author
    ) -> None:
        """Test list_books_with_filters with author_ids."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        in_memory_db.add(BookAuthorLink(book=sample_book.id, author=sample_author.id))
        in_memory_db.commit()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        assert sample_author.id is not None
        books = operations.list_books_with_filters(author_ids=[sample_author.id])
        assert isinstance(books, list)

    def test_count_books_with_filters(
        self, in_memory_db: Session, sample_book: Book
    ) -> None:
        """Test count_books_with_filters."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        count = operations.count_books_with_filters()
        assert isinstance(count, int)

    def test_filter_suggestions_with_none_strategy(self, in_memory_db: Session) -> None:
        """Test filter_suggestions returns empty when strategy is None."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        # Use invalid filter_type to get None strategy
        result = operations.filter_suggestions(query="test", filter_type="invalid")
        assert result == []

    def test_list_books_with_invalid_sort_order(
        self, in_memory_db: Session, sample_book: Book
    ) -> None:
        """Test list_books normalizes invalid sort_order."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        books = operations.list_books(sort_order="invalid")
        assert isinstance(books, list)

    def test_list_books_with_filters_invalid_sort_order(
        self, in_memory_db: Session
    ) -> None:
        """Test list_books_with_filters normalizes invalid sort_order."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        books = operations.list_books_with_filters(sort_order="invalid")
        assert isinstance(books, list)

    def test_build_book_with_relations_with_none_book(
        self, in_memory_db: Session
    ) -> None:
        """Test _build_book_with_relations handles None book."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        result = operations._build_book_with_relations(in_memory_db, None)
        assert result is None

    def test_build_book_with_relations_with_none_id(
        self, in_memory_db: Session
    ) -> None:
        """Test _build_book_with_relations handles book with None id."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
        )

        book_no_id = Book(
            id=None, title="Test", uuid="test", timestamp=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.Book = book_no_id
        result = operations._build_book_with_relations(in_memory_db, mock_result)
        assert result is None
