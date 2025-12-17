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

"""Tests for KoboBookLookupService to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.kobo.book_lookup_service import KoboBookLookupService

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_book_service() -> MagicMock:
    """Create a mock BookService.

    Returns
    -------
    MagicMock
        Mock book service instance.
    """
    service = MagicMock()
    service._book_repo = MagicMock()
    service._book_repo.get_session = MagicMock()
    service.get_book_full = MagicMock(return_value=None)
    return service


@pytest.fixture
def book_lookup_service(mock_book_service: MagicMock) -> KoboBookLookupService:
    """Create KoboBookLookupService instance for testing.

    Parameters
    ----------
    mock_book_service : MagicMock
        Mock book service.

    Returns
    -------
    KoboBookLookupService
        Service instance.
    """
    return KoboBookLookupService(mock_book_service)


@pytest.fixture
def book() -> Book:
    """Create a test book.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(id=1, title="Test Book", uuid="test-uuid-123")


@pytest.fixture
def book_without_id() -> Book:
    """Create a test book without ID.

    Returns
    -------
    Book
        Book instance without ID.
    """
    return Book(id=None, title="Test Book", uuid="test-uuid-123")


# ============================================================================
# Tests for KoboBookLookupService.__init__
# ============================================================================


def test_init(mock_book_service: MagicMock) -> None:
    """Test KoboBookLookupService initialization.

    Parameters
    ----------
    mock_book_service : MagicMock
        Mock book service.
    """
    service = KoboBookLookupService(mock_book_service)
    assert service._book_service == mock_book_service


# ============================================================================
# Tests for KoboBookLookupService.find_book_by_uuid
# ============================================================================


def test_find_book_by_uuid_found(
    book_lookup_service: KoboBookLookupService,
    mock_book_service: MagicMock,
    book: Book,
) -> None:
    """Test finding book by UUID when book exists.

    Parameters
    ----------
    book_lookup_service : KoboBookLookupService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    book : Book
        Test book.
    """
    mock_session = Mock()
    mock_result = Mock()
    mock_result.first = Mock(return_value=book)
    mock_session.exec = Mock(return_value=mock_result)
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    mock_book_service._book_repo.get_session.return_value = mock_session

    result = book_lookup_service.find_book_by_uuid("test-uuid-123")

    assert result is not None
    assert result == (1, book)
    mock_book_service._book_repo.get_session.assert_called_once()


def test_find_book_by_uuid_not_found(
    book_lookup_service: KoboBookLookupService,
    mock_book_service: MagicMock,
) -> None:
    """Test finding book by UUID when book does not exist.

    Parameters
    ----------
    book_lookup_service : KoboBookLookupService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    """
    mock_session = Mock()
    mock_result = Mock()
    mock_result.first = Mock(return_value=None)
    mock_session.exec = Mock(return_value=mock_result)
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    mock_book_service._book_repo.get_session.return_value = mock_session

    result = book_lookup_service.find_book_by_uuid("non-existent-uuid")

    assert result is None


def test_find_book_by_uuid_no_id(
    book_lookup_service: KoboBookLookupService,
    mock_book_service: MagicMock,
    book_without_id: Book,
) -> None:
    """Test finding book by UUID when book has no ID.

    Parameters
    ----------
    book_lookup_service : KoboBookLookupService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    book_without_id : Book
        Test book without ID.
    """
    mock_session = Mock()
    mock_result = Mock()
    mock_result.first = Mock(return_value=book_without_id)
    mock_session.exec = Mock(return_value=mock_result)
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    mock_book_service._book_repo.get_session.return_value = mock_session

    result = book_lookup_service.find_book_by_uuid("test-uuid-123")

    assert result is None


# ============================================================================
# Tests for KoboBookLookupService.get_book_with_relations
# ============================================================================


def test_get_book_with_relations_found(
    book_lookup_service: KoboBookLookupService,
    mock_book_service: MagicMock,
) -> None:
    """Test getting book with relations when book exists.

    Parameters
    ----------
    book_lookup_service : KoboBookLookupService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    """
    book_with_rels = MagicMock(spec=BookWithFullRelations)
    mock_book_service.get_book_full.return_value = book_with_rels

    result = book_lookup_service.get_book_with_relations(book_id=1)

    assert result == book_with_rels
    mock_book_service.get_book_full.assert_called_once_with(1)


def test_get_book_with_relations_not_found(
    book_lookup_service: KoboBookLookupService,
    mock_book_service: MagicMock,
) -> None:
    """Test getting book with relations when book does not exist.

    Parameters
    ----------
    book_lookup_service : KoboBookLookupService
        Service instance.
    mock_book_service : MagicMock
        Mock book service.
    """
    mock_book_service.get_book_full.return_value = None

    result = book_lookup_service.get_book_with_relations(book_id=999)

    assert result is None
    mock_book_service.get_book_full.assert_called_once_with(999)
