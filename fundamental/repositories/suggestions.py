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

"""Filter suggestion strategies for autocomplete functionality.

This module implements the Strategy pattern for providing filter suggestions
based on user input. Each filter type has its own strategy that knows how to
query the database for matching suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func
from sqlmodel import Session, select

from fundamental.models.core import (
    Author,
    Book,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from fundamental.models.media import Data

if TYPE_CHECKING:
    from typing import ClassVar


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
