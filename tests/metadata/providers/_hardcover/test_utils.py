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

"""Tests for Hardcover utils to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.metadata.providers._hardcover.utils import (
    PARSE_EXCEPTIONS,
    get_first_edition,
    safe_string,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("test", "test"),
        (123, "123"),
        (0, None),
        ("", None),
        (None, None),
        (False, None),
        ([], None),
        ({}, None),
    ],
)
def test_safe_string(value: object, expected: str | None) -> None:
    """Test safe_string conversion (covers lines 19-32)."""
    result = safe_string(value)
    assert result == expected


def test_safe_string_truthy_values() -> None:
    """Test safe_string with truthy values."""
    assert safe_string("non-empty") == "non-empty"
    assert safe_string(1) == "1"
    assert safe_string(True) == "True"


def test_get_first_edition_with_editions() -> None:
    """Test get_first_edition with valid editions (covers lines 48-50)."""
    book_data = {
        "editions": [
            {"id": 1, "title": "Edition 1"},
            {"id": 2, "title": "Edition 2"},
        ]
    }
    result = get_first_edition(book_data)
    assert result == {"id": 1, "title": "Edition 1"}


def test_get_first_edition_empty_list() -> None:
    """Test get_first_edition with empty list (covers lines 48-51)."""
    book_data = {"editions": []}
    result = get_first_edition(book_data)
    assert result is None


def test_get_first_edition_no_editions() -> None:
    """Test get_first_edition with no editions key (covers lines 48-51)."""
    book_data = {}
    result = get_first_edition(book_data)
    assert result is None


def test_get_first_edition_editions_not_list() -> None:
    """Test get_first_edition with editions not a list (covers lines 48-51)."""
    book_data = {"editions": "not a list"}
    result = get_first_edition(book_data)
    assert result is None


def test_parse_exceptions() -> None:
    """Test PARSE_EXCEPTIONS constant (covers line 55)."""
    assert KeyError in PARSE_EXCEPTIONS
    assert ValueError in PARSE_EXCEPTIONS
    assert TypeError in PARSE_EXCEPTIONS
    assert AttributeError in PARSE_EXCEPTIONS
