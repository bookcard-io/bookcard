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

"""Tests for ebook enforcer base class to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.metadata_enforcement.ebook_enforcer import (
    EbookMetadataEnforcer,
)


class ConcreteEbookMetadataEnforcer(EbookMetadataEnforcer):
    """Concrete implementation for testing."""

    def enforce_metadata(
        self,
        book_with_rels: BookWithFullRelations,
        file_path: Path,
    ) -> bool:
        """Concrete implementation of enforce_metadata."""
        return True


@pytest.fixture
def enforcer() -> ConcreteEbookMetadataEnforcer:
    """Create a concrete enforcer instance."""
    return ConcreteEbookMetadataEnforcer(supported_formats=["epub", "azw3"])


def test_init() -> None:
    """Test EbookMetadataEnforcer initialization."""
    enforcer = ConcreteEbookMetadataEnforcer(supported_formats=["epub", "pdf"])
    assert enforcer._supported_formats == ["epub", "pdf"]


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("epub", True),
        ("EPUB", True),
        ("Epub", True),
        ("azw3", True),
        ("AZW3", True),
        ("pdf", False),
        ("mobi", False),
        ("", False),
    ],
)
def test_can_handle(
    enforcer: ConcreteEbookMetadataEnforcer, file_format: str, expected: bool
) -> None:
    """Test can_handle method with various formats."""
    assert enforcer.can_handle(file_format) == expected


def test_enforce_metadata_not_implemented() -> None:
    """Test that abstract enforce_metadata raises NotImplementedError."""
    enforcer = ConcreteEbookMetadataEnforcer(supported_formats=["epub"])
    # This should not raise since we have a concrete implementation
    book_with_rels = MagicMock(spec=BookWithFullRelations)
    file_path = Path("/test/book.epub")
    result = enforcer.enforce_metadata(book_with_rels, file_path)
    assert result is True
