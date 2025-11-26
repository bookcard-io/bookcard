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

"""Tests for LanguagesExtractor to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.metadata.providers._hardcover.extractors.languages import (
    LanguagesExtractor,
)


@pytest.fixture
def book_data_with_language() -> dict:
    """Create book data with language."""
    return {
        "editions": [
            {
                "language": {"code3": "eng"},
            }
        ]
    }


@pytest.fixture
def book_data_empty() -> dict:
    """Create empty book data."""
    return {}


def test_extract_with_language(
    book_data_with_language: dict,
) -> None:
    """Test extraction with language (covers lines 38-46)."""
    result = LanguagesExtractor.extract(book_data_with_language)
    assert len(result) == 1
    assert "eng" in result


def test_extract_no_edition(book_data_empty: dict) -> None:
    """Test extraction with no edition (covers lines 38-46)."""
    result = LanguagesExtractor.extract(book_data_empty)
    assert result == []


def test_extract_edition_no_language() -> None:
    """Test extraction with edition but no language (covers lines 38-46)."""
    book_data = {"editions": [{}]}
    result = LanguagesExtractor.extract(book_data)
    assert result == []


def test_extract_language_not_dict() -> None:
    """Test extraction with language not a dict (covers lines 38-46)."""
    book_data = {"editions": [{"language": "not a dict"}]}
    result = LanguagesExtractor.extract(book_data)
    assert result == []


def test_extract_language_no_code3() -> None:
    """Test extraction with language without code3 (covers lines 38-46)."""
    book_data = {"editions": [{"language": {}}]}
    result = LanguagesExtractor.extract(book_data)
    assert result == []


def test_extract_language_code3_falsy() -> None:
    """Test extraction with language code3 falsy (covers lines 38-46)."""
    book_data = {"editions": [{"language": {"code3": ""}}]}
    result = LanguagesExtractor.extract(book_data)
    assert result == []


def test_extract_language_code3_none() -> None:
    """Test extraction with language code3 None (covers lines 38-46)."""
    book_data = {"editions": [{"language": {"code3": None}}]}
    result = LanguagesExtractor.extract(book_data)
    assert result == []
