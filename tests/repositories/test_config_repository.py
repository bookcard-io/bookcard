# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for config repository."""

from __future__ import annotations

from fundamental.models.config import Library
from fundamental.repositories.config_repository import LibraryRepository
from tests.conftest import DummySession


def test_get_active_returns_active_library() -> None:
    """Test get_active returns active library (covers lines 54-55)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]

    active_library = Library(
        id=1,
        name="Active Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    session.add_exec_result([active_library])
    result = repo.get_active()
    assert result is not None
    assert result.id == 1
    assert result.is_active is True


def test_get_active_returns_none() -> None:
    """Test get_active returns None when no active library (covers lines 54-55)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]

    session.add_exec_result([])
    result = repo.get_active()
    assert result is None


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
