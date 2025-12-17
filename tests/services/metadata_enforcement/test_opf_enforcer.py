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

"""Tests for OPF enforcer to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import Library
from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.metadata_enforcement.opf_enforcer import (
    OpfEnforcementService,
)
from bookcard.services.opf_service import OpfMetadataResult, OpfService


@pytest.fixture
def library() -> Library:
    """Create a test library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/test/library",
        calibre_db_file="metadata.db",
    )


@pytest.fixture
def book() -> Book:
    """Create a test book."""
    from datetime import UTC, datetime

    return Book(
        id=1,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
        uuid="test-uuid-123",
        has_cover=False,
        path="Author Name/Test Book (1)",
    )


@pytest.fixture
def book_with_rels(book: Book) -> BookWithFullRelations:
    """Create a test book with relations."""
    return BookWithFullRelations(
        book=book,
        authors=["Author One"],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )


@pytest.fixture
def opf_service() -> MagicMock:
    """Create a mock OPF service."""
    mock_service = MagicMock(spec=OpfService)
    mock_service.generate_opf.return_value = OpfMetadataResult(
        xml_content='<?xml version="1.0"?><package version="3.0"></package>',
        filename="metadata.opf",
    )
    return mock_service


def test_init_default_opf_service(library: Library) -> None:
    """Test initialization with default OPF service."""
    service = OpfEnforcementService(library)
    assert service._library == library
    assert service._opf_service is not None
    assert service._path_resolver is not None


def test_init_custom_opf_service(library: Library, opf_service: MagicMock) -> None:
    """Test initialization with custom OPF service."""
    service = OpfEnforcementService(library, opf_service=opf_service)
    assert service._opf_service == opf_service


def test_enforce_opf_success(
    library: Library,
    book_with_rels: BookWithFullRelations,
    opf_service: MagicMock,
    tmp_path: Path,
) -> None:
    """Test successful OPF enforcement."""
    # Create temporary library root
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)

    with patch(
        "bookcard.services.metadata_enforcement.opf_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        service = OpfEnforcementService(library, opf_service=opf_service)
        result = service.enforce_opf(book_with_rels)

        assert result is True
        opf_file = book_dir / "metadata.opf"
        assert opf_file.exists()
        assert (
            opf_file.read_text(encoding="utf-8")
            == opf_service.generate_opf.return_value.xml_content
        )


def test_enforce_opf_oserror(
    library: Library,
    book_with_rels: BookWithFullRelations,
    opf_service: MagicMock,
) -> None:
    """Test OPF enforcement with OSError."""
    with patch(
        "bookcard.services.metadata_enforcement.opf_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.side_effect = OSError("Permission denied")
        mock_resolver_class.return_value = mock_resolver

        service = OpfEnforcementService(library, opf_service=opf_service)
        result = service.enforce_opf(book_with_rels)

        assert result is False


def test_enforce_opf_valueerror(
    library: Library,
    book_with_rels: BookWithFullRelations,
    opf_service: MagicMock,
) -> None:
    """Test OPF enforcement with ValueError."""
    opf_service.generate_opf.side_effect = ValueError("Invalid metadata")

    with patch(
        "bookcard.services.metadata_enforcement.opf_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = Path("/test/library")
        mock_resolver_class.return_value = mock_resolver

        service = OpfEnforcementService(library, opf_service=opf_service)
        result = service.enforce_opf(book_with_rels)

        assert result is False


def test_enforce_opf_typeerror(
    library: Library,
    book_with_rels: BookWithFullRelations,
    opf_service: MagicMock,
) -> None:
    """Test OPF enforcement with TypeError."""
    opf_service.generate_opf.side_effect = TypeError("Type error")

    with patch(
        "bookcard.services.metadata_enforcement.opf_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = Path("/test/library")
        mock_resolver_class.return_value = mock_resolver

        service = OpfEnforcementService(library, opf_service=opf_service)
        result = service.enforce_opf(book_with_rels)

        assert result is False


def test_enforce_opf_creates_directory(
    library: Library,
    book_with_rels: BookWithFullRelations,
    opf_service: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that OPF enforcement creates book directory if it doesn't exist."""
    library_root = tmp_path / "library"
    library_root.mkdir()

    with patch(
        "bookcard.services.metadata_enforcement.opf_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        service = OpfEnforcementService(library, opf_service=opf_service)
        result = service.enforce_opf(book_with_rels)

        assert result is True
        book_dir = library_root / book_with_rels.book.path
        assert book_dir.exists()
        opf_file = book_dir / "metadata.opf"
        assert opf_file.exists()
