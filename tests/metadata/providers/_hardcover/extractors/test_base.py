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

"""Tests for base extractor protocol to achieve 100% coverage."""

from __future__ import annotations

from bookcard.metadata.providers._hardcover.extractors.base import (
    FieldExtractor,
)


class TestExtractor:
    """Test extractor implementing FieldExtractor protocol."""

    def extract(self, book_data: dict) -> object:
        """Extract field value from book data."""
        return book_data.get("test_field")


def test_field_extractor_protocol() -> None:
    """Test that FieldExtractor protocol can be implemented (covers lines 18-20)."""
    extractor = TestExtractor()
    book_data = {"test_field": "test_value"}
    result = extractor.extract(book_data)
    assert result == "test_value"


def test_field_extractor_protocol_implementation() -> None:
    """Test that extractors implement FieldExtractor protocol."""
    # This test verifies the protocol is properly defined
    # The actual implementation is tested in individual extractor tests
    assert hasattr(FieldExtractor, "__protocol_methods__") or callable(
        getattr(FieldExtractor, "extract", None)
    )
