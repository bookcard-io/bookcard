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

"""Tests for metadata enforcement trigger service to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import Library
from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.metadata_enforcement_trigger_service import (
    MetadataEnforcementTriggerService,
)

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def library() -> Library:
    """Create a test library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/test/library",
        calibre_db_file="metadata.db",
        auto_metadata_enforcement=True,
    )


@pytest.fixture
def library_disabled() -> Library:
    """Create a test library with enforcement disabled."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/test/library",
        calibre_db_file="metadata.db",
        auto_metadata_enforcement=False,
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
def mock_library_service() -> MagicMock:
    """Create a mock library service."""
    return MagicMock()


def test_init_default_services(session: DummySession) -> None:
    """Test initialization with default services."""
    service = MetadataEnforcementTriggerService(session)  # type: ignore[arg-type]
    assert service._session == session
    assert service._library_repo is not None
    assert service._library_service is not None


def test_init_custom_services(
    session: DummySession, mock_library_service: MagicMock
) -> None:
    """Test initialization with custom services."""
    mock_library_repo = MagicMock()
    service = MetadataEnforcementTriggerService(
        session,  # type: ignore[arg-type]
        library_repo=mock_library_repo,
        library_service=mock_library_service,
    )
    assert service._library_repo == mock_library_repo
    assert service._library_service == mock_library_service


def test_trigger_enforcement_if_enabled_enabled(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    mock_library_service: MagicMock,
) -> None:
    """Test trigger_enforcement_if_enabled when enforcement is enabled."""
    mock_library_service.get_active_library.return_value = library

    with patch(
        "bookcard.services.metadata_enforcement_trigger_service.MetadataEnforcementService"
    ) as mock_enforcement_service_class:
        mock_enforcement_service = MagicMock()
        mock_enforcement_service.enforce_metadata.return_value = MagicMock(success=True)
        mock_enforcement_service_class.return_value = mock_enforcement_service

        service = MetadataEnforcementTriggerService(
            session,  # type: ignore[arg-type]
            library_service=mock_library_service,
        )
        service.trigger_enforcement_if_enabled(1, book_with_rels, user_id=1)

        mock_enforcement_service.enforce_metadata.assert_called_once_with(
            book_id=1, book_with_rels=book_with_rels, user_id=1
        )


def test_trigger_enforcement_if_enabled_disabled(
    session: DummySession,
    library_disabled: Library,
    book_with_rels: BookWithFullRelations,
    mock_library_service: MagicMock,
) -> None:
    """Test trigger_enforcement_if_enabled when enforcement is disabled."""
    mock_library_service.get_active_library.return_value = library_disabled

    with patch(
        "bookcard.services.metadata_enforcement_trigger_service.MetadataEnforcementService"
    ) as mock_enforcement_service_class:
        service = MetadataEnforcementTriggerService(
            session,  # type: ignore[arg-type]
            library_service=mock_library_service,
        )
        service.trigger_enforcement_if_enabled(1, book_with_rels, user_id=1)

        mock_enforcement_service_class.assert_not_called()


def test_trigger_enforcement_if_enabled_no_library(
    session: DummySession,
    book_with_rels: BookWithFullRelations,
    mock_library_service: MagicMock,
) -> None:
    """Test trigger_enforcement_if_enabled when no active library."""
    mock_library_service.get_active_library.return_value = None

    with patch(
        "bookcard.services.metadata_enforcement_trigger_service.MetadataEnforcementService"
    ) as mock_enforcement_service_class:
        service = MetadataEnforcementTriggerService(
            session,  # type: ignore[arg-type]
            library_service=mock_library_service,
        )
        service.trigger_enforcement_if_enabled(1, book_with_rels, user_id=1)

        mock_enforcement_service_class.assert_not_called()


def test_trigger_enforcement_if_enabled_exception(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    mock_library_service: MagicMock,
) -> None:
    """Test trigger_enforcement_if_enabled with exception (suppressed)."""
    mock_library_service.get_active_library.return_value = library

    with patch(
        "bookcard.services.metadata_enforcement_trigger_service.MetadataEnforcementService"
    ) as mock_enforcement_service_class:
        mock_enforcement_service = MagicMock()
        mock_enforcement_service.enforce_metadata.side_effect = Exception("Test error")
        mock_enforcement_service_class.return_value = mock_enforcement_service

        service = MetadataEnforcementTriggerService(
            session,  # type: ignore[arg-type]
            library_service=mock_library_service,
        )
        # Should not raise exception
        service.trigger_enforcement_if_enabled(1, book_with_rels, user_id=1)

        mock_enforcement_service.enforce_metadata.assert_called_once()
