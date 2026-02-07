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

"""Tests for user-library API routes (admin and libraries routers)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from bookcard.api.routes import admin, libraries
from bookcard.api.schemas.user_libraries import (
    UserLibraryAssign,
    UserLibraryVisibilityUpdate,
)
from bookcard.models.auth import User
from bookcard.models.user_library import UserLibrary
from tests.conftest import DummySession


def _make_user_library(
    *,
    ul_id: int = 1,
    user_id: int = 1,
    library_id: int = 1,
    is_visible: bool = True,
    is_active: bool = False,
) -> UserLibrary:
    return UserLibrary(
        id=ul_id,
        user_id=user_id,
        library_id=library_id,
        is_visible=is_visible,
        is_active=is_active,
    )


def _make_user(*, user_id: int = 1, is_admin: bool = False) -> User:
    return User(
        id=user_id,
        username=f"user{user_id}",
        email=f"user{user_id}@example.com",
        password_hash="hashed",
        is_admin=is_admin,
    )


# ======================================================================
# Admin routes: /admin/users/{user_id}/libraries
# ======================================================================


class TestAdminListUserLibraries:
    def test_returns_assignments(self) -> None:
        session = DummySession()
        ul1 = _make_user_library(ul_id=1, user_id=10, library_id=1)
        ul2 = _make_user_library(ul_id=2, user_id=10, library_id=2)

        with patch("bookcard.api.routes.admin.UserLibraryService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.list_assignments_for_user.return_value = [ul1, ul2]
            mock_service_cls.return_value = mock_service

            result = admin.list_user_libraries(user_id=10, session=session)

        assert len(result) == 2
        mock_service.list_assignments_for_user.assert_called_once_with(10)

    def test_returns_empty_list(self) -> None:
        session = DummySession()

        with patch("bookcard.api.routes.admin.UserLibraryService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.list_assignments_for_user.return_value = []
            mock_service_cls.return_value = mock_service

            result = admin.list_user_libraries(user_id=10, session=session)

        assert result == []


class TestAdminAssignLibrary:
    def test_success(self) -> None:
        session = DummySession()
        payload = UserLibraryAssign(library_id=5, is_visible=True, is_active=False)
        ul = _make_user_library(ul_id=1, user_id=10, library_id=5)

        with patch("bookcard.api.routes.admin.UserLibraryService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.assign_library_to_user.return_value = ul
            mock_service_cls.return_value = mock_service

            result = admin.assign_library_to_user(
                user_id=10, payload=payload, session=session
            )

        assert result.library_id == 5
        assert session.commit_count == 1

    def test_raises_404_on_missing_library(self) -> None:
        session = DummySession()
        payload = UserLibraryAssign(library_id=99)

        mock_service = MagicMock()
        mock_service.assign_library_to_user.side_effect = ValueError(
            "Library 99 does not exist"
        )

        with (
            patch(
                "bookcard.api.routes.admin.UserLibraryService",
                return_value=mock_service,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            admin.assign_library_to_user(user_id=10, payload=payload, session=session)

        assert exc_info.value.status_code == 404


class TestAdminUnassignLibrary:
    def test_success(self) -> None:
        session = DummySession()

        with patch("bookcard.api.routes.admin.UserLibraryService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service

            result = admin.unassign_library_from_user(
                user_id=10, library_id=5, session=session
            )

        assert result.status_code == 204
        mock_service.unassign_library_from_user.assert_called_once_with(10, 5)
        assert session.commit_count == 1

    def test_raises_404_when_not_found(self) -> None:
        session = DummySession()

        mock_service = MagicMock()
        mock_service.unassign_library_from_user.side_effect = ValueError(
            "No assignment found"
        )

        with (
            patch(
                "bookcard.api.routes.admin.UserLibraryService",
                return_value=mock_service,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            admin.unassign_library_from_user(user_id=10, library_id=99, session=session)

        assert exc_info.value.status_code == 404


class TestAdminSetActiveLibrary:
    def test_success(self) -> None:
        session = DummySession()
        ul = _make_user_library(ul_id=1, user_id=10, library_id=5, is_active=True)

        with patch("bookcard.api.routes.admin.UserLibraryService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.set_active_library_for_user.return_value = ul
            mock_service_cls.return_value = mock_service

            result = admin.set_user_active_library(
                user_id=10, library_id=5, session=session
            )

        assert result.is_active is True
        assert session.commit_count == 1

    def test_raises_404_when_not_found(self) -> None:
        session = DummySession()

        mock_service = MagicMock()
        mock_service.set_active_library_for_user.side_effect = ValueError(
            "No assignment found"
        )

        with (
            patch(
                "bookcard.api.routes.admin.UserLibraryService",
                return_value=mock_service,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            admin.set_user_active_library(user_id=10, library_id=99, session=session)

        assert exc_info.value.status_code == 404


class TestAdminSetVisibility:
    def test_success(self) -> None:
        session = DummySession()
        payload = UserLibraryVisibilityUpdate(is_visible=False)
        ul = _make_user_library(ul_id=1, user_id=10, library_id=5, is_visible=False)

        with patch("bookcard.api.routes.admin.UserLibraryService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.set_visibility_for_user.return_value = ul
            mock_service_cls.return_value = mock_service

            result = admin.set_user_library_visibility(
                user_id=10, library_id=5, payload=payload, session=session
            )

        assert result.is_visible is False
        mock_service.set_visibility_for_user.assert_called_once_with(
            10, 5, is_visible=False
        )
        assert session.commit_count == 1

    def test_raises_404_when_not_found(self) -> None:
        session = DummySession()
        payload = UserLibraryVisibilityUpdate(is_visible=True)

        mock_service = MagicMock()
        mock_service.set_visibility_for_user.side_effect = ValueError(
            "No assignment found"
        )

        with (
            patch(
                "bookcard.api.routes.admin.UserLibraryService",
                return_value=mock_service,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            admin.set_user_library_visibility(
                user_id=10, library_id=99, payload=payload, session=session
            )

        assert exc_info.value.status_code == 404


# ======================================================================
# User routes: /libraries/me
# ======================================================================


class TestListMyLibraries:
    def test_returns_assignments(self) -> None:
        session = DummySession()
        user = _make_user(user_id=7)
        ul1 = _make_user_library(ul_id=1, user_id=7, library_id=1)
        ul2 = _make_user_library(ul_id=2, user_id=7, library_id=2)

        with patch(
            "bookcard.api.routes.libraries.UserLibraryService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service.list_assignments_for_user.return_value = [ul1, ul2]
            mock_service_cls.return_value = mock_service

            result = libraries.list_my_libraries(session=session, current_user=user)

        assert len(result) == 2
        mock_service.list_assignments_for_user.assert_called_once_with(7)

    def test_raises_401_when_user_id_is_none(self) -> None:
        session = DummySession()
        user = _make_user(user_id=1)
        user.id = None

        with pytest.raises(HTTPException) as exc_info:
            libraries.list_my_libraries(session=session, current_user=user)

        assert exc_info.value.status_code == 401


class TestSetMyActiveLibrary:
    def test_success(self) -> None:
        session = DummySession()
        user = _make_user(user_id=7)
        ul = _make_user_library(ul_id=1, user_id=7, library_id=5, is_active=True)

        with patch(
            "bookcard.api.routes.libraries.UserLibraryService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service.set_active_library_for_user.return_value = ul
            mock_service_cls.return_value = mock_service

            result = libraries.set_my_active_library(
                library_id=5, session=session, current_user=user
            )

        assert result.is_active is True
        assert session.commit_count == 1

    def test_raises_404_when_not_found(self) -> None:
        session = DummySession()
        user = _make_user(user_id=7)

        mock_service = MagicMock()
        mock_service.set_active_library_for_user.side_effect = ValueError(
            "No assignment found"
        )

        with (
            patch(
                "bookcard.api.routes.libraries.UserLibraryService",
                return_value=mock_service,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            libraries.set_my_active_library(
                library_id=99, session=session, current_user=user
            )

        assert exc_info.value.status_code == 404

    def test_raises_401_when_user_id_is_none(self) -> None:
        session = DummySession()
        user = _make_user(user_id=1)
        user.id = None

        with pytest.raises(HTTPException) as exc_info:
            libraries.set_my_active_library(
                library_id=5, session=session, current_user=user
            )

        assert exc_info.value.status_code == 401


class TestSetMyLibraryVisibility:
    def test_success(self) -> None:
        session = DummySession()
        user = _make_user(user_id=7)
        ul = _make_user_library(ul_id=1, user_id=7, library_id=5, is_visible=False)

        with patch(
            "bookcard.api.routes.libraries.UserLibraryService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service.set_visibility_for_user.return_value = ul
            mock_service_cls.return_value = mock_service

            result = libraries.set_my_library_visibility(
                library_id=5,
                session=session,
                current_user=user,
                is_visible=False,
            )

        assert result.is_visible is False
        assert session.commit_count == 1

    def test_raises_404_when_not_found(self) -> None:
        session = DummySession()
        user = _make_user(user_id=7)

        mock_service = MagicMock()
        mock_service.set_visibility_for_user.side_effect = ValueError(
            "No assignment found"
        )

        with (
            patch(
                "bookcard.api.routes.libraries.UserLibraryService",
                return_value=mock_service,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            libraries.set_my_library_visibility(
                library_id=99,
                session=session,
                current_user=user,
                is_visible=True,
            )

        assert exc_info.value.status_code == 404

    def test_raises_401_when_user_id_is_none(self) -> None:
        session = DummySession()
        user = _make_user(user_id=1)
        user.id = None

        with pytest.raises(HTTPException) as exc_info:
            libraries.set_my_library_visibility(
                library_id=5,
                session=session,
                current_user=user,
                is_visible=True,
            )

        assert exc_info.value.status_code == 401
