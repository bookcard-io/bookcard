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

"""Tests for AuthorPermissionHelper to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from fundamental.models.auth import User
from fundamental.services.author_permission_helper import AuthorPermissionHelper
from fundamental.services.permission_service import PermissionService

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
def permission_helper(session: DummySession) -> AuthorPermissionHelper:
    """Create AuthorPermissionHelper instance."""
    return AuthorPermissionHelper(session=session)  # type: ignore[arg-type]


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
def author_data_with_name() -> dict[str, object]:
    """Create author data with name."""
    return {"name": "Test Author", "id": 1}


@pytest.fixture
def author_data_without_name() -> dict[str, object]:
    """Create author data without name."""
    return {"id": 1}


@pytest.fixture
def author_data_empty() -> dict[str, object]:
    """Create empty author data."""
    return {}


# ============================================================================
# Initialization Tests
# ============================================================================


class TestAuthorPermissionHelperInit:
    """Test AuthorPermissionHelper initialization."""

    def test_init(self, session: DummySession) -> None:
        """Test __init__ creates PermissionService."""
        helper = AuthorPermissionHelper(session=session)  # type: ignore[arg-type]

        assert isinstance(helper._permission_service, PermissionService)


# ============================================================================
# build_permission_context Tests
# ============================================================================


class TestBuildPermissionContext:
    """Test build_permission_context static method."""

    def test_build_permission_context_with_name(
        self, author_data_with_name: dict[str, object]
    ) -> None:
        """Test build_permission_context with author name."""
        result = AuthorPermissionHelper.build_permission_context(author_data_with_name)

        assert result == {"authors": ["Test Author"]}

    def test_build_permission_context_without_name(
        self, author_data_without_name: dict[str, object]
    ) -> None:
        """Test build_permission_context without author name."""
        result = AuthorPermissionHelper.build_permission_context(
            author_data_without_name
        )

        assert result == {"authors": []}

    def test_build_permission_context_empty(
        self, author_data_empty: dict[str, object]
    ) -> None:
        """Test build_permission_context with empty data."""
        result = AuthorPermissionHelper.build_permission_context(author_data_empty)

        assert result == {"authors": []}

    def test_build_permission_context_name_none(
        self,
    ) -> None:
        """Test build_permission_context with name=None."""
        author_data: dict[str, object] = {"name": None, "id": 1}
        result = AuthorPermissionHelper.build_permission_context(author_data)

        assert result == {"authors": []}

    def test_build_permission_context_name_empty_string(
        self,
    ) -> None:
        """Test build_permission_context with empty string name."""
        author_data: dict[str, object] = {"name": "", "id": 1}
        result = AuthorPermissionHelper.build_permission_context(author_data)

        assert result == {"authors": []}


# ============================================================================
# check_write_permission Tests
# ============================================================================


class TestCheckWritePermission:
    """Test check_write_permission method."""

    def test_check_write_permission_success(
        self,
        permission_helper: AuthorPermissionHelper,
        user: User,
        author_data_with_name: dict[str, object],
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_write_permission succeeds."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_write_permission(user, author_data_with_name)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "write", {"authors": ["Test Author"]}
        )

    def test_check_write_permission_without_name(
        self,
        permission_helper: AuthorPermissionHelper,
        user: User,
        author_data_without_name: dict[str, object],
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_write_permission with author without name."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_write_permission(user, author_data_without_name)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "write", {"authors": []}
        )

    def test_check_write_permission_raises_error(
        self,
        permission_helper: AuthorPermissionHelper,
        user: User,
        author_data_with_name: dict[str, object],
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_write_permission raises PermissionError."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.side_effect = PermissionError(
            "No write permission"
        )

        with pytest.raises(PermissionError, match="No write permission"):
            permission_helper.check_write_permission(user, author_data_with_name)


# ============================================================================
# check_read_permission Tests
# ============================================================================


class TestCheckReadPermission:
    """Test check_read_permission method."""

    def test_check_read_permission_success(
        self,
        permission_helper: AuthorPermissionHelper,
        user: User,
        author_data_with_name: dict[str, object],
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_read_permission succeeds."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_read_permission(user, author_data_with_name)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "read", {"authors": ["Test Author"]}
        )

    def test_check_read_permission_without_name(
        self,
        permission_helper: AuthorPermissionHelper,
        user: User,
        author_data_without_name: dict[str, object],
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_read_permission with author without name."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.return_value = None

        permission_helper.check_read_permission(user, author_data_without_name)

        mock_permission_service.check_permission.assert_called_once_with(
            user, "books", "read", {"authors": []}
        )

    def test_check_read_permission_raises_error(
        self,
        permission_helper: AuthorPermissionHelper,
        user: User,
        author_data_with_name: dict[str, object],
        mock_permission_service: MagicMock,
    ) -> None:
        """Test check_read_permission raises PermissionError."""
        permission_helper._permission_service = mock_permission_service
        mock_permission_service.check_permission.side_effect = PermissionError(
            "No read permission"
        )

        with pytest.raises(PermissionError, match="No read permission"):
            permission_helper.check_read_permission(user, author_data_with_name)
