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

"""Tests for _resolve_active_library, get_active_library_id, and get_visible_library_ids."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from bookcard.api.deps import (
    _resolve_active_library,
    get_active_library_id,
    get_visible_library_ids,
)
from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.models.user_library import UserLibrary
from tests.conftest import DummySession


def _make_library(lib_id: int = 1, name: str = "Test Library") -> Library:
    """Create a test library."""
    lib = Library(id=lib_id, name=name)
    lib.calibre_db_path = "/fake/path"
    return lib


def _make_user(user_id: int = 1) -> User:
    """Create a test user."""
    return User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


class TestResolveActiveLibrary:
    """Tests for _resolve_active_library helper."""

    @patch("bookcard.api.deps.LibraryService")
    @patch("bookcard.api.deps.LibraryRepository")
    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_returns_user_library_when_user_has_active(
        self,
        mock_ul_repo_cls: MagicMock,
        mock_lib_repo_cls: MagicMock,
        mock_lib_svc_cls: MagicMock,
    ) -> None:
        """When user has an active UserLibrary, return that library."""
        session = DummySession()
        user_library = _make_library(lib_id=42, name="User Library")
        mock_ul_repo = MagicMock()
        mock_ul_repo.get_active_library_for_user.return_value = user_library
        mock_ul_repo_cls.return_value = mock_ul_repo

        result = _resolve_active_library(session, user_id=1)  # type: ignore[arg-type]

        assert result is user_library
        mock_ul_repo.get_active_library_for_user.assert_called_once_with(1)
        # Should NOT have fallen through to global
        mock_lib_repo_cls.assert_not_called()

    @patch("bookcard.api.deps.LibraryService")
    @patch("bookcard.api.deps.LibraryRepository")
    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_falls_back_to_global_when_user_has_no_active(
        self,
        mock_ul_repo_cls: MagicMock,
        mock_lib_repo_cls: MagicMock,
        mock_lib_svc_cls: MagicMock,
    ) -> None:
        """When user has no active UserLibrary, fall back to global."""
        session = DummySession()
        global_library = _make_library(lib_id=99, name="Global Library")
        mock_ul_repo = MagicMock()
        mock_ul_repo.get_active_library_for_user.return_value = None
        mock_ul_repo_cls.return_value = mock_ul_repo

        mock_lib_svc = MagicMock()
        mock_lib_svc.get_active_library.return_value = global_library
        mock_lib_svc_cls.return_value = mock_lib_svc

        result = _resolve_active_library(session, user_id=1)  # type: ignore[arg-type]

        assert result is global_library

    @patch("bookcard.api.deps.LibraryService")
    @patch("bookcard.api.deps.LibraryRepository")
    def test_falls_back_to_global_when_no_user(
        self,
        mock_lib_repo_cls: MagicMock,
        mock_lib_svc_cls: MagicMock,
    ) -> None:
        """When user_id is None, go directly to global fallback."""
        session = DummySession()
        global_library = _make_library(lib_id=99, name="Global Library")
        mock_lib_svc = MagicMock()
        mock_lib_svc.get_active_library.return_value = global_library
        mock_lib_svc_cls.return_value = mock_lib_svc

        result = _resolve_active_library(session, user_id=None)  # type: ignore[arg-type]

        assert result is global_library

    @patch("bookcard.api.deps.LibraryService")
    @patch("bookcard.api.deps.LibraryRepository")
    def test_returns_none_when_no_global_library(
        self,
        mock_lib_repo_cls: MagicMock,
        mock_lib_svc_cls: MagicMock,
    ) -> None:
        """When no global active library exists, return None."""
        session = DummySession()
        mock_lib_svc = MagicMock()
        mock_lib_svc.get_active_library.return_value = None
        mock_lib_svc_cls.return_value = mock_lib_svc

        result = _resolve_active_library(session, user_id=None)  # type: ignore[arg-type]

        assert result is None


class TestGetActiveLibraryId:
    """Tests for get_active_library_id dependency."""

    @patch("bookcard.api.deps._resolve_active_library")
    def test_returns_library_id_for_authenticated_user(
        self,
        mock_resolve: MagicMock,
    ) -> None:
        """Return the ID of the resolved library for an authenticated user."""
        session = DummySession()
        user = _make_user()
        library = _make_library(lib_id=42)
        mock_resolve.return_value = library

        result = get_active_library_id(session, current_user=user)  # type: ignore[arg-type]

        assert result == 42
        mock_resolve.assert_called_once_with(session, 1)

    @patch("bookcard.api.deps._resolve_active_library")
    def test_returns_library_id_for_anonymous_user(
        self,
        mock_resolve: MagicMock,
    ) -> None:
        """Return the ID of the global library when user is None."""
        session = DummySession()
        library = _make_library(lib_id=99)
        mock_resolve.return_value = library

        result = get_active_library_id(session, current_user=None)  # type: ignore[arg-type]

        assert result == 99
        mock_resolve.assert_called_once_with(session, None)

    @patch("bookcard.api.deps._resolve_active_library")
    def test_raises_404_when_no_library(
        self,
        mock_resolve: MagicMock,
    ) -> None:
        """Raise 404 when no active library exists."""
        session = DummySession()
        mock_resolve.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_active_library_id(session, current_user=None)  # type: ignore[arg-type]

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "no_active_library"

    @patch("bookcard.api.deps._resolve_active_library")
    def test_raises_404_when_library_has_no_id(
        self,
        mock_resolve: MagicMock,
    ) -> None:
        """Raise 404 when resolved library has id=None."""
        session = DummySession()
        library = Library(id=None, name="No ID")
        mock_resolve.return_value = library

        with pytest.raises(HTTPException) as exc_info:
            get_active_library_id(session, current_user=None)  # type: ignore[arg-type]

        assert exc_info.value.status_code == 404


class TestGetVisibleLibraryIds:
    """Tests for get_visible_library_ids dependency."""

    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_returns_visible_library_ids(
        self,
        mock_ul_repo_cls: MagicMock,
    ) -> None:
        """Return IDs of visible libraries for the user."""
        session = DummySession()
        user = _make_user(user_id=1)
        mock_repo = MagicMock()
        mock_repo.list_visible_for_user.return_value = [
            UserLibrary(id=1, user_id=1, library_id=10, is_visible=True),
            UserLibrary(id=2, user_id=1, library_id=20, is_visible=True),
        ]
        mock_ul_repo_cls.return_value = mock_repo

        result = get_visible_library_ids(session, current_user=user)  # type: ignore[arg-type]

        assert result == [10, 20]

    @patch(
        "bookcard.repositories.user_library_repository.UserLibraryRepository",
    )
    def test_returns_empty_list_when_no_visible(
        self,
        mock_ul_repo_cls: MagicMock,
    ) -> None:
        """Return empty list when user has no visible libraries."""
        session = DummySession()
        user = _make_user(user_id=1)
        mock_repo = MagicMock()
        mock_repo.list_visible_for_user.return_value = []
        mock_ul_repo_cls.return_value = mock_repo

        result = get_visible_library_ids(session, current_user=user)  # type: ignore[arg-type]

        assert result == []

    def test_returns_empty_list_when_user_has_no_id(self) -> None:
        """Return empty list when user id is None."""
        session = DummySession()
        user = User(id=None, username="noone", email="a@b.c", password_hash="h")

        result = get_visible_library_ids(session, current_user=user)  # type: ignore[arg-type]

        assert result == []
