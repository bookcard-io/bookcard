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

"""Tests for the refactored Calibre repository modules.

These tests intentionally target the refactored `bookcard.repositories.calibre`
package (facade + focused helpers) rather than legacy private helpers that were
removed during the split.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from bookcard.models.core import Book
from bookcard.repositories.calibre.queries import BookQueryBuilder
from bookcard.repositories.calibre.repository import CalibreBookRepository
from bookcard.repositories.calibre.unwrapping import ResultUnwrapper
from bookcard.repositories.interfaces import ISessionManager

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlmodel import Session


class FakeSessionManager(ISessionManager):
    """Test double for `ISessionManager`."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self.disposed = False

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        yield self._session

    def dispose(self) -> None:
        self.disposed = True


def test_result_unwrapper_unwrap_book_variants() -> None:
    unwrapper = ResultUnwrapper()
    book = Book(id=1, title="T", uuid="u")

    assert unwrapper.unwrap_book(book) == book
    assert unwrapper.unwrap_book((book, "series")) == book

    row_attr = MagicMock()
    row_attr.Book = book
    assert unwrapper.unwrap_book(row_attr) == book

    row_getitem = MagicMock()
    row_getitem.__getitem__.side_effect = lambda k: book if k == "Book" else None
    assert unwrapper.unwrap_book(row_getitem) == book


def test_result_unwrapper_unwrap_series_name_variants() -> None:
    unwrapper = ResultUnwrapper()
    book = Book(id=1, title="T", uuid="u")

    assert unwrapper.unwrap_series_name((book, "Series A")) == "Series A"

    row_attr = MagicMock()
    row_attr.series_name = "Series B"
    assert unwrapper.unwrap_series_name(row_attr) == "Series B"

    row_getitem = MagicMock()
    row_getitem.__getitem__.side_effect = lambda k: (
        "Series C" if k == "series_name" else None
    )
    assert unwrapper.unwrap_series_name(row_getitem) == "Series C"


def test_query_builder_get_sort_field() -> None:
    qb = BookQueryBuilder()
    assert qb.get_sort_field("random") is None
    assert qb.get_sort_field("timestamp") == Book.timestamp
    # Unknown keys fall back to timestamp
    assert qb.get_sort_field("does_not_exist") == Book.timestamp


def test_facade_get_book_uses_injected_session_manager() -> None:
    # Arrange a fake session that will return a fake row for the first .first() call,
    # then authors, formats, and lightweight list-level metadata (ids/tags).
    session = MagicMock()

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    row = MagicMock()
    row.Book = book
    row.series_name = "Series X"

    # Mock query results in call order:
    # - base book row
    # - authors
    # - formats
    # - list enrichment (single aggregated query)
    exec_base = MagicMock()
    exec_base.first.return_value = row

    exec_authors = MagicMock()
    exec_authors.all.return_value = ["Author 1"]

    exec_formats = MagicMock()
    exec_formats.all.return_value = [(1, "EPUB", 123, "name", "Author/Test Book (1)")]

    exec_list_enrich = MagicMock()
    exec_list_enrich.mappings.return_value.all.return_value = [
        {
            "book_id": 1,
            "tags_json": '[{"id": 77, "name": "Fiction"}]',
            "author_ids_json": "[11]",
            "identifiers_json": "[]",
            "languages_json": "[]",
            "publisher_name": "Publisher X",
            "publisher_id": 20,
            "rating_value": None,
            "rating_id": None,
            "series_id": 10,
            "description": None,
        }
    ]

    session.exec.side_effect = [exec_base, exec_authors, exec_formats, exec_list_enrich]

    repo = CalibreBookRepository(
        calibre_db_path="/tmp",
        session_manager=FakeSessionManager(session),
    )

    # Mock file existence check to return True
    with patch.object(repo._enrichment, "_validate_format_exists", return_value=True):
        result = repo.get_book(1)

        assert result is not None
        assert result.book.id == 1
        assert result.authors == ["Author 1"]
        assert result.author_ids == [11]
        assert result.series == "Series X"
        assert result.series_id == 10
        assert result.publisher == "Publisher X"
        assert result.publisher_id == 20
        assert result.tags == ["Fiction"]
        assert result.tag_ids == [77]
        assert result.formats == [{"format": "EPUB", "size": 123, "name": "name"}]
