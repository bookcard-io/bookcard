# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Repository for querying Calibre SQLite database.

This repository connects directly to Calibre's metadata.db SQLite database
to query book information using SQLAlchemy ORM.
"""

from __future__ import annotations

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import aliased
from sqlmodel import Session, create_engine, select

from fundamental.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from fundamental.models.media import Data

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import ClassVar

    from sqlalchemy import Engine
    from sqlalchemy.sql import Select


@dataclass
class BookWithRelations:
    """Book with related author and series data.

    Attributes
    ----------
    book : Book
        Book instance.
    authors : list[str]
        List of author names.
    series : str | None
        Series name if part of a series.
    """

    book: Book
    authors: list[str]
    series: str | None


@dataclass
class FilterContext:
    """Context for building filter conditions.

    Attributes
    ----------
    stmt : Select
        SQLAlchemy select statement.
    or_conditions : list
        List of filter conditions to combine with OR (author, title, genre, etc.).
    and_conditions : list
        List of filter conditions to combine with AND (format, rating, language).
    """

    stmt: Select
    or_conditions: list
    and_conditions: list


class FilterStrategy:
    """Strategy interface for building filter conditions.

    Each filter type implements this interface to build its specific
    filter condition and join requirements.
    """

    def apply(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str] | None,
    ) -> FilterContext:
        """Apply filter condition to query context.

        Parameters
        ----------
        context : FilterContext
            Current query context with statement and conditions.
        filter_value : list[int] | list[str] | None
            Filter values to apply.

        Returns
        -------
        FilterContext
            Updated context with filter applied.
        """
        if not filter_value:
            return context
        return self._build_filter(context, filter_value)

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build specific filter condition.

        Parameters
        ----------
        context : FilterContext
            Current query context.
        filter_value : list[int] | list[str]
            Filter values.

        Returns
        -------
        FilterContext
            Updated context.
        """
        raise NotImplementedError


class AuthorFilterStrategy(FilterStrategy):
    """Strategy for filtering by author IDs (OR condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build author filter condition."""
        author_alias = aliased(Author)
        context.stmt = context.stmt.outerjoin(
            BookAuthorLink, Book.id == BookAuthorLink.book
        ).outerjoin(author_alias, BookAuthorLink.author == author_alias.id)
        context.or_conditions.append(author_alias.id.in_(filter_value))  # type: ignore[attr-defined]
        return context


class TitleFilterStrategy(FilterStrategy):
    """Strategy for filtering by book IDs (OR condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build title filter condition."""
        context.or_conditions.append(Book.id.in_(filter_value))  # type: ignore[attr-defined]
        return context


class GenreFilterStrategy(FilterStrategy):
    """Strategy for filtering by tag/genre IDs (OR condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build genre filter condition."""
        tag_alias = aliased(Tag)
        context.stmt = context.stmt.outerjoin(
            BookTagLink, Book.id == BookTagLink.book
        ).outerjoin(tag_alias, BookTagLink.tag == tag_alias.id)
        context.or_conditions.append(tag_alias.id.in_(filter_value))  # type: ignore[attr-defined]
        return context


class PublisherFilterStrategy(FilterStrategy):
    """Strategy for filtering by publisher IDs (OR condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build publisher filter condition."""
        publisher_alias = aliased(Publisher)
        context.stmt = context.stmt.outerjoin(
            BookPublisherLink, Book.id == BookPublisherLink.book
        ).outerjoin(publisher_alias, BookPublisherLink.publisher == publisher_alias.id)
        context.or_conditions.append(publisher_alias.id.in_(filter_value))  # type: ignore[attr-defined]
        return context


class IdentifierFilterStrategy(FilterStrategy):
    """Strategy for filtering by identifier IDs (OR condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build identifier filter condition."""
        identifier_alias = aliased(Identifier)
        context.stmt = context.stmt.outerjoin(
            identifier_alias, Book.id == identifier_alias.book
        )
        context.or_conditions.append(identifier_alias.id.in_(filter_value))  # type: ignore[attr-defined]
        return context


class SeriesFilterStrategy(FilterStrategy):
    """Strategy for filtering by series IDs (OR condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build series filter condition."""
        # Series alias should be provided via context if already joined
        # For now, we'll create a new alias if needed
        series_alias = aliased(Series)
        context.or_conditions.append(series_alias.id.in_(filter_value))  # type: ignore[attr-defined]
        return context


class FormatFilterStrategy(FilterStrategy):
    """Strategy for filtering by format strings (AND condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build format filter condition."""
        data_alias = aliased(Data)
        context.stmt = context.stmt.outerjoin(data_alias, Book.id == data_alias.book)
        context.and_conditions.append(data_alias.format.in_(filter_value))  # type: ignore[attr-defined]
        return context


