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

"""Tests for filename utilities to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.repositories.filename_utils import (
    calculate_book_path,
    sanitize_filename,
)


@pytest.mark.parametrize(
    ("name", "max_length", "expected"),
    [
        ("normal_name", 96, "normal_name"),
        ("name<>with|invalid*chars", 96, "name__with_invalid_chars"),
        ("short", 96, "short"),
        ("a" * 200, 96, "a" * 96),  # Truncation (covers line 41)
        ("", 96, "Unknown"),
        ("   ", 96, "Unknown"),
    ],
)
def test_sanitize_filename(name: str, max_length: int, expected: str) -> None:
    """Test sanitize_filename (covers lines 23-42, including line 41)."""
    result = sanitize_filename(name, max_length)
    assert result == expected


def test_sanitize_filename_truncation() -> None:
    """Test sanitize_filename truncates long names (covers line 41)."""
    long_name = "a" * 150
    result = sanitize_filename(long_name, max_length=50)
    assert len(result) == 50
    assert result == "a" * 50


@pytest.mark.parametrize(
    ("author_name", "title", "expected"),
    [
        ("Test Author", "Test Book", "Test Author/Test Book"),
        (None, "Test Book", "Unknown/Test Book"),
        ("Test Author", None, None),  # Covers line 61
        (None, None, None),  # Covers line 61
        ("Author/With/Slashes", "Title", "Author_With_Slashes/Title"),
        ("Author\\With\\Backslashes", "Title", "Author_With_Backslashes/Title"),
    ],
)
def test_calculate_book_path(
    author_name: str | None, title: str | None, expected: str | None
) -> None:
    """Test calculate_book_path (covers lines 45-66, including line 61)."""
    result = calculate_book_path(author_name, title)
    assert result == expected


def test_calculate_book_path_no_title() -> None:
    """Test calculate_book_path returns None when title is None (covers line 61)."""
    result = calculate_book_path("Test Author", None)
    assert result is None
