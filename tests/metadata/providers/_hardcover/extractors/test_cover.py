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

"""Tests for CoverExtractor to achieve 100% coverage."""

from __future__ import annotations

import pytest

from bookcard.metadata.providers._hardcover.extractors.cover import (
    CoverExtractor,
)


@pytest.fixture
def book_data_with_edition_image() -> dict:
    """Create book data with edition image."""
    return {
        "editions": [
            {
                "image": {"url": "https://example.com/edition-cover.jpg"},
            }
        ]
    }


@pytest.fixture
def book_data_with_default_cover() -> dict:
    """Create book data with default_cover_edition."""
    return {
        "default_cover_edition": {
            "cached_image": {"url": "https://example.com/default-cover.jpg"},
        }
    }


@pytest.fixture
def book_data_with_image() -> dict:
    """Create book data with top-level image."""
    return {
        "image": {"url": "https://example.com/cover.jpg"},
    }


@pytest.fixture
def book_data_empty() -> dict:
    """Create empty book data."""
    return {}


def test_extract_from_edition(
    book_data_with_edition_image: dict,
) -> None:
    """Test extraction from edition (covers lines 38-45)."""
    result = CoverExtractor.extract(book_data_with_edition_image)
    assert result == "https://example.com/edition-cover.jpg"


def test_extract_from_edition_no_image(
    book_data_with_edition_image: dict,
) -> None:
    """Test extraction from edition without image (covers lines 38-45)."""
    book_data_with_edition_image["editions"][0].pop("image")
    result = CoverExtractor.extract(book_data_with_edition_image)
    assert result is None


def test_extract_from_edition_image_not_dict(
    book_data_with_edition_image: dict,
) -> None:
    """Test extraction from edition with image not a dict (covers lines 38-45)."""
    book_data_with_edition_image["editions"][0]["image"] = "not a dict"
    result = CoverExtractor.extract(book_data_with_edition_image)
    assert result is None


def test_extract_from_edition_image_no_url(
    book_data_with_edition_image: dict,
) -> None:
    """Test extraction from edition with image without url (covers lines 38-45)."""
    book_data_with_edition_image["editions"][0]["image"] = {}
    result = CoverExtractor.extract(book_data_with_edition_image)
    assert result is None


def test_extract_from_default_cover(
    book_data_with_default_cover: dict,
) -> None:
    """Test extraction from default_cover_edition (covers lines 47-54)."""
    result = CoverExtractor.extract(book_data_with_default_cover)
    assert result == "https://example.com/default-cover.jpg"


def test_extract_from_default_cover_no_cached_image(
    book_data_with_default_cover: dict,
) -> None:
    """Test extraction from default_cover_edition without cached_image (covers lines 47-54)."""
    book_data_with_default_cover["default_cover_edition"].pop("cached_image")
    result = CoverExtractor.extract(book_data_with_default_cover)
    assert result is None


def test_extract_from_default_cover_cached_image_not_dict(
    book_data_with_default_cover: dict,
) -> None:
    """Test extraction from default_cover_edition with cached_image not a dict (covers lines 47-54)."""
    book_data_with_default_cover["default_cover_edition"]["cached_image"] = "not a dict"
    result = CoverExtractor.extract(book_data_with_default_cover)
    assert result is None


def test_extract_from_default_cover_no_url(
    book_data_with_default_cover: dict,
) -> None:
    """Test extraction from default_cover_edition with cached_image without url (covers lines 47-54)."""
    book_data_with_default_cover["default_cover_edition"]["cached_image"] = {}
    result = CoverExtractor.extract(book_data_with_default_cover)
    assert result is None


def test_extract_from_default_cover_not_dict() -> None:
    """Test extraction from default_cover_edition not a dict (covers lines 47-54)."""
    book_data = {"default_cover_edition": "not a dict"}
    result = CoverExtractor.extract(book_data)
    assert result is None


def test_extract_from_image(
    book_data_with_image: dict,
) -> None:
    """Test extraction from top-level image (covers lines 56-61)."""
    result = CoverExtractor.extract(book_data_with_image)
    assert result == "https://example.com/cover.jpg"


def test_extract_from_image_not_dict() -> None:
    """Test extraction from top-level image not a dict (covers lines 56-61)."""
    book_data = {"image": "not a dict"}
    result = CoverExtractor.extract(book_data)
    assert result is None


def test_extract_from_image_no_url() -> None:
    """Test extraction from top-level image without url (covers lines 56-61)."""
    book_data = {"image": {}}
    result = CoverExtractor.extract(book_data)
    assert result is None


def test_extract_no_cover(book_data_empty: dict) -> None:
    """Test extraction with no cover data (covers lines 38-63)."""
    result = CoverExtractor.extract(book_data_empty)
    assert result is None


def test_extract_priority_order() -> None:
    """Test that edition takes priority over default_cover_edition and image."""
    book_data = {
        "editions": [{"image": {"url": "edition.jpg"}}],
        "default_cover_edition": {"cached_image": {"url": "default.jpg"}},
        "image": {"url": "top.jpg"},
    }
    result = CoverExtractor.extract(book_data)
    assert result == "edition.jpg"


def test_extract_fallback_to_default_cover() -> None:
    """Test fallback to default_cover_edition when edition has no image."""
    book_data = {
        "editions": [{}],
        "default_cover_edition": {"cached_image": {"url": "default.jpg"}},
    }
    result = CoverExtractor.extract(book_data)
    assert result == "default.jpg"


def test_extract_fallback_to_image() -> None:
    """Test fallback to top-level image when edition and default_cover have no image."""
    book_data = {
        "editions": [{}],
        "image": {"url": "top.jpg"},
    }
    result = CoverExtractor.extract(book_data)
    assert result == "top.jpg"
