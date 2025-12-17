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

"""Tests for BookPermissionHelper to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from bookcard.models.auth import User
from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations, BookWithRelations
from bookcard.services.book_permission_helper import BookPermissionHelper
from bookcard.services.permission_service import PermissionService

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_permission_service() -> MagicMock:
    """Create a mock permission service."""
    return MagicMock(spec=PermissionService)


@pytest.fixture
def permission_helper(session: DummySession) -> BookPermissionHelper:
    """Create BookPermissionHelper instance."""
    return BookPermissionHelper(session=session)  # type: ignore[arg-type]


@pytest.fixture
def user() -> User:
    """Create sample user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


@pytest.fixture
def book() -> Book:
    """Create sample book."""
    return Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
    )


@pytest.fixture
def book_with_relations(book: Book) -> BookWithRelations:
    """Create BookWithRelations."""
    return BookWithRelations(
        book=book,
        authors=["Author One", "Author Two"],
        series=None,
        formats=[],
    )


@pytest.fixture
def book_with_full_relations(book: Book) -> BookWithFullRelations:
    """Create BookWithFullRelations."""
    return BookWithFullRelations(
        book=book,
        authors=["Author One", "Author Two"],
        series="Test Series",
        series_id=1,
        tags=["Fiction", "Sci-Fi"],
        identifiers=[{"type": "isbn", "val": "1234567890"}],
        description="Test description",
        publisher="Test Publisher",
        publisher_id=1,
        languages=["en"],
        language_ids=[1],
        rating=5,
        rating_id=1,
        formats=[],
    )


@pytest.fixture
def book_with_full_relations_no_optional(book: Book) -> BookWithFullRelations:
    """Create BookWithFullRelations without optional fields."""
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


# ============================================================================
# Initialization Tests
# ============================================================================


class TestBookPermissionHelperInit:
    """Test BookPermissionHelper initialization."""

    def test_init(self, session: DummySession) -> None:
        """Test __init__ creates PermissionService."""
        helper = BookPermissionHelper(session=session)  # type: ignore[arg-type]

        assert isinstance(helper._permission_service, PermissionService)


# ============================================================================
# build_permission_context Tests
# ============================================================================


class TestBuildPermissionContext:
    """Test build_permission_context static method."""

    def test_build_permission_context_with_relations(
        self,
        book_with_relations: BookWithRelations,
    ) -> None:
        """Test build_permission_context with BookWithRelations."""
        result = BookPermissionHelper.build_permission_context(book_with_relations)

        assert result == {"authors": ["Author One", "Author Two"]}

    def test_build_permission_context_with_full_relations(
        self,
        book_with_full_relations: BookWithFullRelations,
    ) -> None:
        """Test build_permission_context with BookWithFullRelations."""
        result = BookPermissionHelper.build_permission_context(book_with_full_relations)

        assert result == {
            "authors": ["Author One", "Author Two"],
            "series_id": 1,
            "tags": ["Fiction", "Sci-Fi"],
        }

    def test_build_permission_context_with_full_relations_no_optional(
        self,
        book_with_full_relations_no_optional: BookWithFullRelations,
    ) -> None:
        """Test build_permission_context with BookWithFullRelations without optional fields."""
        result = BookPermissionHelper.build_permission_context(
            book_with_full_relations_no_optional
        )

        assert result == {"authors": ["Author One"]}


# ============================================================================
# check_read_permission Tests
# ============================================================================


class TestCheckReadPermission:
    """Test check_read_permission method."""

    def test_check_read_permission_with_book(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        book_with_relations: BookWithRelations,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_read_permission with book_with_rels."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_read_permission(user, book_with_relations)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "read", {"authors": ["Author One", "Author Two"]}
        )

    def test_check_read_permission_without_book(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_read_permission without book_with_rels."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_read_permission(user, None)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "read"
        )

    def test_check_read_permission_raises_error(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        book_with_relations: BookWithRelations,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_read_permission raises PermissionError."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.side_effect = PermissionError(
            "No read permission"
        )

        with pytest.raises(PermissionError, match="No read permission"):
            permission_helper.check_read_permission(user, book_with_relations)


# ============================================================================
# check_write_permission Tests
# ============================================================================


class TestCheckWritePermission:
    """Test check_write_permission method."""

    def test_check_write_permission_success(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        book_with_relations: BookWithRelations,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_write_permission succeeds."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_write_permission(user, book_with_relations)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "write", {"authors": ["Author One", "Author Two"]}
        )

    def test_check_write_permission_raises_error(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        book_with_relations: BookWithRelations,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_write_permission raises PermissionError."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.side_effect = PermissionError(
            "No write permission"
        )

        with pytest.raises(PermissionError, match="No write permission"):
            permission_helper.check_write_permission(user, book_with_relations)


# ============================================================================
# check_create_permission Tests
# ============================================================================


class TestCheckCreatePermission:
    """Test check_create_permission method."""

    def test_check_create_permission_success(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_create_permission succeeds."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_create_permission(user)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "create"
        )

    def test_check_create_permission_raises_error(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_create_permission raises PermissionError."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.side_effect = PermissionError(
            "No create permission"
        )

        with pytest.raises(PermissionError, match="No create permission"):
            permission_helper.check_create_permission(user)


# ============================================================================
# check_send_permission Tests
# ============================================================================


class TestCheckSendPermission:
    """Test check_send_permission method."""

    def test_check_send_permission_success(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        book_with_relations: BookWithRelations,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_send_permission succeeds."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_send_permission(user, book_with_relations)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "send", {"authors": ["Author One", "Author Two"]}
        )

    def test_check_send_permission_raises_error(
        self,
        permission_helper: BookPermissionHelper,
        user: User,
        book_with_relations: BookWithRelations,
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_send_permission raises PermissionError."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.side_effect = PermissionError(
            "No send permission"
        )

        with pytest.raises(PermissionError, match="No send permission"):
            permission_helper.check_send_permission(user, book_with_relations)
