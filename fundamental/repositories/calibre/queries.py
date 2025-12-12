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

"""Query builder helpers for the Calibre book repository."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, overload

from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlmodel import select

from fundamental.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookSeriesLink,
    BookTagLink,
    Series,
    Tag,
)

if TYPE_CHECKING:
    from sqlalchemy.sql import Select, Subquery
    from sqlmodel import Session
    from sqlmodel.sql.expression import SelectOfScalar

logger = logging.getLogger(__name__)


class BookQueryBuilder:
    """Build SQL statements used by `CalibreBookRepository`."""

    def get_sort_field(self, sort_by: str) -> object | None:
        """Get sort field for query ordering.

        Parameters
        ----------
        sort_by : str
            Sort field name.

        Returns
        -------
        object | None
            SQLAlchemy column/function for sorting, or None for random sort.
        """
        valid_sort_fields = {
            "timestamp": Book.timestamp,
            "pubdate": Book.pubdate,
            "title": Book.title,
            "author_sort": Book.author_sort,
            "series_index": Book.series_index,
        }
        if sort_by == "random":
            return None
        return valid_sort_fields.get(sort_by, Book.timestamp)  # type: ignore[return-value]

    def build_author_books_subquery(
        self,
        session: Session,
        author_id: int | None,
    ) -> Subquery | None:
        """Build optional subquery for author filter."""
        if author_id is None:
            return None

        author_books_subquery: Subquery = (
            select(BookAuthorLink.book)
            .where(BookAuthorLink.author == author_id)
            .subquery()
        )
        author_book_count = session.exec(
            select(func.count()).select_from(author_books_subquery)
        ).one()
        logger.debug(
            "Author filter active: author_id=%s, linked_books=%s",
            author_id,
            author_book_count,
        )
        return author_books_subquery

    @overload
    def apply_pubdate_filter(
        self,
        stmt: Select,
        *,
        pubdate_month: int | None,
        pubdate_day: int | None,
    ) -> Select: ...

    @overload
    def apply_pubdate_filter(
        self,
        stmt: SelectOfScalar,
        *,
        pubdate_month: int | None,
        pubdate_day: int | None,
    ) -> SelectOfScalar: ...

    def apply_pubdate_filter(
        self,
        stmt: Select | SelectOfScalar,
        *,
        pubdate_month: int | None,
        pubdate_day: int | None,
    ) -> Select | SelectOfScalar:
        """Apply publication date filtering to a statement."""
        conditions = []
        if pubdate_month is not None:
            month_str = f"{pubdate_month:02d}"
            conditions.append(func.strftime("%m", Book.pubdate) == month_str)  # type: ignore[attr-defined]
        if pubdate_day is not None:
            day_str = f"{pubdate_day:02d}"
            conditions.append(func.strftime("%d", Book.pubdate) == day_str)  # type: ignore[attr-defined]

        if not conditions:
            return stmt

        combined_condition = Book.pubdate.isnot(None)  # type: ignore[attr-defined]
        for condition in conditions:
            combined_condition = combined_condition & condition  # type: ignore[assignment]
        return stmt.where(combined_condition)

    def build_list_base_stmt(self, *, search_query: str | None) -> Select:
        """Build base `list_books` statement with series join and optional search."""
        series_alias = aliased(Series)
        stmt = (
            select(Book, series_alias.name.label("series_name"))  # type: ignore[attr-defined]
            .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
            .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
        )
        return self._apply_search(
            stmt, series_alias=series_alias, search_query=search_query
        )

    def build_count_stmt(self, *, search_query: str | None) -> SelectOfScalar:
        """Build `count_books` statement with optional search."""
        if not search_query:
            return select(func.count(Book.id))

        # Exact series match
        if search_query.startswith('series:"=') and search_query.endswith('"'):
            series_name = search_query[9:-1]
            series_alias = aliased(Series)
            return (
                select(func.count(func.distinct(Book.id)))
                .join(BookSeriesLink, Book.id == BookSeriesLink.book)
                .join(series_alias, BookSeriesLink.series == series_alias.id)
                .where(series_alias.name == series_name)  # type: ignore[attr-defined]
            )

        query_lower = search_query.lower()
        pattern_lower = f"%{query_lower}%"
        author_alias = aliased(Author)
        tag_alias = aliased(Tag)
        series_alias = aliased(Series)

        return (
            select(func.count(func.distinct(Book.id)))
            .outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)
            .outerjoin(author_alias, BookAuthorLink.author == author_alias.id)
            .outerjoin(BookTagLink, Book.id == BookTagLink.book)
            .outerjoin(tag_alias, BookTagLink.tag == tag_alias.id)
            .outerjoin(BookSeriesLink, Book.id == BookSeriesLink.book)
            .outerjoin(series_alias, BookSeriesLink.series == series_alias.id)
            .where(
                (func.lower(Book.title).like(pattern_lower))  # type: ignore[attr-defined]
                | (func.lower(author_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                | (func.lower(tag_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
                | (func.lower(series_alias.name).like(pattern_lower))  # type: ignore[attr-defined]
            )
        )

    def apply_ordering_and_pagination(
        self,
        stmt: Select,
        *,
        sort_field: object | None,
        sort_order: str,
        limit: int,
        offset: int,
    ) -> Select:
        """Apply ordering and pagination to a statement."""
        if sort_field is None:
            stmt = stmt.order_by(func.random())  # type: ignore[attr-defined]
        elif sort_order == "desc":
            stmt = stmt.order_by(sort_field.desc())  # type: ignore[attr-defined]
        else:
            stmt = stmt.order_by(sort_field.asc())  # type: ignore[attr-defined]
        return stmt.limit(limit).offset(offset)

    def _apply_search(
        self, stmt: Select, *, series_alias: object, search_query: str | None
    ) -> Select:
        if not search_query:
            return stmt

        # Exact series match used by frontend series panel
        if search_query.startswith('series:"=') and search_query.endswith('"'):
            series_name = search_query[9:-1]
            return stmt.where(series_alias.name == series_name)  # type: ignore[attr-defined]

        query_lower = search_query.lower()
        pattern_lower = f"%{query_lower}%"
        author_alias = aliased(Author)
        tag_alias = aliased(Tag)

        return (
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
