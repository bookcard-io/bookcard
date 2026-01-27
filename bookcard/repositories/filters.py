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

"""Filter strategies for building book query filters.

This module implements the Strategy pattern for building filter conditions
on book queries. Each filter type has its own strategy class that knows how
to build the appropriate SQL conditions and joins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

from bookcard.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookTagLink,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from bookcard.models.media import Data
from bookcard.repositories.models import FilterContext

if TYPE_CHECKING:
    from sqlalchemy.sql import Select


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
            BookAuthorLink,
            Book.id == BookAuthorLink.book,  # type: ignore[invalid-argument-type]
        ).outerjoin(author_alias, BookAuthorLink.author == author_alias.id)  # type: ignore[invalid-argument-type]
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
            BookTagLink,
            Book.id == BookTagLink.book,  # type: ignore[invalid-argument-type]
        ).outerjoin(tag_alias, BookTagLink.tag == tag_alias.id)  # type: ignore[invalid-argument-type]
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
            BookPublisherLink,
            Book.id == BookPublisherLink.book,  # type: ignore[invalid-argument-type]
        ).outerjoin(publisher_alias, BookPublisherLink.publisher == publisher_alias.id)  # type: ignore[invalid-argument-type]
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
            identifier_alias,
            Book.id == identifier_alias.book,  # type: ignore[invalid-argument-type]
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
        context.stmt = context.stmt.outerjoin(data_alias, Book.id == data_alias.book)  # type: ignore[invalid-argument-type]
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
            BookRatingLink,
            Book.id == BookRatingLink.book,  # type: ignore[invalid-argument-type]
        ).outerjoin(rating_alias, BookRatingLink.rating == rating_alias.id)  # type: ignore[invalid-argument-type]
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
            BookLanguageLink,
            Book.id == BookLanguageLink.book,  # type: ignore[invalid-argument-type]
        ).outerjoin(language_alias, BookLanguageLink.lang_code == language_alias.id)  # type: ignore[invalid-argument-type]
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
