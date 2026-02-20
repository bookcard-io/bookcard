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

"""Tests for library repository."""

from __future__ import annotations

from bookcard.models.config import Library
from bookcard.repositories.library_repository import LibraryRepository
from tests.conftest import DummySession


def test_library_repository_init() -> None:
    """Test LibraryRepository initialization."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    assert repo._session is session
    assert repo._model_type is Library


def test_find_by_path_returns_matching_library() -> None:
    """Test find_by_path returns library with matching path."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    session.add_exec_result([library])
    result = repo.find_by_path("/path/to/library")
    assert result is not None
    assert result.id == 1
    assert result.calibre_db_path == "/path/to/library"


def test_find_by_path_returns_none_when_not_found() -> None:
    """Test find_by_path returns None when no library matches path."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_path("/nonexistent/path")
    assert result is None
