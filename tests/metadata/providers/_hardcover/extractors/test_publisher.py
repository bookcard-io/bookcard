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

"""Tests for PublisherExtractor to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.metadata.providers._hardcover.extractors.publisher import (
    PublisherExtractor,
)


@pytest.fixture
def book_data_with_edition_publisher() -> dict:
    """Create book data with edition publisher."""
    return {
        "editions": [
            {
                "publisher": {"name": "Edition Publisher"},
            }
        ]
    }


@pytest.fixture
def book_data_with_publisher() -> dict:
    """Create book data with top-level publisher."""
    return {
        "publisher": "Top Publisher",
    }


@pytest.fixture
def book_data_empty() -> dict:
    """Create empty book data."""
    return {}


def test_extract_from_edition(
    book_data_with_edition_publisher: dict,
) -> None:
    """Test extraction from edition (covers lines 41-48)."""
    result = PublisherExtractor.extract(book_data_with_edition_publisher)
    assert result == "Edition Publisher"


def test_extract_from_edition_no_publisher(
    book_data_with_edition_publisher: dict,
) -> None:
    """Test extraction from edition without publisher (covers lines 41-48)."""
    book_data_with_edition_publisher["editions"][0].pop("publisher")
    result = PublisherExtractor.extract(book_data_with_edition_publisher)
    assert result is None


def test_extract_from_edition_publisher_not_dict(
    book_data_with_edition_publisher: dict,
) -> None:
    """Test extraction from edition with publisher not a dict (covers lines 41-48)."""
    book_data_with_edition_publisher["editions"][0]["publisher"] = "not a dict"
    result = PublisherExtractor.extract(book_data_with_edition_publisher)
    assert result is None


def test_extract_from_edition_publisher_no_name(
    book_data_with_edition_publisher: dict,
) -> None:
    """Test extraction from edition with publisher without name (covers lines 41-48)."""
    book_data_with_edition_publisher["editions"][0]["publisher"] = {}
    result = PublisherExtractor.extract(book_data_with_edition_publisher)
    assert result is None


def test_extract_from_publisher(
    book_data_with_publisher: dict,
) -> None:
    """Test extraction from top-level publisher (covers lines 50-51)."""
    result = PublisherExtractor.extract(book_data_with_publisher)
    assert result == "Top Publisher"


def test_extract_from_publisher_falsy() -> None:
    """Test extraction from top-level publisher falsy (covers lines 50-51)."""
    book_data = {"publisher": ""}
    result = PublisherExtractor.extract(book_data)
    assert result is None


def test_extract_no_publisher(book_data_empty: dict) -> None:
    """Test extraction with no publisher (covers lines 41-51)."""
    result = PublisherExtractor.extract(book_data_empty)
    assert result is None


def test_extract_priority_order() -> None:
    """Test that edition takes priority over top-level publisher."""
    book_data = {
        "editions": [{"publisher": {"name": "Edition Publisher"}}],
        "publisher": "Top Publisher",
    }
    result = PublisherExtractor.extract(book_data)
    assert result == "Edition Publisher"


def test_extract_fallback_to_publisher() -> None:
    """Test fallback to top-level publisher when edition has no publisher."""
    book_data = {
        "editions": [{}],
        "publisher": "Top Publisher",
    }
    result = PublisherExtractor.extract(book_data)
    assert result == "Top Publisher"
