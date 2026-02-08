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

"""Tests for Phase 3 backend changes.

Covers:
- UserLibraryRead library_name enrichment in /api/libraries/me
- UserLibraryRead library_name enrichment in /admin/users/{id}/libraries
- UserLibraryRead schema accepts library_name field
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bookcard.api.routes import admin, libraries
from bookcard.api.schemas.user_libraries import UserLibraryRead
from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.models.user_library import UserLibrary
from tests.conftest import DummySession


def _make_user(*, user_id: int = 1, is_admin: bool = False) -> User:
    """Create a test user."""
    return User(
        id=user_id,
        username=f"user{user_id}",
        email=f"user{user_id}@example.com",
        password_hash="hashed",
        is_admin=is_admin,
    )


def _make_user_library(
    *,
    ul_id: int = 1,
    user_id: int = 1,
    library_id: int = 1,
    is_visible: bool = True,
    is_active: bool = False,
) -> UserLibrary:
    """Create a test user-library association."""
    return UserLibrary(
        id=ul_id,
        user_id=user_id,
        library_id=library_id,
        is_visible=is_visible,
        is_active=is_active,
    )


def _make_library(*, lib_id: int = 1, name: str = "Test Library") -> MagicMock:
    """Create a mock Library with id and name."""
    lib = MagicMock(spec=Library)
    lib.id = lib_id
    lib.name = name
    return lib


# ======================================================================
# UserLibraryRead schema tests
# ======================================================================


class TestUserLibraryReadSchema:
    """Tests for the UserLibraryRead Pydantic schema."""

    def test_library_name_defaults_to_none(self) -> None:
        """Schema should accept records without library_name."""
        ul = _make_user_library()
        read = UserLibraryRead.model_validate(ul, from_attributes=True)
        assert read.library_name is None

    def test_library_name_can_be_set(self) -> None:
        """Schema should accept library_name when explicitly set."""
        ul = _make_user_library()
        read = UserLibraryRead.model_validate(ul, from_attributes=True)
        read.library_name = "Comics"
        assert read.library_name == "Comics"

    def test_library_name_in_serialization(self) -> None:
        """library_name should appear in serialized output."""
        ul = _make_user_library()
        read = UserLibraryRead.model_validate(ul, from_attributes=True)
        read.library_name = "Literature"
        data = read.model_dump()
        assert "library_name" in data
        assert data["library_name"] == "Literature"

    def test_library_name_none_in_serialization(self) -> None:
        """library_name should be None in serialized output when not set."""
        ul = _make_user_library()
        read = UserLibraryRead.model_validate(ul, from_attributes=True)
        data = read.model_dump()
        assert data["library_name"] is None


# ======================================================================
# /api/libraries/me endpoint tests
# ======================================================================


class TestListMyLibrariesEnrichment:
    """Tests for library_name enrichment in list_my_libraries endpoint."""

    def test_returns_library_name_for_each_assignment(self) -> None:
        """Each assignment should include the library's name."""
        session = DummySession()
        user = _make_user(user_id=1)

        ul1 = _make_user_library(ul_id=1, library_id=10)
        ul2 = _make_user_library(ul_id=2, library_id=20)

        lib10 = _make_library(lib_id=10, name="Comics")
        lib20 = _make_library(lib_id=20, name="Literature")

        with (
            patch("bookcard.api.routes.libraries.UserLibraryService") as mock_svc_cls,
            patch("bookcard.api.routes.libraries.LibraryRepository") as mock_repo_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.list_assignments_for_user.return_value = [ul1, ul2]
            mock_svc_cls.return_value = mock_svc

            mock_repo = MagicMock()
            mock_repo.get.side_effect = lambda lid: {10: lib10, 20: lib20}.get(lid)
            mock_repo_cls.return_value = mock_repo

            result = libraries.list_my_libraries(
                session=session,
                current_user=user,
            )

        assert len(result) == 2
        assert result[0].library_name == "Comics"
        assert result[1].library_name == "Literature"

    def test_returns_none_for_missing_library(self) -> None:
        """library_name should be None when the library cannot be found."""
        session = DummySession()
        user = _make_user(user_id=1)

        ul1 = _make_user_library(ul_id=1, library_id=99)

        with (
            patch("bookcard.api.routes.libraries.UserLibraryService") as mock_svc_cls,
            patch("bookcard.api.routes.libraries.LibraryRepository") as mock_repo_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.list_assignments_for_user.return_value = [ul1]
            mock_svc_cls.return_value = mock_svc

            mock_repo = MagicMock()
            mock_repo.get.return_value = None  # Library not found
            mock_repo_cls.return_value = mock_repo

            result = libraries.list_my_libraries(
                session=session,
                current_user=user,
            )

        assert len(result) == 1
        assert result[0].library_name is None

    def test_preserves_other_fields(self) -> None:
        """Enrichment should not alter other fields."""
        session = DummySession()
        user = _make_user(user_id=5)

        ul = _make_user_library(
            ul_id=3, user_id=5, library_id=7, is_visible=True, is_active=True
        )
        lib7 = _make_library(lib_id=7, name="Textbooks")

        with (
            patch("bookcard.api.routes.libraries.UserLibraryService") as mock_svc_cls,
            patch("bookcard.api.routes.libraries.LibraryRepository") as mock_repo_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.list_assignments_for_user.return_value = [ul]
            mock_svc_cls.return_value = mock_svc

            mock_repo = MagicMock()
            mock_repo.get.return_value = lib7
            mock_repo_cls.return_value = mock_repo

            result = libraries.list_my_libraries(
                session=session,
                current_user=user,
            )

        assert len(result) == 1
        r = result[0]
        assert r.id == 3
        assert r.user_id == 5
        assert r.library_id == 7
        assert r.is_visible is True
        assert r.is_active is True
        assert r.library_name == "Textbooks"

    def test_empty_assignments(self) -> None:
        """Should return empty list when user has no assignments."""
        session = DummySession()
        user = _make_user(user_id=1)

        with (
            patch("bookcard.api.routes.libraries.UserLibraryService") as mock_svc_cls,
            patch("bookcard.api.routes.libraries.LibraryRepository") as mock_repo_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.list_assignments_for_user.return_value = []
            mock_svc_cls.return_value = mock_svc
            mock_repo_cls.return_value = MagicMock()

            result = libraries.list_my_libraries(
                session=session,
                current_user=user,
            )

        assert result == []

    def test_rejects_unauthenticated_user(self) -> None:
        """Should raise 401 when user.id is None."""
        from fastapi import HTTPException

        session = DummySession()
        user = _make_user(user_id=1)
        user.id = None

        with pytest.raises(HTTPException, match="authentication_required"):
            libraries.list_my_libraries(
                session=session,
                current_user=user,
            )


# ======================================================================
# Admin /admin/users/{user_id}/libraries endpoint tests
# ======================================================================


class TestAdminListUserLibrariesEnrichment:
    """Tests for library_name enrichment in admin list_user_libraries endpoint."""

    def test_returns_library_name(self) -> None:
        """Admin endpoint should also include library_name."""
        session = DummySession()
        ul = _make_user_library(ul_id=1, user_id=10, library_id=5)
        lib5 = _make_library(lib_id=5, name="Manga")

        with (
            patch("bookcard.api.routes.admin._user_library_service") as mock_svc_fn,
            patch("bookcard.api.routes.admin.LibraryRepository") as mock_repo_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.list_assignments_for_user.return_value = [ul]
            mock_svc_fn.return_value = mock_svc

            mock_repo = MagicMock()
            mock_repo.get.return_value = lib5
            mock_repo_cls.return_value = mock_repo

            result = admin.list_user_libraries(
                user_id=10,
                session=session,
            )

        assert len(result) == 1
        assert result[0].library_name == "Manga"

    def test_returns_none_for_missing_library(self) -> None:
        """Admin endpoint returns None library_name for missing libraries."""
        session = DummySession()
        ul = _make_user_library(ul_id=1, user_id=10, library_id=99)

        with (
            patch("bookcard.api.routes.admin._user_library_service") as mock_svc_fn,
            patch("bookcard.api.routes.admin.LibraryRepository") as mock_repo_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.list_assignments_for_user.return_value = [ul]
            mock_svc_fn.return_value = mock_svc

            mock_repo = MagicMock()
            mock_repo.get.return_value = None
            mock_repo_cls.return_value = mock_repo

            result = admin.list_user_libraries(
                user_id=10,
                session=session,
            )

        assert len(result) == 1
        assert result[0].library_name is None

    def test_deduplicates_library_lookups(self) -> None:
        """Admin endpoint should not look up the same library_id twice."""
        session = DummySession()
        ul1 = _make_user_library(ul_id=1, user_id=10, library_id=5)
        ul2 = _make_user_library(ul_id=2, user_id=10, library_id=5)
        lib5 = _make_library(lib_id=5, name="Comics")

        with (
            patch("bookcard.api.routes.admin._user_library_service") as mock_svc_fn,
            patch("bookcard.api.routes.admin.LibraryRepository") as mock_repo_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.list_assignments_for_user.return_value = [ul1, ul2]
            mock_svc_fn.return_value = mock_svc

            mock_repo = MagicMock()
            mock_repo.get.return_value = lib5
            mock_repo_cls.return_value = mock_repo

            result = admin.list_user_libraries(
                user_id=10,
                session=session,
            )

        assert len(result) == 2
        assert result[0].library_name == "Comics"
        assert result[1].library_name == "Comics"
        # get() should only be called once due to deduplication
        mock_repo.get.assert_called_once_with(5)
