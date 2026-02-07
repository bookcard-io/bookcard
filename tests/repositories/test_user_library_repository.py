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

"""Tests for user-library repository."""

from __future__ import annotations

from bookcard.models.config import Library
from bookcard.models.user_library import UserLibrary
from bookcard.repositories.user_library_repository import UserLibraryRepository
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


def _make_library(
    *, lib_id: int = 1, name: str = "Library", is_active: bool = False
) -> Library:
    return Library(
        id=lib_id,
        name=name,
        calibre_db_path=f"/path/{lib_id}",
        calibre_db_file="metadata.db",
        is_active=is_active,
    )


# ------------------------------------------------------------------
# Initialization
# ------------------------------------------------------------------


def test_init_sets_model_type() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]
    assert repo._session is session
    assert repo._model_type is UserLibrary


# ------------------------------------------------------------------
# find_by_user_and_library
# ------------------------------------------------------------------


def test_find_by_user_and_library_found() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    ul = _make_user_library(ul_id=1, user_id=10, library_id=20)
    session.add_exec_result([ul])

    result = repo.find_by_user_and_library(10, 20)
    assert result is not None
    assert result.user_id == 10
    assert result.library_id == 20


def test_find_by_user_and_library_not_found() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_user_and_library(10, 99)
    assert result is None


# ------------------------------------------------------------------
# find_active_for_user
# ------------------------------------------------------------------


def test_find_active_for_user_found() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    ul = _make_user_library(ul_id=1, user_id=5, library_id=3, is_active=True)
    session.add_exec_result([ul])

    result = repo.find_active_for_user(5)
    assert result is not None
    assert result.is_active is True
    assert result.library_id == 3


def test_find_active_for_user_none() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_active_for_user(5)
    assert result is None


# ------------------------------------------------------------------
# list_visible_for_user
# ------------------------------------------------------------------


def test_list_visible_for_user_returns_visible() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    ul1 = _make_user_library(ul_id=1, user_id=1, library_id=10, is_visible=True)
    ul2 = _make_user_library(ul_id=2, user_id=1, library_id=20, is_visible=True)
    session.add_exec_result([ul1, ul2])

    result = repo.list_visible_for_user(1)
    assert len(result) == 2


def test_list_visible_for_user_empty() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.list_visible_for_user(1)
    assert result == []


# ------------------------------------------------------------------
# list_for_user
# ------------------------------------------------------------------


def test_list_for_user_returns_all() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    ul1 = _make_user_library(ul_id=1, user_id=1, library_id=10, is_visible=True)
    ul2 = _make_user_library(ul_id=2, user_id=1, library_id=20, is_visible=False)
    session.add_exec_result([ul1, ul2])

    result = repo.list_for_user(1)
    assert len(result) == 2


def test_list_for_user_empty() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.list_for_user(999)
    assert result == []


# ------------------------------------------------------------------
# list_for_library
# ------------------------------------------------------------------


def test_list_for_library_returns_all() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    ul1 = _make_user_library(ul_id=1, user_id=1, library_id=10)
    ul2 = _make_user_library(ul_id=2, user_id=2, library_id=10)
    session.add_exec_result([ul1, ul2])

    result = repo.list_for_library(10)
    assert len(result) == 2


def test_list_for_library_empty() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.list_for_library(999)
    assert result == []


# ------------------------------------------------------------------
# deactivate_all_for_user
# ------------------------------------------------------------------


def test_deactivate_all_for_user_deactivates_active() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    ul = _make_user_library(ul_id=1, user_id=5, library_id=3, is_active=True)
    session.add_exec_result([ul])

    repo.deactivate_all_for_user(5)
    assert ul.is_active is False
    assert ul in session.added


def test_deactivate_all_for_user_no_active() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    repo.deactivate_all_for_user(5)
    # No error, no entities modified
    assert session.added == []


# ------------------------------------------------------------------
# get_active_library_for_user
# ------------------------------------------------------------------


def test_get_active_library_for_user_found() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    lib = _make_library(lib_id=3, name="Active Lib", is_active=True)
    session.add_exec_result([lib])

    result = repo.get_active_library_for_user(5)
    assert result is not None
    assert result.id == 3
    assert result.name == "Active Lib"


def test_get_active_library_for_user_none() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.get_active_library_for_user(5)
    assert result is None


# ------------------------------------------------------------------
# get_visible_libraries_for_user
# ------------------------------------------------------------------


def test_get_visible_libraries_for_user_returns_libraries() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    lib1 = _make_library(lib_id=1, name="Comics")
    lib2 = _make_library(lib_id=2, name="Literature")
    session.add_exec_result([lib1, lib2])

    result = repo.get_visible_libraries_for_user(5)
    assert len(result) == 2
    assert result[0].name == "Comics"
    assert result[1].name == "Literature"


def test_get_visible_libraries_for_user_empty() -> None:
    session = DummySession()
    repo = UserLibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.get_visible_libraries_for_user(5)
    assert result == []
