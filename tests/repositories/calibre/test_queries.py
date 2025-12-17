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

"""Tests for queries module."""

from __future__ import annotations

import pytest
from sqlmodel import Session, select

from bookcard.models.core import Book
from bookcard.repositories.calibre.queries import BookQueryBuilder


class TestBookQueryBuilder:
    """Test suite for BookQueryBuilder."""

    def test_get_sort_field_random(self) -> None:
        """Test get_sort_field returns None for random."""
        builder = BookQueryBuilder()
        assert builder.get_sort_field("random") is None

    def test_get_sort_field_timestamp(self) -> None:
        """Test get_sort_field returns timestamp field."""
        builder = BookQueryBuilder()
        assert builder.get_sort_field("timestamp") == Book.timestamp

    def test_get_sort_field_pubdate(self) -> None:
        """Test get_sort_field returns pubdate field."""
        builder = BookQueryBuilder()
        assert builder.get_sort_field("pubdate") == Book.pubdate

    def test_get_sort_field_title(self) -> None:
        """Test get_sort_field returns title field."""
        builder = BookQueryBuilder()
        assert builder.get_sort_field("title") == Book.title

    def test_get_sort_field_author_sort(self) -> None:
        """Test get_sort_field returns author_sort field."""
        builder = BookQueryBuilder()
        assert builder.get_sort_field("author_sort") == Book.author_sort

    def test_get_sort_field_series_index(self) -> None:
        """Test get_sort_field returns series_index field."""
        builder = BookQueryBuilder()
        assert builder.get_sort_field("series_index") == Book.series_index

    def test_get_sort_field_unknown_falls_back_to_timestamp(self) -> None:
        """Test get_sort_field falls back to timestamp for unknown field."""
        builder = BookQueryBuilder()
        assert builder.get_sort_field("unknown_field") == Book.timestamp

    def test_build_author_books_subquery_with_author_id(
        self, in_memory_db: Session
    ) -> None:
        """Test build_author_books_subquery with author_id."""
        builder = BookQueryBuilder()
        result = builder.build_author_books_subquery(in_memory_db, author_id=1)
        assert result is not None

    def test_build_author_books_subquery_without_author_id(
        self, in_memory_db: Session
    ) -> None:
        """Test build_author_books_subquery returns None without author_id."""
        builder = BookQueryBuilder()
        result = builder.build_author_books_subquery(in_memory_db, author_id=None)
        assert result is None

    def test_apply_pubdate_filter_with_month(self) -> None:
        """Test apply_pubdate_filter with month."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_pubdate_filter(stmt, pubdate_month=6, pubdate_day=None)
        assert result is not None

    def test_apply_pubdate_filter_with_day(self) -> None:
        """Test apply_pubdate_filter with day."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_pubdate_filter(stmt, pubdate_month=None, pubdate_day=15)
        assert result is not None

    def test_apply_pubdate_filter_with_both(self) -> None:
        """Test apply_pubdate_filter with both month and day."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_pubdate_filter(stmt, pubdate_month=6, pubdate_day=15)
        assert result is not None

    def test_apply_pubdate_filter_with_none(self) -> None:
        """Test apply_pubdate_filter returns original statement with None."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_pubdate_filter(
            stmt, pubdate_month=None, pubdate_day=None
        )
        assert result == stmt

    def test_build_list_base_stmt_without_search(self) -> None:
        """Test build_list_base_stmt without search query."""
        builder = BookQueryBuilder()
        stmt = builder.build_list_base_stmt(search_query=None)
        assert stmt is not None

    def test_build_list_base_stmt_with_search(self) -> None:
        """Test build_list_base_stmt with search query."""
        builder = BookQueryBuilder()
        stmt = builder.build_list_base_stmt(search_query="test")
        assert stmt is not None

    def test_build_list_base_stmt_with_exact_series_match(self) -> None:
        """Test build_list_base_stmt with exact series match."""
        builder = BookQueryBuilder()
        stmt = builder.build_list_base_stmt(search_query='series:"=Test Series"')
        assert stmt is not None

    def test_build_count_stmt_without_search(self) -> None:
        """Test build_count_stmt without search query."""
        builder = BookQueryBuilder()
        stmt = builder.build_count_stmt(search_query=None)
        assert stmt is not None

    def test_build_count_stmt_with_search(self) -> None:
        """Test build_count_stmt with search query."""
        builder = BookQueryBuilder()
        stmt = builder.build_count_stmt(search_query="test")
        assert stmt is not None

    def test_build_count_stmt_with_exact_series_match(self) -> None:
        """Test build_count_stmt with exact series match."""
        builder = BookQueryBuilder()
        stmt = builder.build_count_stmt(search_query='series:"=Test Series"')
        assert stmt is not None

    def test_apply_ordering_and_pagination_with_random(self) -> None:
        """Test apply_ordering_and_pagination with random sort."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_ordering_and_pagination(
            stmt, sort_field=None, sort_order="desc", limit=10, offset=0
        )
        assert result is not None

    def test_apply_ordering_and_pagination_with_desc(self) -> None:
        """Test apply_ordering_and_pagination with desc order."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_ordering_and_pagination(
            stmt,
            sort_field=Book.timestamp,
            sort_order="desc",
            limit=10,
            offset=0,
        )
        assert result is not None

    def test_apply_ordering_and_pagination_with_asc(self) -> None:
        """Test apply_ordering_and_pagination with asc order."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_ordering_and_pagination(
            stmt,
            sort_field=Book.timestamp,
            sort_order="asc",
            limit=10,
            offset=0,
        )
        assert result is not None

    def test_apply_ordering_and_pagination_with_limit_and_offset(self) -> None:
        """Test apply_ordering_and_pagination applies limit and offset."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_ordering_and_pagination(
            stmt,
            sort_field=Book.timestamp,
            sort_order="desc",
            limit=20,
            offset=10,
        )
        assert result is not None

    @pytest.mark.parametrize(
        ("sort_by", "expected_field"),
        [
            ("random", None),
            ("timestamp", Book.timestamp),
            ("pubdate", Book.pubdate),
            ("title", Book.title),
            ("author_sort", Book.author_sort),
            ("series_index", Book.series_index),
            ("unknown", Book.timestamp),  # Falls back to timestamp
        ],
    )
    def test_get_sort_field_parametrized(
        self, sort_by: str, expected_field: object | None
    ) -> None:
        """Test get_sort_field with various inputs (parametrized)."""
        builder = BookQueryBuilder()
        result = builder.get_sort_field(sort_by)
        assert result == expected_field

    @pytest.mark.parametrize(
        ("pubdate_month", "pubdate_day", "should_filter"),
        [
            (None, None, False),
            (6, None, True),
            (None, 15, True),
            (6, 15, True),
            (12, 31, True),
        ],
    )
    def test_apply_pubdate_filter_parametrized(
        self,
        pubdate_month: int | None,
        pubdate_day: int | None,
        should_filter: bool,
    ) -> None:
        """Test apply_pubdate_filter with various inputs (parametrized)."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_pubdate_filter(
            stmt, pubdate_month=pubdate_month, pubdate_day=pubdate_day
        )
        assert result is not None
        if not should_filter:
            assert result == stmt

    @pytest.mark.parametrize(
        ("sort_order", "limit", "offset"),
        [
            ("asc", 10, 0),
            ("desc", 10, 0),
            ("asc", 20, 10),
            ("desc", 50, 25),
        ],
    )
    def test_apply_ordering_and_pagination_parametrized(
        self, sort_order: str, limit: int, offset: int
    ) -> None:
        """Test apply_ordering_and_pagination with various inputs (parametrized)."""
        builder = BookQueryBuilder()
        stmt = select(Book)
        result = builder.apply_ordering_and_pagination(
            stmt,
            sort_field=Book.timestamp,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        assert result is not None
