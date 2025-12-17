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

"""Tests for metadata query to achieve 100% coverage."""

from __future__ import annotations

import pytest

from bookcard.services.ingest.metadata_query import MetadataQuery


@pytest.mark.parametrize(
    ("title", "authors", "isbn", "expected_valid"),
    [
        ("Test Book", None, None, True),
        (None, ["Author"], None, True),
        (None, None, "1234567890", True),
        ("Test Book", ["Author"], "1234567890", True),
        (None, None, None, False),
    ],
)
def test_is_valid(
    title: str | None,
    authors: list[str] | None,
    isbn: str | None,
    expected_valid: bool,
) -> None:
    """Test is_valid method with various parameter combinations."""
    query = MetadataQuery(title=title, authors=authors, isbn=isbn)
    assert query.is_valid() == expected_valid


@pytest.mark.parametrize(
    ("title", "authors", "isbn", "expected_string"),
    [
        ("Test Book", None, None, "Test Book"),
        (None, ["Author1", "Author2"], None, "Author1 Author2"),
        (None, None, "1234567890", "1234567890"),
        ("Test Book", ["Author"], "1234567890", "Test Book Author 1234567890"),
        (
            "Test Book",
            ["Author1", "Author2", "Author3"],
            None,
            "Test Book Author1 Author2",
        ),
        (None, None, None, None),
    ],
)
def test_build_search_string(
    title: str | None,
    authors: list[str] | None,
    isbn: str | None,
    expected_string: str | None,
) -> None:
    """Test build_search_string method with various parameter combinations."""
    query = MetadataQuery(
        title=title,
        authors=authors,
        isbn=isbn,
        locale="en",
        max_results_per_provider=10,
    )
    assert query.build_search_string() == expected_string


def test_metadata_query_defaults() -> None:
    """Test MetadataQuery default values."""
    query = MetadataQuery()
    assert query.title is None
    assert query.authors is None
    assert query.isbn is None
    assert query.locale == "en"
    assert query.max_results_per_provider == 10
