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

"""Result unwrapping utilities.

SQLModel/SQLAlchemy row results can vary by query shape. This module centralizes
"unwrap Book" and "unwrap series name" behavior.
"""

from __future__ import annotations

from contextlib import suppress

from fundamental.models.core import Book


class ResultUnwrapper:
    """Helpers to normalize SQLAlchemy/SQLModel result row shapes."""

    def unwrap_book(self, result: object) -> Book | None:
        """Extract a `Book` instance from a query result."""
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

    def unwrap_series_name(self, result: object) -> str | None:
        """Extract a series name from a query result."""
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

    @staticmethod
    def _extract_book_from_book_instance(result: object) -> Book | None:
        if isinstance(result, Book):
            return result
        return None

    @staticmethod
    def _extract_book_from_indexable_container(result: object) -> Book | None:
        with suppress(TypeError, KeyError, AttributeError, IndexError):
            inner0 = result[0]  # type: ignore[index]
            if isinstance(inner0, Book):
                return inner0
        return None

    @staticmethod
    def _extract_book_from_attr(result: object) -> Book | None:
        with suppress(AttributeError, TypeError):
            book = result.Book  # type: ignore[attr-defined]
            if isinstance(book, Book):
                return book
        return None

    @staticmethod
    def _extract_book_from_getitem(result: object) -> Book | None:
        if not hasattr(result, "__getitem__"):
            return None
        with suppress(KeyError, TypeError, AttributeError):
            book = result["Book"]  # type: ignore[index, misc]
            if isinstance(book, Book):
                return book
        return None

    @staticmethod
    def _extract_series_name_from_indexable_container(result: object) -> str | None:
        with suppress(TypeError, KeyError, AttributeError, IndexError):
            inner1 = result[1]  # type: ignore[index]
            if isinstance(inner1, str):
                return inner1
            if inner1 is None:
                return None
        return None

    @staticmethod
    def _extract_series_name_from_attr(result: object) -> str | None:
        with suppress(AttributeError, TypeError):
            series_name = result.series_name  # type: ignore[attr-defined]
            if isinstance(series_name, str):
                return series_name
            if series_name is None:
                return None
        return None

    @staticmethod
    def _extract_series_name_from_getitem(result: object) -> str | None:
        if not hasattr(result, "__getitem__"):
            return None
        with suppress(KeyError, TypeError, AttributeError):
            series_name = result["series_name"]  # type: ignore[index, misc]
            if isinstance(series_name, str):
                return series_name
            if series_name is None:
                return None
        return None
