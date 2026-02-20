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

"""Tests for config repository."""

from __future__ import annotations

from bookcard.models.config import Library
from bookcard.repositories.config_repository import LibraryRepository
from tests.conftest import DummySession


def test_list_all_returns_all_libraries() -> None:
    """Test list_all returns all libraries ordered by creation date (covers lines 65-66)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]

    library1 = Library(
        id=1,
        name="Library 1",
        calibre_db_path="/path1",
        calibre_db_file="metadata.db",
    )
    library2 = Library(
        id=2,
        name="Library 2",
        calibre_db_path="/path2",
        calibre_db_file="metadata.db",
    )

    session.add_exec_result([library1, library2])
    result = repo.list_all()
    assert len(result) == 2
    assert result[0].id == 1
    assert result[1].id == 2


def test_find_by_path_returns_matching_library() -> None:
    """Test find_by_path returns library with matching path (covers lines 81-82)."""
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


def test_find_by_path_returns_none() -> None:
    """Test find_by_path returns None when not found (covers lines 81-82)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.find_by_path("/nonexistent/path")
    assert result is None
