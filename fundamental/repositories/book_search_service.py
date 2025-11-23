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

"""Book search service for search functionality.

This module handles book search operations following SRP.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, select

from fundamental.models.core import Author, Book, Series, Tag
from fundamental.repositories.interfaces import IBookSearchService


class BookSearchService(IBookSearchService):
    """Service for searching books, authors, tags, and series.

    Handles search operations following SRP.
    """

    def search_suggestions(
        self,
        session: Session,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Search for suggestions across books, authors, tags, and series.

        Parameters
        ----------
        session : Session
            Database session.
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
            {"id": book_id, "name": book_title} for book_id, book_title in book_results
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
