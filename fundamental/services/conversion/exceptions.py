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

"""Custom exceptions for book format conversion.

Provides a consistent exception hierarchy for conversion operations,
following best practices for error handling.
"""


class ConversionError(Exception):
    """Base exception for conversion failures.

    All conversion-related exceptions inherit from this class,
    allowing callers to catch all conversion errors with a single
    exception type.
    """


class BookNotFoundError(ConversionError):
    """Raised when the book doesn't exist.

    Parameters
    ----------
    book_id : int
        The book ID that was not found.
    """

    def __init__(self, book_id: int) -> None:
        """Initialize BookNotFoundError.

        Parameters
        ----------
        book_id : int
            The book ID that was not found.
        """
        self.book_id = book_id
        super().__init__(f"Book {book_id} not found")


class FormatNotFoundError(ConversionError):
    """Raised when the source format doesn't exist.

    Parameters
    ----------
    book_id : int
        The book ID.
    format : str
        The format that was not found.
    """

    def __init__(self, book_id: int, format_name: str) -> None:
        """Initialize FormatNotFoundError.

        Parameters
        ----------
        book_id : int
            The book ID.
        format_name : str
            The format that was not found.
        """
        self.book_id = book_id
        self.format = format_name
        super().__init__(f"Original format {format_name} not found for book {book_id}")


class ConverterNotAvailableError(ConversionError):
    """Raised when no converter is available.

    Parameters
    ----------
    message : str
        Error message describing why converter is not available.
    """

    def __init__(self, message: str) -> None:
        """Initialize ConverterNotAvailableError.

        Parameters
        ----------
        message : str
            Error message describing why converter is not available.
        """
        super().__init__(message)
