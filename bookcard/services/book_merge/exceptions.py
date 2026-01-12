# Copyright (C) 2026 knguyen and others
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

"""Domain exceptions for book merge operations."""


class BookMergeError(Exception):
    """Base exception for book merge operations."""


class InsufficientBooksError(BookMergeError):
    """Raised when insufficient books provided for merge."""


class BookNotFoundError(BookMergeError):
    """Raised when book not found."""

    def __init__(self, book_id: int) -> None:
        self.book_id = book_id
        super().__init__(f"Book not found: {book_id}")


class InvalidKeepBookError(BookMergeError):
    """Raised when keep_book_id not in merge set."""


class DuplicateBookIdsError(BookMergeError):
    """Raised when duplicate book IDs are provided."""