class RatingFilterStrategy(FilterStrategy):
    """Strategy for filtering by rating IDs (AND condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build rating filter condition."""
        rating_alias = aliased(Rating)
        context.stmt = context.stmt.outerjoin(
            BookRatingLink, Book.id == BookRatingLink.book
        ).outerjoin(rating_alias, BookRatingLink.rating == rating_alias.id)
        context.and_conditions.append(rating_alias.id.in_(filter_value))  # type: ignore[attr-defined]
        return context


class LanguageFilterStrategy(FilterStrategy):
    """Strategy for filtering by language IDs (AND condition)."""

    def _build_filter(
        self,
        context: FilterContext,
        filter_value: list[int] | list[str],
    ) -> FilterContext:
        """Build language filter condition."""
        language_alias = aliased(Language)
        context.stmt = context.stmt.outerjoin(
            BookLanguageLink, Book.id == BookLanguageLink.book
        ).outerjoin(language_alias, BookLanguageLink.lang_code == language_alias.id)
        context.and_conditions.append(language_alias.id.in_(filter_value))  # type: ignore[attr-defined]
        return context


class FilterBuilder:
    """Builder for applying multiple filter strategies to a query.

    Uses Strategy pattern to apply different filter types while maintaining
    separation of concerns and single responsibility.
    """

    def __init__(self, base_stmt: Select) -> None:
        """Initialize filter builder with base query statement.

        Parameters
        ----------
        base_stmt : Select
            Base SQLAlchemy select statement.
        """
        self._context = FilterContext(
            stmt=base_stmt, or_conditions=[], and_conditions=[]
        )
        self._strategies: dict[str, FilterStrategy] = {
            "author": AuthorFilterStrategy(),
            "title": TitleFilterStrategy(),
            "genre": GenreFilterStrategy(),
            "publisher": PublisherFilterStrategy(),
            "identifier": IdentifierFilterStrategy(),
            "series": SeriesFilterStrategy(),
            "format": FormatFilterStrategy(),
            "rating": RatingFilterStrategy(),
            "language": LanguageFilterStrategy(),
        }

    def with_author_ids(self, author_ids: list[int] | None) -> FilterBuilder:
        """Add author filter.

        Parameters
        ----------
        author_ids : list[int] | None
            Author IDs to filter by.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        self._context = self._strategies["author"].apply(self._context, author_ids)
        return self

    def with_title_ids(self, title_ids: list[int] | None) -> FilterBuilder:
        """Add title filter.

        Parameters
        ----------
        title_ids : list[int] | None
            Book IDs to filter by.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        self._context = self._strategies["title"].apply(self._context, title_ids)
        return self

    def with_genre_ids(self, genre_ids: list[int] | None) -> FilterBuilder:
        """Add genre filter.

        Parameters
        ----------
        genre_ids : list[int] | None
            Tag IDs to filter by.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        self._context = self._strategies["genre"].apply(self._context, genre_ids)
        return self

    def with_publisher_ids(self, publisher_ids: list[int] | None) -> FilterBuilder:
        """Add publisher filter.

        Parameters
        ----------
        publisher_ids : list[int] | None
            Publisher IDs to filter by.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        self._context = self._strategies["publisher"].apply(
            self._context, publisher_ids
        )
        return self

    def with_identifier_ids(self, identifier_ids: list[int] | None) -> FilterBuilder:
        """Add identifier filter.

        Parameters
        ----------
        identifier_ids : list[int] | None
            Identifier IDs to filter by.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        self._context = self._strategies["identifier"].apply(
            self._context, identifier_ids
        )
        return self

    def with_series_ids(
        self, series_ids: list[int] | None, series_alias: object | None = None
    ) -> FilterBuilder:
        """Add series filter.

        Parameters
        ----------
        series_ids : list[int] | None
            Series IDs to filter by.
        series_alias : object | None
            Optional series alias if already joined.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        if series_ids and series_alias:
            # If series_alias is provided, use it directly in the condition
            self._context.or_conditions.append(series_alias.id.in_(series_ids))  # type: ignore[attr-defined]
        else:
            self._context = self._strategies["series"].apply(self._context, series_ids)
        return self

    def with_formats(self, formats: list[str] | None) -> FilterBuilder:
        """Add format filter.

        Parameters
        ----------
        formats : list[str] | None
            Format strings to filter by.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        self._context = self._strategies["format"].apply(self._context, formats)
        return self

    def with_rating_ids(self, rating_ids: list[int] | None) -> FilterBuilder:
        """Add rating filter.

        Parameters
        ----------
        rating_ids : list[int] | None
            Rating IDs to filter by.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        self._context = self._strategies["rating"].apply(self._context, rating_ids)
        return self

    def with_language_ids(self, language_ids: list[int] | None) -> FilterBuilder:
        """Add language filter.

        Parameters
        ----------
        language_ids : list[int] | None
            Language IDs to filter by.

        Returns
        -------
        FilterBuilder
            Self for method chaining.
        """
        self._context = self._strategies["language"].apply(self._context, language_ids)
        return self

    def build(self) -> Select:
        """Build final query with all filters applied.

        OR conditions (author, title, genre, publisher, identifier, series) are
        combined with OR. AND conditions (format, rating, language) are combined
        with AND. The two groups are then combined with AND:
        (OR_conditions) AND (AND_conditions)

        Returns
        -------
        Select
            SQLAlchemy select statement with filters applied.
        """
        stmt = self._context.stmt
        final_conditions = []

        # Combine OR conditions: (author OR title OR genre OR ...)
        if self._context.or_conditions:
            if len(self._context.or_conditions) == 1:
                final_conditions.append(self._context.or_conditions[0])
            else:
                final_conditions.append(or_(*self._context.or_conditions))

        # Combine AND conditions: (format AND rating AND language)
        if self._context.and_conditions:
            final_conditions.extend(self._context.and_conditions)

        # Apply all conditions: (OR_group) AND (AND_group)
        if final_conditions:
            stmt = stmt.where(and_(*final_conditions)).distinct()
        return stmt


