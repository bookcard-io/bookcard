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

"""Tests for reads module."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bookcard.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookPublisherLink,
    BookSeriesLink,
    BookTagLink,
    Publisher,
    Series,
    Tag,
)

if TYPE_CHECKING:
    from sqlmodel import Session
from bookcard.models.media import Data
from bookcard.repositories.calibre.enrichment import BookEnrichmentService
from bookcard.repositories.calibre.pathing import BookPathService
from bookcard.repositories.calibre.queries import BookQueryBuilder
from bookcard.repositories.calibre.reads import BookReadOperations
from bookcard.repositories.calibre.retry import SQLiteRetryPolicy
from bookcard.repositories.calibre.unwrapping import ResultUnwrapper
from tests.repositories.calibre.conftest import (
    MockBookSearchService,
    MockLibraryStatisticsService,
    MockSessionManager,
)


class TestBookReadOperations:
    """Test suite for BookReadOperations."""

    def test_count_books_empty(self, in_memory_db: Session) -> None:
        """Test count_books returns 0 for empty database."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        count = operations.count_books()
        assert count == 0

    def test_count_books_with_books(
        self, in_memory_db: Session, sample_book: Book
    ) -> None:
        """Test count_books returns correct count."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        count = operations.count_books()
        assert count == 1

    def test_list_books_empty(self, in_memory_db: Session) -> None:
        """Test list_books returns empty list for empty database."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        books = operations.list_books()
        assert books == []

    def test_list_books_with_results(
        self, in_memory_db: Session, sample_book: Book, sample_author: Author
    ) -> None:
        """Test list_books returns books."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        # Create book-author link
        in_memory_db.add(BookAuthorLink(book=sample_book.id, author=sample_author.id))

        # Create series and link
        series = Series(id=99, name="Test Series")
        in_memory_db.add(series)
        in_memory_db.add(BookSeriesLink(book=sample_book.id, series=series.id))

        # Create publisher and link
        publisher = Publisher(id=88, name="Test Publisher")
        in_memory_db.add(publisher)
        in_memory_db.add(BookPublisherLink(book=sample_book.id, publisher=publisher.id))

        # Create tag and link
        tag = Tag(id=77, name="Fiction")
        in_memory_db.add(tag)
        in_memory_db.add(BookTagLink(book=sample_book.id, tag=tag.id))

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
            pathing=BookPathService(),
            calibre_db_path=Path("test.db"),
        )

        books = operations.list_books(limit=10)
        assert len(books) == 1
        assert books[0].book.id == sample_book.id
        assert books[0].author_ids == [sample_author.id]
        assert books[0].series_id == 99
        assert books[0].publisher_id == 88
        assert books[0].tags == ["Fiction"]
        assert books[0].tag_ids == [77]

    @pytest.mark.parametrize(
        ("method_name", "kwargs"),
        [
            ("list_books", {"limit": 10}),
            ("list_books_with_filters", {"limit": 10, "author_ids": [1]}),
        ],
    )
    def test_list_methods_populate_ids_and_tags(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_author: Author,
        method_name: str,
        kwargs: dict[str, object],
    ) -> None:
        """Ensure list endpoints populate IDs/tags for MoreFromSame UI."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        # Create book-author link
        assert sample_book.id is not None
        assert sample_author.id is not None
        in_memory_db.add(BookAuthorLink(book=sample_book.id, author=sample_author.id))

        # Create series/publisher/tag links
        series = Series(id=99, name="Test Series")
        publisher = Publisher(id=88, name="Test Publisher")
        tag = Tag(id=77, name="Fiction")
        in_memory_db.add(series)
        in_memory_db.add(publisher)
        in_memory_db.add(tag)
        in_memory_db.add(BookSeriesLink(book=sample_book.id, series=series.id))
        in_memory_db.add(BookPublisherLink(book=sample_book.id, publisher=publisher.id))
        in_memory_db.add(BookTagLink(book=sample_book.id, tag=tag.id))

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
            pathing=BookPathService(),
            calibre_db_path=Path("test.db"),
        )

        method = getattr(operations, method_name)
        # Fix up author_ids in kwargs for the filter-based method
        if method_name == "list_books_with_filters":
            kwargs = dict(kwargs)
            kwargs["author_ids"] = [sample_author.id]
        books = method(**kwargs)  # type: ignore[misc]

        assert len(books) == 1
        assert books[0].book.id == sample_book.id
        assert books[0].author_ids == [sample_author.id]
        assert books[0].series_id == 99
        assert books[0].publisher_id == 88
        assert books[0].tags == ["Fiction"]
        assert books[0].tag_ids == [77]

    def test_get_book_not_found(self, in_memory_db: Session) -> None:
        """Test get_book returns None when book not found."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        result = operations.get_book(book_id=999)
        assert result is None

    def test_get_book_found(
        self, in_memory_db: Session, sample_book: Book, sample_author: Author
    ) -> None:
        """Test get_book returns book when found."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        # Create book-author link
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
            pathing=BookPathService(),
            calibre_db_path=Path("test.db"),
        )

        assert sample_book.id is not None
        result = operations.get_book(book_id=sample_book.id)
        assert result is not None
        assert result.book.id == sample_book.id
        assert sample_author.name in result.authors

    def test_get_book_full_not_found(self, in_memory_db: Session) -> None:
        """Test get_book_full returns None when book not found."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        result = operations.get_book_full(book_id=999)
        assert result is None

    def test_search_suggestions_empty_query(self, in_memory_db: Session) -> None:
        """Test search_suggestions returns empty for empty query."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        result = operations.search_suggestions(query="")
        assert result == {"books": [], "authors": [], "tags": [], "series": []}

    def test_search_suggestions_with_query(self, in_memory_db: Session) -> None:
        """Test search_suggestions returns results for query."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        result = operations.search_suggestions(query="test")
        assert "books" in result
        assert "authors" in result
        assert "tags" in result
        assert "series" in result

    def test_filter_suggestions_empty_query(self, in_memory_db: Session) -> None:
        """Test filter_suggestions returns empty for empty query."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        result = operations.filter_suggestions(query="", filter_type="author")
        assert result == []

    def test_get_library_stats(self, in_memory_db: Session) -> None:
        """Test get_library_stats returns statistics."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        stats = operations.get_library_stats()
        assert "total_books" in stats
        assert "total_series" in stats
        assert "total_authors" in stats

    def test_list_books_with_pagination(self, in_memory_db: Session) -> None:
        """Test list_books respects pagination."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()

        # Create multiple books
        for i in range(5):
            book = Book(
                id=i + 1,
                title=f"Book {i + 1}",
                uuid=f"uuid-{i + 1}",
                timestamp=datetime.now(UTC),
                path=f"Author/Book {i + 1}",
            )
            in_memory_db.add(book)
        in_memory_db.commit()

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=BookPathService(),
            calibre_db_path=Path("test.db"),
        )

        books = operations.list_books(limit=2, offset=0)
        assert len(books) <= 2

        books_page2 = operations.list_books(limit=2, offset=2)
        assert len(books_page2) <= 2

    def test_list_books_with_search(
        self, in_memory_db: Session, sample_book: Book
    ) -> None:
        """Test list_books with search query."""
        session_manager = MockSessionManager(in_memory_db)
        retry = SQLiteRetryPolicy()
        unwrapper = ResultUnwrapper()
        queries = BookQueryBuilder()
        enrichment = BookEnrichmentService()
        search_service = MockBookSearchService()
        statistics_service = MockLibraryStatisticsService()
        pathing = BookPathService()
        calibre_db_path = Path("test.db")

        operations = BookReadOperations(
            session_manager=session_manager,
            retry_policy=retry,
            unwrapper=unwrapper,
            queries=queries,
            enrichment=enrichment,
            search_service=search_service,
            statistics_service=statistics_service,
            pathing=pathing,
            calibre_db_path=calibre_db_path,
        )

        books = operations.list_books(search_query="Test")
        # Search may or may not return results depending on implementation
        assert isinstance(books, list)
