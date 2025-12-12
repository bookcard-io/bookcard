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

"""Tests for unwrapping module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.models.core import Book
from fundamental.repositories.calibre.unwrapping import ResultUnwrapper


class TestResultUnwrapper:
    """Test suite for ResultUnwrapper."""

    def test_unwrap_book_from_book_instance(self) -> None:
        """Test unwrapping book from Book instance."""
        unwrapper = ResultUnwrapper()
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        result = unwrapper.unwrap_book(book)
        assert result is not None
        assert result == book
        assert result.id == 1
        assert result.title == "Test Book"

    def test_unwrap_book_from_tuple(self) -> None:
        """Test unwrapping book from tuple (indexable container)."""
        unwrapper = ResultUnwrapper()
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        result = unwrapper.unwrap_book((book, "Series Name"))
        assert result == book

    def test_unwrap_book_from_attr_access(self) -> None:
        """Test unwrapping book from object with Book attribute."""
        unwrapper = ResultUnwrapper()
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        row = MagicMock()
        row.Book = book
        result = unwrapper.unwrap_book(row)
        assert result == book

    def test_unwrap_book_from_getitem(self) -> None:
        """Test unwrapping book from object with __getitem__."""
        unwrapper = ResultUnwrapper()
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        row = MagicMock()
        row.__getitem__ = MagicMock(return_value=book)
        row.__getitem__.side_effect = lambda k: book if k == "Book" else None
        result = unwrapper.unwrap_book(row)
        assert result == book

    def test_unwrap_book_returns_none_for_invalid_input(self) -> None:
        """Test unwrapping book returns None for invalid input."""
        unwrapper = ResultUnwrapper()
        result = unwrapper.unwrap_book("not a book")
        assert result is None

    def test_unwrap_book_handles_index_error(self) -> None:
        """Test unwrapping book handles IndexError gracefully."""
        unwrapper = ResultUnwrapper()
        result = unwrapper.unwrap_book(())
        assert result is None

    def test_unwrap_series_name_from_tuple(self) -> None:
        """Test unwrapping series name from tuple."""
        unwrapper = ResultUnwrapper()
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        result = unwrapper.unwrap_series_name((book, "Series A"))
        assert result == "Series A"

    def test_unwrap_series_name_from_tuple_none(self) -> None:
        """Test unwrapping series name from tuple with None."""
        unwrapper = ResultUnwrapper()
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        result = unwrapper.unwrap_series_name((book, None))
        assert result is None

    def test_unwrap_series_name_from_attr_access(self) -> None:
        """Test unwrapping series name from object with series_name attribute."""
        unwrapper = ResultUnwrapper()
        row = MagicMock()
        row.series_name = "Series B"
        result = unwrapper.unwrap_series_name(row)
        assert result == "Series B"

    def test_unwrap_series_name_from_attr_access_none(self) -> None:
        """Test unwrapping series name from object with None series_name."""
        unwrapper = ResultUnwrapper()
        row = MagicMock()
        row.series_name = None
        result = unwrapper.unwrap_series_name(row)
        assert result is None

    def test_unwrap_series_name_from_getitem(self) -> None:
        """Test unwrapping series name from object with __getitem__."""
        unwrapper = ResultUnwrapper()
        row = MagicMock()
        row.__getitem__ = MagicMock(return_value="Series C")
        row.__getitem__.side_effect = (
            lambda k: "Series C" if k == "series_name" else None
        )
        result = unwrapper.unwrap_series_name(row)
        assert result == "Series C"

    def test_unwrap_series_name_from_getitem_none(self) -> None:
        """Test unwrapping series name from object with None value."""
        unwrapper = ResultUnwrapper()
        row = MagicMock()
        row.__getitem__ = MagicMock(return_value=None)
        row.__getitem__.side_effect = lambda k: None
        result = unwrapper.unwrap_series_name(row)
        assert result is None

    def test_unwrap_series_name_returns_none_for_invalid_input(self) -> None:
        """Test unwrapping series name returns None for invalid input."""
        unwrapper = ResultUnwrapper()
        # Strings are indexable, so unwrapper might return a character
        # Test with a non-indexable object instead
        result = unwrapper.unwrap_series_name(42)
        assert result is None

    def test_unwrap_book_from_getitem_no_getitem(self) -> None:
        """Test unwrap_book handles object without __getitem__."""
        unwrapper = ResultUnwrapper()

        # Object without __getitem__ attribute
        class NoGetItem:
            pass

        result = unwrapper.unwrap_book(NoGetItem())
        assert result is None

    def test_unwrap_series_name_handles_index_error(self) -> None:
        """Test unwrapping series name handles IndexError gracefully."""
        unwrapper = ResultUnwrapper()
        result = unwrapper.unwrap_series_name((Book(id=1, title="T", uuid="u"),))
        assert result is None

    @pytest.mark.parametrize(
        ("book_id", "title", "uuid"),
        [
            (1, "Book 1", "uuid-1"),
            (2, "Book 2", "uuid-2"),
            (999, "Long Title Book", "very-long-uuid-string"),
        ],
    )
    def test_unwrap_book_variants_parametrized(
        self, book_id: int, title: str, uuid: str
    ) -> None:
        """Test unwrapping book with various inputs (parametrized)."""
        unwrapper = ResultUnwrapper()
        book = Book(id=book_id, title=title, uuid=uuid)

        # Test all unwrapping strategies
        assert unwrapper.unwrap_book(book) == book
        assert unwrapper.unwrap_book((book, "Series")) == book

        row_attr = MagicMock()
        row_attr.Book = book
        assert unwrapper.unwrap_book(row_attr) == book

        row_getitem = MagicMock()
        row_getitem.__getitem__.side_effect = lambda k: book if k == "Book" else None
        assert unwrapper.unwrap_book(row_getitem) == book
