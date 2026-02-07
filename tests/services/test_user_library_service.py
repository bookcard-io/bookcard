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

"""Tests for user-library service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.models.config import Library
from bookcard.models.user_library import UserLibrary
from bookcard.services.user_library_service import UserLibraryService
from tests.conftest import DummySession


def _make_user_library(
    *,
    ul_id: int | None = None,
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


def _make_library(*, lib_id: int = 1, name: str = "Library") -> Library:
    return Library(
        id=lib_id,
        name=name,
        calibre_db_path=f"/path/{lib_id}",
        calibre_db_file="metadata.db",
    )


def _build_service() -> tuple[UserLibraryService, DummySession, MagicMock, MagicMock]:
    session = DummySession()
    ul_repo = MagicMock()
    lib_repo = MagicMock()
    service = UserLibraryService(
        session=session,  # type: ignore[arg-type]
        user_library_repo=ul_repo,
        library_repo=lib_repo,
    )
    return service, session, ul_repo, lib_repo


# ------------------------------------------------------------------
# Query delegation
# ------------------------------------------------------------------


def test_get_active_library_for_user_delegates() -> None:
    service, _, ul_repo, _ = _build_service()
    lib = _make_library(lib_id=3)
    ul_repo.get_active_library_for_user.return_value = lib

    result = service.get_active_library_for_user(user_id=10)
    assert result is lib
    ul_repo.get_active_library_for_user.assert_called_once_with(10)


def test_get_active_library_for_user_returns_none() -> None:
    service, _, ul_repo, _ = _build_service()
    ul_repo.get_active_library_for_user.return_value = None

    assert service.get_active_library_for_user(user_id=10) is None


def test_get_visible_libraries_for_user_delegates() -> None:
    service, _, ul_repo, _ = _build_service()
    libs = [_make_library(lib_id=1), _make_library(lib_id=2, name="Lib2")]
    ul_repo.get_visible_libraries_for_user.return_value = libs

    result = service.get_visible_libraries_for_user(user_id=1)
    assert result == libs
    ul_repo.get_visible_libraries_for_user.assert_called_once_with(1)


def test_get_visible_library_ids_for_user() -> None:
    service, _, ul_repo, _ = _build_service()
    ul_repo.list_visible_for_user.return_value = [
        _make_user_library(library_id=10),
        _make_user_library(library_id=20),
    ]

    result = service.get_visible_library_ids_for_user(user_id=1)
    assert result == [10, 20]


def test_get_visible_library_ids_for_user_empty() -> None:
    service, _, ul_repo, _ = _build_service()
    ul_repo.list_visible_for_user.return_value = []

    result = service.get_visible_library_ids_for_user(user_id=1)
    assert result == []


def test_list_assignments_for_user_delegates() -> None:
    service, _, ul_repo, _ = _build_service()
    assignments = [_make_user_library(ul_id=1), _make_user_library(ul_id=2)]
    ul_repo.list_for_user.return_value = assignments

    result = service.list_assignments_for_user(user_id=5)
    assert result == assignments
    ul_repo.list_for_user.assert_called_once_with(5)


def test_list_assignments_for_library_delegates() -> None:
    service, _, ul_repo, _ = _build_service()
    assignments = [_make_user_library(ul_id=1)]
    ul_repo.list_for_library.return_value = assignments

    result = service.list_assignments_for_library(library_id=3)
    assert result == assignments
    ul_repo.list_for_library.assert_called_once_with(3)


# ------------------------------------------------------------------
# assign_library_to_user
# ------------------------------------------------------------------


def test_assign_library_to_user_creates_new() -> None:
    service, session, ul_repo, lib_repo = _build_service()
    lib_repo.get.return_value = _make_library(lib_id=5)
    ul_repo.find_by_user_and_library.return_value = None

    result = service.assign_library_to_user(user_id=1, library_id=5)

    assert result.user_id == 1
    assert result.library_id == 5
    assert result.is_visible is True
    assert result.is_active is False
    ul_repo.add.assert_called_once()
    assert session.flush_count == 1


def test_assign_library_to_user_returns_existing() -> None:
    service, session, ul_repo, lib_repo = _build_service()
    lib_repo.get.return_value = _make_library(lib_id=5)
    existing = _make_user_library(ul_id=99, user_id=1, library_id=5)
    ul_repo.find_by_user_and_library.return_value = existing

    result = service.assign_library_to_user(user_id=1, library_id=5)

    assert result is existing
    ul_repo.add.assert_not_called()
    assert session.flush_count == 0


def test_assign_library_to_user_raises_for_missing_library() -> None:
    service, _, _, lib_repo = _build_service()
    lib_repo.get.return_value = None

    with pytest.raises(ValueError, match="Library 99 does not exist"):
        service.assign_library_to_user(user_id=1, library_id=99)


def test_assign_library_to_user_with_active_deactivates_others() -> None:
    service, _session, ul_repo, lib_repo = _build_service()
    lib_repo.get.return_value = _make_library(lib_id=5)
    ul_repo.find_by_user_and_library.return_value = None

    result = service.assign_library_to_user(user_id=1, library_id=5, is_active=True)

    ul_repo.deactivate_all_for_user.assert_called_once_with(1)
    assert result.is_active is True


def test_assign_library_to_user_not_active_skips_deactivation() -> None:
    service, _, ul_repo, lib_repo = _build_service()
    lib_repo.get.return_value = _make_library(lib_id=5)
    ul_repo.find_by_user_and_library.return_value = None

    service.assign_library_to_user(user_id=1, library_id=5, is_active=False)

    ul_repo.deactivate_all_for_user.assert_not_called()


def test_assign_library_to_user_custom_visibility() -> None:
    service, _, ul_repo, lib_repo = _build_service()
    lib_repo.get.return_value = _make_library(lib_id=5)
    ul_repo.find_by_user_and_library.return_value = None

    result = service.assign_library_to_user(user_id=1, library_id=5, is_visible=False)

    assert result.is_visible is False


# ------------------------------------------------------------------
# unassign_library_from_user
# ------------------------------------------------------------------


def test_unassign_library_from_user_deletes() -> None:
    service, session, ul_repo, _ = _build_service()
    ul = _make_user_library(ul_id=10, user_id=1, library_id=5)
    ul_repo.find_by_user_and_library.return_value = ul

    service.unassign_library_from_user(user_id=1, library_id=5)

    ul_repo.delete.assert_called_once_with(ul)
    assert session.flush_count == 1


def test_unassign_library_from_user_raises_when_not_found() -> None:
    service, _, ul_repo, _ = _build_service()
    ul_repo.find_by_user_and_library.return_value = None

    with pytest.raises(ValueError, match="No assignment found"):
        service.unassign_library_from_user(user_id=1, library_id=99)


# ------------------------------------------------------------------
# set_active_library_for_user
# ------------------------------------------------------------------


def test_set_active_library_for_user_activates() -> None:
    service, session, ul_repo, _ = _build_service()
    ul = _make_user_library(ul_id=10, user_id=1, library_id=5, is_active=False)
    ul_repo.find_by_user_and_library.return_value = ul

    result = service.set_active_library_for_user(user_id=1, library_id=5)

    assert result.is_active is True
    ul_repo.deactivate_all_for_user.assert_called_once_with(1)
    assert session.flush_count == 1


def test_set_active_library_for_user_raises_when_not_found() -> None:
    service, _, ul_repo, _ = _build_service()
    ul_repo.find_by_user_and_library.return_value = None

    with pytest.raises(ValueError, match="No assignment found"):
        service.set_active_library_for_user(user_id=1, library_id=99)


# ------------------------------------------------------------------
# set_visibility_for_user
# ------------------------------------------------------------------


def test_set_visibility_for_user_hides() -> None:
    service, session, ul_repo, _ = _build_service()
    ul = _make_user_library(ul_id=10, user_id=1, library_id=5, is_visible=True)
    ul_repo.find_by_user_and_library.return_value = ul

    result = service.set_visibility_for_user(user_id=1, library_id=5, is_visible=False)

    assert result.is_visible is False
    assert session.flush_count == 1


def test_set_visibility_for_user_shows() -> None:
    service, _session, ul_repo, _ = _build_service()
    ul = _make_user_library(ul_id=10, user_id=1, library_id=5, is_visible=False)
    ul_repo.find_by_user_and_library.return_value = ul

    result = service.set_visibility_for_user(user_id=1, library_id=5, is_visible=True)

    assert result.is_visible is True


def test_set_visibility_for_user_raises_when_not_found() -> None:
    service, _, ul_repo, _ = _build_service()
    ul_repo.find_by_user_and_library.return_value = None

    with pytest.raises(ValueError, match="No assignment found"):
        service.set_visibility_for_user(user_id=1, library_id=99, is_visible=True)
