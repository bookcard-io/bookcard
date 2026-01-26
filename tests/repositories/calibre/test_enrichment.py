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

"""Tests for enrichment module."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from bookcard.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from bookcard.models.media import Data
from bookcard.repositories.calibre.enrichment import BookEnrichmentService
from bookcard.repositories.models import BookWithRelations

if TYPE_CHECKING:
    from sqlmodel import Session


class TestBookEnrichmentService:
    """Test suite for BookEnrichmentService."""

    def test_enrich_books_with_full_details_empty_list(
        self, in_memory_db: Session
    ) -> None:
        """Test enrich_books_with_full_details with empty list."""
        service = BookEnrichmentService()
        result = service.enrich_books_with_full_details(in_memory_db, [])
        assert result == []

    def test_enrich_books_with_full_details_no_book_ids(
        self, in_memory_db: Session
    ) -> None:
        """Test enrich_books_with_full_details with books without ids."""
        service = BookEnrichmentService()
        book = Book(id=None, title="Test", uuid="test", timestamp=datetime.now(UTC))
        book_with_relations = BookWithRelations(
            book=book, authors=[], series=None, formats=[]
        )
        result = service.enrich_books_with_full_details(
            in_memory_db, [book_with_relations]
        )
        assert result == []

    def test_enrich_books_with_full_details_single_book(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_author: Author,
        sample_tag: Tag,
        sample_series: Series,
        sample_publisher: Publisher,
        sample_language: Language,
        sample_rating: Rating,
    ) -> None:
        """Test enrich_books_with_full_details with single book."""
        service = BookEnrichmentService()

        # Create relationships
        in_memory_db.add(BookAuthorLink(book=sample_book.id, author=sample_author.id))
        in_memory_db.add(BookTagLink(book=sample_book.id, tag=sample_tag.id))
        in_memory_db.add(BookSeriesLink(book=sample_book.id, series=sample_series.id))
        in_memory_db.add(
            BookPublisherLink(book=sample_book.id, publisher=sample_publisher.id)
        )
        in_memory_db.add(
            BookLanguageLink(book=sample_book.id, lang_code=sample_language.id)
        )
        in_memory_db.add(BookRatingLink(book=sample_book.id, rating=sample_rating.id))
        in_memory_db.add(Comment(book=sample_book.id, text="Test description"))
        in_memory_db.add(Identifier(book=sample_book.id, type="isbn", val="1234567890"))
        in_memory_db.add(
            Data(
                book=sample_book.id,
                format="EPUB",
                uncompressed_size=1000,
                name="Test Book",
            )
        )
        in_memory_db.commit()

        book_with_relations = BookWithRelations(
            book=sample_book,
            authors=[sample_author.name],
            series=sample_series.name,
            formats=[],
        )

        result = service.enrich_books_with_full_details(
            in_memory_db, [book_with_relations]
        )

        assert len(result) == 1
        enriched = result[0]
        assert enriched.book == sample_book
        assert sample_author.name in enriched.authors
        assert enriched.series == sample_series.name
        assert len(enriched.tags) > 0
        assert len(enriched.identifiers) > 0
        assert enriched.description == "Test description"
        assert enriched.publisher == sample_publisher.name
        assert len(enriched.languages) > 0
        assert enriched.rating == sample_rating.rating
        assert len(enriched.formats) > 0

    def test_fetch_formats_map(self, in_memory_db: Session, sample_book: Book) -> None:
        """Test fetch_formats_map."""
        service = BookEnrichmentService()
        in_memory_db.add(
            Data(
                book=sample_book.id,
                format="EPUB",
                uncompressed_size=1000,
                name="Test Book",
            )
        )
        in_memory_db.add(
            Data(
                book=sample_book.id,
                format="PDF",
                uncompressed_size=2000,
                name="Test Book",
            )
        )
        in_memory_db.commit()

        assert sample_book.id is not None
        result = service.fetch_formats_map(in_memory_db, [sample_book.id])
        assert sample_book.id in result
        assert len(result[sample_book.id]) == 2
        formats = result[sample_book.id]
        assert any(f["format"] == "EPUB" for f in formats)
        assert any(f["format"] == "PDF" for f in formats)

    def test_enrich_books_with_full_details_multiple_books(
        self, in_memory_db: Session
    ) -> None:
        """Test enrich_books_with_full_details with multiple books."""
        service = BookEnrichmentService()

        # Create multiple books
        book1 = Book(
            id=1,
            title="Book 1",
            uuid="uuid-1",
            timestamp=datetime.now(UTC),
            path="Author/Book 1",
        )
        book2 = Book(
            id=2,
            title="Book 2",
            uuid="uuid-2",
            timestamp=datetime.now(UTC),
            path="Author/Book 2",
        )
        in_memory_db.add(book1)
        in_memory_db.add(book2)
        in_memory_db.commit()

        book_with_relations1 = BookWithRelations(
            book=book1, authors=["Author"], series=None, formats=[]
        )
        book_with_relations2 = BookWithRelations(
            book=book2, authors=["Author"], series=None, formats=[]
        )

        result = service.enrich_books_with_full_details(
            in_memory_db, [book_with_relations1, book_with_relations2]
        )

        assert len(result) == 2
        assert result[0].book.id == 1
        assert result[1].book.id == 2

    def test_enrich_books_with_full_details_skips_books_without_id(
        self, in_memory_db: Session
    ) -> None:
        """Test enrich_books_with_full_details skips books without id."""
        service = BookEnrichmentService()
        book = Book(id=None, title="Test", uuid="test", timestamp=datetime.now(UTC))
        book_with_relations = BookWithRelations(
            book=book, authors=[], series=None, formats=[]
        )
        result = service.enrich_books_with_full_details(
            in_memory_db, [book_with_relations]
        )
        assert result == []