class FilterSuggestionStrategy:
    """Strategy interface for filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get filter suggestions for a query.

        Parameters
        ----------
        session : Session
            Database session.
        query : str
            Search query string.
        limit : int
            Maximum number of suggestions.

        Returns
        -------
        list[dict[str, str | int]]
            List of suggestions with 'id' and 'name' fields.
        """
        raise NotImplementedError


class AuthorSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for author filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get author suggestions."""
        query_lower = query.strip().lower()
        pattern_lower = f"%{query_lower}%"
        stmt = (
            select(Author.id, Author.name)
            .where(func.lower(Author.name).like(pattern_lower))  # type: ignore[attr-defined]
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [
            {"id": author_id, "name": author_name} for author_id, author_name in results
        ]


class TitleSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for title filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get title suggestions."""
        query_lower = query.strip().lower()
        pattern_lower = f"%{query_lower}%"
        stmt = (
            select(Book.id, Book.title)
            .where(func.lower(Book.title).like(pattern_lower))  # type: ignore[attr-defined]
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [{"id": book_id, "name": book_title} for book_id, book_title in results]


class GenreSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for genre filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get genre suggestions."""
        query_lower = query.strip().lower()
        pattern_lower = f"%{query_lower}%"
        stmt = (
            select(Tag.id, Tag.name)
            .where(func.lower(Tag.name).like(pattern_lower))  # type: ignore[attr-defined]
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [{"id": tag_id, "name": tag_name} for tag_id, tag_name in results]


class PublisherSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for publisher filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get publisher suggestions."""
        query_lower = query.strip().lower()
        pattern_lower = f"%{query_lower}%"
        stmt = (
            select(Publisher.id, Publisher.name)
            .where(func.lower(Publisher.name).like(pattern_lower))  # type: ignore[attr-defined]
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [
            {"id": publisher_id, "name": publisher_name}
            for publisher_id, publisher_name in results
        ]


class IdentifierSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for identifier filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get identifier suggestions."""
        query_lower = query.strip().lower()
        pattern_lower = f"%{query_lower}%"
        stmt = (
            select(Identifier.id, Identifier.val, Identifier.type)
            .where(func.lower(Identifier.val).like(pattern_lower))  # type: ignore[attr-defined]
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [
            {
                "id": identifier_id,
                "name": f"{identifier_type}: {identifier_val}",
            }
            for identifier_id, identifier_val, identifier_type in results
        ]


class SeriesSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for series filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get series suggestions."""
        query_lower = query.strip().lower()
        pattern_lower = f"%{query_lower}%"
        stmt = (
            select(Series.id, Series.name)
            .where(func.lower(Series.name).like(pattern_lower))  # type: ignore[attr-defined]
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [
            {"id": series_id, "name": series_name} for series_id, series_name in results
        ]


class FormatSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for format filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get format suggestions."""
        query_lower = query.strip().lower()
        pattern_lower = f"%{query_lower}%"
        stmt = (
            select(Data.format)
            .where(func.lower(Data.format).like(pattern_lower))  # type: ignore[attr-defined]
            .distinct()
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [
            {"id": idx, "name": format_name}
            for idx, format_name in enumerate(results, start=1)
        ]


class RatingSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for rating filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get rating suggestions."""
        try:
            rating_query = int(query.strip())
            stmt = (
                select(Rating.id, Rating.rating)
                .where(Rating.rating == rating_query)  # type: ignore[attr-defined]
                .limit(limit)
            )
        except ValueError:
            stmt = (
                select(Rating.id, Rating.rating)
                .where(Rating.rating.isnot(None))  # type: ignore[attr-defined]
                .limit(limit)
            )
        results = session.exec(stmt).all()
        return [
            {"id": rating_id, "name": str(rating_value)}
            for rating_id, rating_value in results
            if rating_value is not None
        ]


class LanguageSuggestionStrategy(FilterSuggestionStrategy):
    """Strategy for language filter suggestions."""

    def get_suggestions(
        self, session: Session, query: str, limit: int
    ) -> list[dict[str, str | int]]:
        """Get language suggestions."""
        query_lower = query.strip().lower()
        pattern_lower = f"%{query_lower}%"
        stmt = (
            select(Language.id, Language.lang_code)
            .where(func.lower(Language.lang_code).like(pattern_lower))  # type: ignore[attr-defined]
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [{"id": lang_id, "name": lang_code} for lang_id, lang_code in results]


class FilterSuggestionFactory:
    """Factory for creating filter suggestion strategies.

    Uses Factory pattern to provide appropriate strategy based on filter type.
    """

    if TYPE_CHECKING:
        _strategies: ClassVar[dict[str, FilterSuggestionStrategy]]
    else:
        _strategies: dict[str, FilterSuggestionStrategy] = {
            "author": AuthorSuggestionStrategy(),
            "title": TitleSuggestionStrategy(),
            "genre": GenreSuggestionStrategy(),
            "publisher": PublisherSuggestionStrategy(),
            "identifier": IdentifierSuggestionStrategy(),
            "series": SeriesSuggestionStrategy(),
            "format": FormatSuggestionStrategy(),
            "rating": RatingSuggestionStrategy(),
            "language": LanguageSuggestionStrategy(),
        }

    @classmethod
    def get_strategy(cls, filter_type: str) -> FilterSuggestionStrategy | None:
        """Get suggestion strategy for filter type.

        Parameters
        ----------
        filter_type : str
            Type of filter.

        Returns
        -------
        FilterSuggestionStrategy | None
            Strategy instance or None if not found.
        """
        return cls._strategies.get(filter_type)


class CalibreBookRepository:
    """Repository for querying books from Calibre SQLite database.

    Parameters
    ----------
    calibre_db_path : str
        Path to Calibre library directory (contains metadata.db).
    calibre_db_file : str
        Calibre database filename (default: 'metadata.db').
    """

    def __init__(
        self,
        calibre_db_path: str,
        calibre_db_file: str = "metadata.db",
    ) -> None:
        self._calibre_db_path = Path(calibre_db_path)
        self._calibre_db_file = calibre_db_file
        self._db_path = self._calibre_db_path / self._calibre_db_file
        self._engine: Engine | None = None

    def _unwrap_book_from_result(self, result: object) -> Book | None:
        """Extract Book instance from query result using strategy pattern.

        Tries multiple extraction strategies in order until one succeeds.

        Parameters
        ----------
        result : object
            Query result which may be a Row, tuple, Book instance, or other.

        Returns
        -------
        Book | None
            Extracted Book instance or None if extraction fails.
        """
        strategies = [
            self._extract_book_from_book_instance,
            self._extract_book_from_indexable_container,
            self._extract_book_from_attr,
            self._extract_book_from_getitem,
        ]

        for strategy in strategies:
            book = strategy(result)
            if book is not None:
                return book
        return None

    def _extract_book_from_book_instance(self, result: object) -> Book | None:
        """Extract Book from Book instance."""
        if isinstance(result, Book):
            return result
        return None

    def _extract_book_from_indexable_container(self, result: object) -> Book | None:
        """Extract Book from indexable container (e.g., tuple, list, Row)."""
        with suppress(TypeError, KeyError, AttributeError, IndexError):
            inner0 = result[0]  # type: ignore[index]
            if isinstance(inner0, Book):
                return inner0
        return None

    def _extract_book_from_attr(self, result: object) -> Book | None:
        """Extract Book from object with 'Book' attribute (Row object)."""
        with suppress(AttributeError, TypeError):
            book = result.Book  # type: ignore[attr-defined]
            if isinstance(book, Book):
                return book
        return None

    def _extract_book_from_getitem(self, result: object) -> Book | None:
        """Extract Book from object supporting __getitem__ with 'Book' key."""
        if not hasattr(result, "__getitem__"):
            return None
        with suppress(KeyError, TypeError, AttributeError):
            book = result["Book"]  # type: ignore[index, misc]
            if isinstance(book, Book):
                return book
        return None

    def _unwrap_series_name_from_result(self, result: object) -> str | None:
        """Extract series name from query result using strategy pattern.

        Parameters
        ----------
        result : object
            Query result which may be a Row, tuple, or other.

        Returns
        -------
        str | None
            Extracted series name or None if extraction fails.
        """
        strategies = [
            self._extract_series_name_from_indexable_container,
            self._extract_series_name_from_attr,
            self._extract_series_name_from_getitem,
        ]

        for strategy in strategies:
            series_name = strategy(result)
            if series_name is not None:
                return series_name
        return None

    def _extract_series_name_from_indexable_container(
        self, result: object
    ) -> str | None:
        """Extract series name from indexable container (e.g., tuple, Row)."""
        with suppress(TypeError, KeyError, AttributeError, IndexError):
            inner1 = result[1]  # type: ignore[index]
            if isinstance(inner1, str):
                return inner1
            if inner1 is None:
                return None
        return None

    def _extract_series_name_from_attr(self, result: object) -> str | None:
        """Extract series name from object with 'series_name' attribute."""
        with suppress(AttributeError, TypeError):
            series_name = result.series_name  # type: ignore[attr-defined]
            if isinstance(series_name, str):
                return series_name
            if series_name is None:
                return None
        return None

    def _extract_series_name_from_getitem(self, result: object) -> str | None:
        """Extract series name from object supporting __getitem__."""
        if not hasattr(result, "__getitem__"):
            return None
        with suppress(KeyError, TypeError, AttributeError):
            series_name = result["series_name"]  # type: ignore[index, misc]
            if isinstance(series_name, str):
                return series_name
            if series_name is None:
                return None
        return None

    def _get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine for Calibre database.

        Returns
        -------
        Engine
            SQLAlchemy engine instance.

        Raises
        ------
        FileNotFoundError
            If Calibre database file does not exist.
        """
        if not self._db_path.exists():
            msg = f"Calibre database not found at {self._db_path}"
            raise FileNotFoundError(msg)
        if self._engine is None:
            db_url = f"sqlite:///{self._db_path}"
            self._engine = create_engine(db_url, echo=False, future=True)
        return self._engine

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """Get a SQLModel session for the Calibre database.

        Yields
        ------
        Session
            SQLModel session.
        """
        engine = self._get_engine()
        session = Session(engine)
        try:
            yield session
        finally:
            session.close()

    def count_books(self, search_query: str | None = None) -> int:
        """Count total number of books, optionally filtered by search.

        Parameters
        ----------
        search_query : str | None
            Optional search query to filter by title, author, or tag.

        Returns
        -------
        int
            Total number of books.
        """
        with self._get_session() as session:
            if search_query:
                # Use case-insensitive search for SQLite
                query_lower = search_query.lower()
                pattern_lower = f"%{query_lower}%"
                author_alias = aliased(Author)
                tag_alias = aliased(Tag)
                series_search_alias = aliased(Series)
                stmt = (
                    select(func.count(func.distinct(Book.id)))
                    .outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)
                    .outerjoin(author_alias, BookAuthorLink.author == author_alias.id)
                    .outerjoin(BookTagLink, Book.id == BookTagLink.book)
                    .outerjoin(tag_alias, BookTagLink.tag == tag_alias.id)
                    .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                    .outerjoin(
                        series_search_alias,
                        BookSeriesLink.series == series_search_alias.id,
                    )
                    .where(
                        (func.lower(Book.title).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(author_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(tag_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(series_search_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                    )
                )
            else:
                stmt = select(func.count(Book.id))
            result = session.exec(stmt).one()
            return result if result else 0

    def list_books(
        self,
        limit: int = 20,
        offset: int = 0,
        search_query: str | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> list[BookWithRelations]:
        """List books with pagination and optional search.

        Parameters
        ----------
        limit : int
            Maximum number of books to return.
        offset : int
            Number of books to skip.
        search_query : str | None
            Optional search query to filter by title or author.
        sort_by : str
            Field to sort by (default: 'timestamp').
        sort_order : str
            Sort order: 'asc' or 'desc' (default: 'desc').

        Returns
        -------
        list[BookWithRelations]
            List of books with authors and series.
        """
        # Validate sort_by to prevent SQL injection
        valid_sort_fields = {
            "timestamp": Book.timestamp,
            "pubdate": Book.pubdate,
            "title": Book.title,
            "author_sort": Book.author_sort,
            "series_index": Book.series_index,
        }
        sort_field = valid_sort_fields.get(sort_by, Book.timestamp)

        if sort_order.lower() not in {"asc", "desc"}:
            sort_order = "desc"

        with self._get_session() as session:
            # Build base query with series
            series_alias = aliased(Series)
            stmt = (
                select(Book, series_alias.name.label("series_name"))  # type: ignore[attr-defined]
                .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
            )

            # Add search filter if provided
            if search_query:
                # Use case-insensitive search for SQLite
                query_lower = search_query.lower()
                pattern_lower = f"%{query_lower}%"
                author_alias = aliased(Author)
                tag_alias = aliased(Tag)
                # Reuse the existing series_alias from the base query for search
                stmt = (
                    stmt.outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)
                    .outerjoin(author_alias, BookAuthorLink.author == author_alias.id)
                    .outerjoin(BookTagLink, Book.id == BookTagLink.book)
                    .outerjoin(tag_alias, BookTagLink.tag == tag_alias.id)
                    .distinct()
                    .where(
                        (func.lower(Book.title).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(author_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(tag_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                        | (func.lower(series_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                    )
                )

            # Add ordering
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_field.desc())  # type: ignore[attr-defined]
            else:
                stmt = stmt.order_by(sort_field.asc())  # type: ignore[attr-defined]

            # Add pagination
            stmt = stmt.limit(limit).offset(offset)

            # Execute query
            results = session.exec(stmt).all()

            books = []
            for result in results:
                book = self._unwrap_book_from_result(result)
                if book is None:
                    continue

                series_name = self._unwrap_series_name_from_result(result)

                # Get authors for this book
                if book.id is None:
                    continue

                authors_stmt = (
                    select(Author.name)
                    .join(BookAuthorLink, Author.id == BookAuthorLink.author)
                    .where(BookAuthorLink.book == book.id)
                    .order_by(BookAuthorLink.id)
                )
                authors = list(session.exec(authors_stmt).all())

                books.append(
                    BookWithRelations(
                        book=book,
                        authors=authors,
                        series=series_name,
                    )
                )

            return books

    def _build_book_with_relations(
        self, session: Session, result: object
    ) -> BookWithRelations | None:
        """Build BookWithRelations from query result.

        Parameters
        ----------
        session : Session
            Database session.
        result : object
            Query result.

        Returns
        -------
        BookWithRelations | None
            Book with relations or None if extraction fails.
        """
        book = self._unwrap_book_from_result(result)
        if book is None or book.id is None:
            return None

        series_name = self._unwrap_series_name_from_result(result)

        authors_stmt = (
            select(Author.name)
            .join(BookAuthorLink, Author.id == BookAuthorLink.author)
            .where(BookAuthorLink.book == book.id)
            .order_by(BookAuthorLink.id)
        )
        authors = list(session.exec(authors_stmt).all())

        return BookWithRelations(
            book=book,
            authors=authors,
            series=series_name,
        )

    def _get_sort_field(self, sort_by: str) -> object:
        """Get sort field for query ordering.

        Parameters
        ----------
        sort_by : str
            Sort field name.

        Returns
        -------
        object
            SQLAlchemy column field for sorting.
        """
        valid_sort_fields = {
            "timestamp": Book.timestamp,
            "pubdate": Book.pubdate,
            "title": Book.title,
            "author_sort": Book.author_sort,
            "series_index": Book.series_index,
        }
        return valid_sort_fields.get(sort_by, Book.timestamp)  # type: ignore[return-value]

    def list_books_with_filters(
        self,
        limit: int = 20,
        offset: int = 0,
        author_ids: list[int] | None = None,
        title_ids: list[int] | None = None,
        genre_ids: list[int] | None = None,
        publisher_ids: list[int] | None = None,
        identifier_ids: list[int] | None = None,
        series_ids: list[int] | None = None,
        formats: list[str] | None = None,
        rating_ids: list[int] | None = None,
        language_ids: list[int] | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> list[BookWithRelations]:
        """List books with multiple filter criteria using OR conditions.

        Each filter type uses OR conditions (e.g., multiple authors = OR).
        Different filter types are combined with AND conditions.

        Parameters
        ----------
        limit : int
            Maximum number of books to return.
        offset : int
            Number of books to skip.
        author_ids : list[int] | None
            List of author IDs to filter by (OR condition).
        title_ids : list[int] | None
            List of book IDs to filter by (OR condition).
        genre_ids : list[int] | None
            List of tag IDs to filter by (OR condition).
        publisher_ids : list[int] | None
            List of publisher IDs to filter by (OR condition).
        identifier_ids : list[int] | None
            List of identifier IDs to filter by (OR condition).
        series_ids : list[int] | None
            List of series IDs to filter by (OR condition).
        formats : list[str] | None
            List of format strings to filter by (OR condition).
        rating_ids : list[int] | None
            List of rating IDs to filter by (OR condition).
        language_ids : list[int] | None
            List of language IDs to filter by (OR condition).
        sort_by : str
            Field to sort by (default: 'timestamp').
        sort_order : str
            Sort order: 'asc' or 'desc' (default: 'desc').

        Returns
        -------
        list[BookWithRelations]
            List of books with authors and series.
        """
        sort_field = self._get_sort_field(sort_by)
        if sort_order.lower() not in {"asc", "desc"}:
            sort_order = "desc"

        with self._get_session() as session:
            series_alias = aliased(Series)
            base_stmt = (
                select(Book, series_alias.name.label("series_name"))  # type: ignore[attr-defined]
                .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
            )

            stmt = (
                FilterBuilder(base_stmt)
                .with_author_ids(author_ids)
                .with_title_ids(title_ids)
                .with_genre_ids(genre_ids)
                .with_publisher_ids(publisher_ids)
                .with_identifier_ids(identifier_ids)
                .with_series_ids(series_ids, series_alias)
                .with_formats(formats)
                .with_rating_ids(rating_ids)
                .with_language_ids(language_ids)
                .build()
            )

            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_field.desc())  # type: ignore[attr-defined]
            else:
                stmt = stmt.order_by(sort_field.asc())  # type: ignore[attr-defined]

            stmt = stmt.limit(limit).offset(offset)
            results = session.exec(stmt).all()

            books = []
            for result in results:
                book_with_rels = self._build_book_with_relations(session, result)
                if book_with_rels:
                    books.append(book_with_rels)

            return books

    def count_books_with_filters(
        self,
        author_ids: list[int] | None = None,
        title_ids: list[int] | None = None,
        genre_ids: list[int] | None = None,
        publisher_ids: list[int] | None = None,
        identifier_ids: list[int] | None = None,
        series_ids: list[int] | None = None,
        formats: list[str] | None = None,
        rating_ids: list[int] | None = None,
        language_ids: list[int] | None = None,
    ) -> int:
        """Count books matching filter criteria.

        Parameters
        ----------
        author_ids : list[int] | None
            List of author IDs to filter by (OR condition).
        title_ids : list[int] | None
            List of book IDs to filter by (OR condition).
        genre_ids : list[int] | None
            List of tag IDs to filter by (OR condition).
        publisher_ids : list[int] | None
            List of publisher IDs to filter by (OR condition).
        identifier_ids : list[int] | None
            List of identifier IDs to filter by (OR condition).
        series_ids : list[int] | None
            List of series IDs to filter by (OR condition).
        formats : list[str] | None
            List of format strings to filter by (OR condition).
        rating_ids : list[int] | None
            List of rating IDs to filter by (OR condition).
        language_ids : list[int] | None
            List of language IDs to filter by (OR condition).

        Returns
        -------
        int
            Total number of books matching the filters.
        """
        with self._get_session() as session:
            series_alias = aliased(Series)
            base_stmt = (
                select(func.count(func.distinct(Book.id)))
                .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
            )

            stmt = (
                FilterBuilder(base_stmt)
                .with_author_ids(author_ids)
                .with_title_ids(title_ids)
                .with_genre_ids(genre_ids)
                .with_publisher_ids(publisher_ids)
                .with_identifier_ids(identifier_ids)
                .with_series_ids(series_ids, series_alias)
                .with_formats(formats)
                .with_rating_ids(rating_ids)
                .with_language_ids(language_ids)
                .build()
            )

            result = session.exec(stmt).one()
            return result if result else 0

    def get_book(self, book_id: int) -> BookWithRelations | None:
        """Get a book by ID.

        Parameters
        ----------
        book_id : int
            Calibre book ID.

        Returns
        -------
        BookWithRelations | None
            Book with authors and series if found, None otherwise.
        """
        with self._get_session() as session:
            series_alias = aliased(Series)
            stmt = (
                select(Book, series_alias.name.label("series_name"))  # type: ignore[attr-defined]
                .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
                .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
                .where(Book.id == book_id)
            )
            result = session.exec(stmt).first()

            if result is None:
                return None

            book = self._unwrap_book_from_result(result)
            if book is None:
                return None

            series_name = self._unwrap_series_name_from_result(result)

            # Get authors for this book
            authors_stmt = (
                select(Author.name)
                .join(BookAuthorLink, Author.id == BookAuthorLink.author)
                .where(BookAuthorLink.book == book_id)
                .order_by(BookAuthorLink.id)
            )
            authors = list(session.exec(authors_stmt).all())

            return BookWithRelations(
                book=book,
                authors=authors,
                series=series_name,
            )

    def search_suggestions(
        self,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Search for suggestions across books, authors, tags, and series.

        Parameters
        ----------
        query : str
            Search query string.
        book_limit : int
            Maximum number of book matches to return (default: 3).
        author_limit : int
            Maximum number of author matches to return (default: 3).
        tag_limit : int
            Maximum number of tag matches to return (default: 3).
        series_limit : int
            Maximum number of series matches to return (default: 3).

        Returns
        -------
        dict[str, list[dict[str, str | int]]]
            Dictionary with keys 'books', 'authors', 'tags', 'series', each
            containing a list of matches with 'name' and 'id' fields.
        """
        if not query or not query.strip():
            return {"books": [], "authors": [], "tags": [], "series": []}

        results = {
            "books": [],
            "authors": [],
            "tags": [],
            "series": [],
        }

        with self._get_session() as session:
            # Use func.lower for case-insensitive search in SQLite
            query_lower = query.strip().lower()
            pattern_lower = f"%{query_lower}%"

            # Search books by title
            book_stmt = (
                select(Book.id, Book.title)
                .where(func.lower(Book.title).like(pattern_lower))  # type: ignore[attr-defined]
                .limit(book_limit)
            )
            book_results = session.exec(book_stmt).all()
            results["books"] = [
                {"id": book_id, "name": book_title}
                for book_id, book_title in book_results
            ]

            # Search authors
            author_stmt = (
                select(Author.id, Author.name)
                .where(func.lower(Author.name).like(pattern_lower))  # type: ignore[attr-defined]
                .limit(author_limit)
            )
            author_results = session.exec(author_stmt).all()
            results["authors"] = [
                {"id": author_id, "name": author_name}
                for author_id, author_name in author_results
            ]

            # Search tags
            tag_stmt = (
                select(Tag.id, Tag.name)
                .where(func.lower(Tag.name).like(pattern_lower))  # type: ignore[attr-defined]
                .limit(tag_limit)
            )
            tag_results = session.exec(tag_stmt).all()
            results["tags"] = [
                {"id": tag_id, "name": tag_name} for tag_id, tag_name in tag_results
            ]

            # Search series
            series_stmt = (
                select(Series.id, Series.name)
                .where(func.lower(Series.name).like(pattern_lower))  # type: ignore[attr-defined]
                .limit(series_limit)
            )
            series_results = session.exec(series_stmt).all()
            results["series"] = [
                {"id": series_id, "name": series_name}
                for series_id, series_name in series_results
            ]

        return results

    def filter_suggestions(
        self,
        query: str,
        filter_type: str,
        limit: int = 10,
    ) -> list[dict[str, str | int]]:
        """Get filter suggestions for a specific filter type.

        Parameters
        ----------
        query : str
            Search query string.
        filter_type : str
            Type of filter: 'author', 'title', 'genre', 'publisher',
            'identifier', 'series', 'format', 'rating', 'language'.
        limit : int
            Maximum number of suggestions to return (default: 10).

        Returns
        -------
        list[dict[str, str | int]]
            List of suggestions with 'id' and 'name' fields.
        """
        if not query or not query.strip():
            return []

        strategy = FilterSuggestionFactory.get_strategy(filter_type)
        if strategy is None:
            return []

        with self._get_session() as session:
            return strategy.get_suggestions(session, query, limit)

    @staticmethod
    def _parse_datetime(value: str | float | None) -> datetime | None:
        """Parse Calibre datetime value.

        Calibre stores timestamps as Unix timestamps (seconds since epoch)
        or as ISO format strings, or None.

        Parameters
        ----------
        value : str | float | None
            Timestamp value (Unix timestamp or ISO string) or None.

        Returns
        -------
        datetime | None
            Parsed datetime or None.
        """
        if value is None:
            return None
        try:
            # Try parsing as Unix timestamp (float/int)
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value, tz=UTC)
            # Try parsing as ISO string
            if isinstance(value, str):
                # Remove timezone info if present and try ISO format
                value_clean = value.replace("Z", "+00:00")
                try:
                    return datetime.fromisoformat(value_clean)
                except ValueError:
                    # Try parsing as Unix timestamp string
                    try:
                        return datetime.fromtimestamp(float(value_clean), tz=UTC)
                    except (ValueError, TypeError):
                        return None
            else:
                return None
        except (ValueError, AttributeError, OSError):
            return None
