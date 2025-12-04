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

"""Tests for conversion exceptions to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.services.conversion.exceptions import (
    BookNotFoundError,
    ConversionError,
    ConverterNotAvailableError,
    FormatNotFoundError,
)


@pytest.mark.parametrize(
    ("book_id", "expected_message"),
    [
        (1, "Book 1 not found"),
        (42, "Book 42 not found"),
        (999, "Book 999 not found"),
    ],
)
def test_book_not_found_error_initialization(
    book_id: int,
    expected_message: str,
) -> None:
    """Test BookNotFoundError initialization and message.

    Parameters
    ----------
    book_id : int
        Book ID to test.
    expected_message : str
        Expected error message.
    """
    error = BookNotFoundError(book_id)

    assert error.book_id == book_id
    assert str(error) == expected_message
    assert isinstance(error, ConversionError)


@pytest.mark.parametrize(
    ("book_id", "format_name", "expected_message"),
    [
        (1, "MOBI", "Original format MOBI not found for book 1"),
        (42, "EPUB", "Original format EPUB not found for book 42"),
        (999, "AZW3", "Original format AZW3 not found for book 999"),
    ],
)
def test_format_not_found_error_initialization(
    book_id: int,
    format_name: str,
    expected_message: str,
) -> None:
    """Test FormatNotFoundError initialization and message.

    Parameters
    ----------
    book_id : int
        Book ID to test.
    format_name : str
        Format name to test.
    expected_message : str
        Expected error message.
    """
    error = FormatNotFoundError(book_id, format_name)

    assert error.book_id == book_id
    assert error.format == format_name
    assert str(error) == expected_message
    assert isinstance(error, ConversionError)


@pytest.mark.parametrize(
    "message",
    [
        "Calibre converter not found",
        "Converter path is invalid",
        "No converter available",
    ],
)
def test_converter_not_available_error_initialization(message: str) -> None:
    """Test ConverterNotAvailableError initialization and message.

    Parameters
    ----------
    message : str
        Error message to test.
    """
    error = ConverterNotAvailableError(message)

    assert str(error) == message
    assert isinstance(error, ConversionError)


def test_conversion_error_is_base_exception() -> None:
    """Test ConversionError is base exception class."""
    error = ConversionError("Test error")

    assert isinstance(error, Exception)
    assert str(error) == "Test error"
