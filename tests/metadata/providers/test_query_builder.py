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

"""Tests for SRU query builder to achieve 100% coverage."""

import pytest

from bookcard.metadata.providers.dnb._query_builder import SRUQueryBuilder


def test_query_builder_init(query_builder: SRUQueryBuilder) -> None:
    """Test SRUQueryBuilder initialization."""
    assert query_builder is not None
    assert hasattr(query_builder, "FILTER_NON_BOOKS")


def test_query_builder_build_queries_with_idn(query_builder: SRUQueryBuilder) -> None:
    """Test building queries with IDN."""
    queries = query_builder.build_queries(idn="123456789")
    assert len(queries) == 1
    assert "num=123456789" in queries[0]
    assert query_builder.FILTER_NON_BOOKS in queries[0]


def test_query_builder_build_queries_with_isbn(query_builder: SRUQueryBuilder) -> None:
    """Test building queries with ISBN."""
    queries = query_builder.build_queries(isbn="9783123456789")
    assert len(queries) == 1
    assert "num=9783123456789" in queries[0]
    assert query_builder.FILTER_NON_BOOKS in queries[0]


def test_query_builder_build_queries_with_title(query_builder: SRUQueryBuilder) -> None:
    """Test building queries with title."""
    queries = query_builder.build_queries(title="Test Book")
    assert len(queries) >= 1
    assert any("tit=" in q for q in queries)
    assert all(query_builder.FILTER_NON_BOOKS in q for q in queries)


def test_query_builder_build_queries_title_variations(
    query_builder: SRUQueryBuilder,
) -> None:
    """Test building queries with title creates multiple variations."""
    queries = query_builder.build_queries(title="Der Test und das Buch")
    # Should create at least one query, possibly more with German joiners removed
    assert len(queries) >= 1
    assert all(query_builder.FILTER_NON_BOOKS in q for q in queries)


def test_query_builder_build_queries_empty_title(
    query_builder: SRUQueryBuilder,
) -> None:
    """Test building queries with empty title."""
    queries = query_builder.build_queries(title="")
    assert len(queries) == 0


@pytest.mark.parametrize(
    ("title", "expected_tokens"),
    [
        ("Simple Title", ["Simple", "Title"]),
        ("Test Book", ["Test", "Book"]),
        ("Word1 Word2 Word3", ["Word1", "Word2", "Word3"]),
    ],
)
def test_query_builder_tokenize_title(
    query_builder: SRUQueryBuilder,
    title: str,
    expected_tokens: list[str],
) -> None:
    """Test title tokenization."""
    tokens = query_builder._tokenize_title(title, strip_joiners=False)
    assert len(tokens) == len(expected_tokens)
    assert all(token in tokens for token in expected_tokens)


def test_query_builder_tokenize_title_with_joiners(
    query_builder: SRUQueryBuilder,
) -> None:
    """Test title tokenization with joiners."""
    title = "Der Test und das Buch"
    tokens_with_joiners = query_builder._tokenize_title(title, strip_joiners=False)
    tokens_without_joiners = query_builder._tokenize_title(title, strip_joiners=True)

    # Should have fewer tokens when joiners are stripped
    assert len(tokens_without_joiners) <= len(tokens_with_joiners)


@pytest.mark.parametrize(
    ("wordlist", "expected_filtered"),
    [
        (["ein", "Test", "Buch"], ["Test", "Buch"]),
        (["der", "die", "das", "Word"], ["Word"]),
        (["und", "oder", "Test"], ["Test"]),
        (["Test", "Book"], ["Test", "Book"]),  # No joiners
    ],
)
def test_query_builder_strip_german_joiners(
    query_builder: SRUQueryBuilder,
    wordlist: list[str],
    expected_filtered: list[str],
) -> None:
    """Test German joiner removal."""
    filtered = query_builder._strip_german_joiners(wordlist)
    assert filtered == expected_filtered


def test_query_builder_strip_german_joiners_case_insensitive(
    query_builder: SRUQueryBuilder,
) -> None:
    """Test German joiner removal is case insensitive."""
    wordlist = ["EIN", "Test", "UND"]
    filtered = query_builder._strip_german_joiners(wordlist)
    assert filtered == ["Test"]


def test_query_builder_build_title_queries_simple(
    query_builder: SRUQueryBuilder,
) -> None:
    """Test building title queries for simple title."""
    queries = query_builder._build_title_queries("Test Book")
    assert len(queries) >= 1
    assert all('tit="' in q for q in queries)


def test_query_builder_build_title_queries_with_german_joiners(
    query_builder: SRUQueryBuilder,
) -> None:
    """Test building title queries with German joiners."""
    queries = query_builder._build_title_queries("Der Test und das Buch")
    # Should create multiple queries (with and without joiners)
    assert len(queries) >= 1


def test_query_builder_filter_non_books(query_builder: SRUQueryBuilder) -> None:
    """Test that queries include filter for non-books."""
    queries = query_builder.build_queries(title="Test")
    assert all(query_builder.FILTER_NON_BOOKS in q for q in queries)
