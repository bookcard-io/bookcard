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

"""Tests for PublishedDateExtractor to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.metadata.providers._hardcover.extractors.published_date import (
    PublishedDateExtractor,
)


@pytest.fixture
def book_data_with_edition_date() -> dict:
    """Create book data with edition release_date."""
    return {
        "editions": [
            {
                "release_date": "2024-01-01",
            }
        ]
    }


@pytest.fixture
def book_data_with_release_date() -> dict:
    """Create book data with top-level release_date."""
    return {
        "release_date": "2024-01-01",
    }


@pytest.fixture
def book_data_with_release_year() -> dict:
    """Create book data with release_year."""
    return {
        "release_year": 2024,
    }


@pytest.fixture
def book_data_empty() -> dict:
    """Create empty book data."""
    return {}


def test_extract_from_edition(
    book_data_with_edition_date: dict,
) -> None:
    """Test extraction from edition (covers lines 38-43)."""
    result = PublishedDateExtractor.extract(book_data_with_edition_date)
    assert result == "2024-01-01"


def test_extract_from_edition_no_release_date(
    book_data_with_edition_date: dict,
) -> None:
    """Test extraction from edition without release_date (covers lines 38-43)."""
    book_data_with_edition_date["editions"][0].pop("release_date")
    result = PublishedDateExtractor.extract(book_data_with_edition_date)
    assert result is None


def test_extract_from_release_date(
    book_data_with_release_date: dict,
) -> None:
    """Test extraction from top-level release_date (covers lines 45-48)."""
    result = PublishedDateExtractor.extract(book_data_with_release_date)
    assert result == "2024-01-01"


def test_extract_from_release_year(
    book_data_with_release_year: dict,
) -> None:
    """Test extraction from release_year (covers lines 50-53)."""
    result = PublishedDateExtractor.extract(book_data_with_release_year)
    assert result == "2024"


def test_extract_from_release_year_string() -> None:
    """Test extraction from release_year as string (covers lines 50-53)."""
    book_data = {"release_year": "2024"}
    result = PublishedDateExtractor.extract(book_data)
    assert result == "2024"


def test_extract_no_date(book_data_empty: dict) -> None:
    """Test extraction with no date (covers lines 38-55)."""
    result = PublishedDateExtractor.extract(book_data_empty)
    assert result is None


def test_extract_priority_order() -> None:
    """Test that edition takes priority over top-level release_date and release_year."""
    book_data = {
        "editions": [{"release_date": "2024-01-01"}],
        "release_date": "2023-01-01",
        "release_year": 2022,
    }
    result = PublishedDateExtractor.extract(book_data)
    assert result == "2024-01-01"


def test_extract_fallback_to_release_date() -> None:
    """Test fallback to release_date when edition has no date."""
    book_data = {
        "editions": [{}],
        "release_date": "2024-01-01",
    }
    result = PublishedDateExtractor.extract(book_data)
    assert result == "2024-01-01"


def test_extract_fallback_to_release_year() -> None:
    """Test fallback to release_year when edition and release_date are missing."""
    book_data = {
        "editions": [{}],
        "release_year": 2024,
    }
    result = PublishedDateExtractor.extract(book_data)
    assert result == "2024"
