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

"""Tests for SeriesExtractor to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.metadata.providers._hardcover.extractors.series import (
    SeriesExtractor,
)


@pytest.fixture
def book_data_with_series() -> dict:
    """Create book data with series_names."""
    return {
        "series_names": ["Series 1", "Series 2"],
    }


@pytest.fixture
def book_data_empty() -> dict:
    """Create empty book data."""
    return {}


def test_extract_with_series(
    book_data_with_series: dict,
) -> None:
    """Test extraction with series_names (covers lines 38-41)."""
    result = SeriesExtractor.extract(book_data_with_series)
    assert result == ("Series 1", None)


def test_extract_no_series(book_data_empty: dict) -> None:
    """Test extraction with no series (covers lines 38-41)."""
    result = SeriesExtractor.extract(book_data_empty)
    assert result == (None, None)


def test_extract_series_names_not_list() -> None:
    """Test extraction with series_names not a list (covers lines 38-41)."""
    book_data = {"series_names": "not a list"}
    result = SeriesExtractor.extract(book_data)
    assert result == (None, None)


def test_extract_series_names_empty() -> None:
    """Test extraction with empty series_names (covers lines 38-41)."""
    book_data = {"series_names": []}
    result = SeriesExtractor.extract(book_data)
    assert result == (None, None)


def test_extract_series_names_single() -> None:
    """Test extraction with single series name."""
    book_data = {"series_names": ["Single Series"]}
    result = SeriesExtractor.extract(book_data)
    assert result == ("Single Series", None)
