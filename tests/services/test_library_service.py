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

"""Tests for library service."""

from __future__ import annotations

import pytest

from bookcard.models.config import Library
from bookcard.repositories.library_repository import LibraryRepository
from bookcard.services.library_service import LibraryService
from tests.conftest import DummySession


def test_library_service_init() -> None:
    """Test LibraryService initialization."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]
    assert service._session is session
    assert service._library_repo is repo


def test_create_library_success() -> None:
    """Test create_library succeeds with valid parameters."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([])  # No existing library with same path

    library = service.create_library(
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        use_split_library=False,
        split_library_dir=None,
        auto_reconnect=True,
    )

    assert library.name == "Test Library"
    assert library.calibre_db_path == "/path/to/library"
    assert library.calibre_db_file == "metadata.db"
    assert library.use_split_library is False
    assert library.auto_reconnect is True
    assert library in session.added


def test_create_library_with_defaults() -> None:
    """Test create_library uses default values."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([])

    library = service.create_library(
        name="Test Library",
        calibre_db_path="/path/to/library",
    )

    assert library.calibre_db_file == "metadata.db"
    assert library.use_split_library is False
    assert library.auto_reconnect is True


def test_create_library_path_already_exists() -> None:
    """Test create_library raises ValueError when path already exists."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    existing_library = Library(
        id=1,
        name="Existing Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    session.add_exec_result([existing_library])

    with pytest.raises(ValueError, match="library_path_already_exists"):
        service.create_library(
            name="New Library",
            calibre_db_path="/path/to/library",
        )


def test_update_library_success() -> None:
    """Test update_library succeeds with valid parameters."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Original Name",
        calibre_db_path="/original/path",
        calibre_db_file="metadata.db",
    )

    session.add(library)  # Add to session for get() lookup
    session.add_exec_result([])  # find_by_path() call (no conflict)

    updated = service.update_library(
        1,
        name="Updated Name",
        calibre_db_path="/updated/path",
        calibre_db_file="new_metadata.db",
    )

    assert updated.name == "Updated Name"
    assert updated.calibre_db_path == "/updated/path"
    assert updated.calibre_db_file == "new_metadata.db"


def test_update_library_not_found() -> None:
    """Test update_library raises ValueError when library not found."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.update_library(999, name="New Name")


def test_update_library_path_conflict() -> None:
    """Test update_library raises ValueError when path conflicts with another library."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Library 1",
        calibre_db_path="/path1",
        calibre_db_file="metadata.db",
    )

    existing_library = Library(
        id=2,
        name="Library 2",
        calibre_db_path="/path2",
        calibre_db_file="metadata.db",
    )

    session.add(library)  # Add to session for get() lookup
    session.add_exec_result([existing_library])  # find_by_path() finds conflict

    with pytest.raises(ValueError, match="library_path_already_exists"):
        service.update_library(1, calibre_db_path="/path2")


def test_update_library_no_path_change() -> None:
    """Test update_library doesn't check path conflict when path unchanged."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Original Name",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    session.add(library)  # Add to session for get() lookup

    updated = service.update_library(1, name="Updated Name")
    assert updated.name == "Updated Name"
    assert updated.calibre_db_path == "/path/to/library"


def test_update_library_updates_calibre_uuid() -> None:
    """Test update_library updates calibre_uuid (covers line 184)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        calibre_uuid=None,
    )

    session.add(library)  # Add to session for get() lookup

    updated = service.update_library(1, calibre_uuid="test-uuid-123")

    assert updated.calibre_uuid == "test-uuid-123"


def test_update_library_partial_update() -> None:
    """Test update_library updates only provided fields."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Original Name",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        use_split_library=False,
        split_library_dir=None,
        auto_reconnect=True,
    )

    session.add(library)  # Add to session for get() lookup
    session.add_exec_result([])  # find_by_path() call

    updated = service.update_library(
        1,
        name="Updated Name",
        use_split_library=True,
        split_library_dir="/split/dir",
        auto_reconnect=False,
    )

    assert updated.name == "Updated Name"
    assert updated.use_split_library is True
    assert updated.split_library_dir == "/split/dir"
    assert updated.auto_reconnect is False


def test_delete_library_success() -> None:
    """Test delete_library succeeds."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    session.add(library)  # Add to session for get() lookup

    service.delete_library(1)

    assert library in session.deleted


def test_delete_library_not_found() -> None:
    """Test delete_library raises ValueError when library not found."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.delete_library(999)


def test_get_library_stats_success() -> None:
    """Test get_library_stats returns statistics (covers lines 273-282)."""
    from unittest.mock import MagicMock, patch

    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    session.add(library)  # Add to session for get() lookup

    mock_stats = {
        "total_books": 100,
        "total_series": 20,
        "total_authors": 50,
        "total_content_size": 1024000,
    }

    with patch(
        "bookcard.services.library_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.get_library_stats.return_value = mock_stats
        mock_repo_class.return_value = mock_repo

        result = service.get_library_stats(1)

        assert result == mock_stats
        mock_repo_class.assert_called_once_with(
            calibre_db_path="/path/to/library",
            calibre_db_file="metadata.db",
        )
        mock_repo.get_library_stats.assert_called_once()


def test_get_library_stats_not_found() -> None:
    """Test get_library_stats raises when library not found (covers lines 273-276)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.get_library_stats(999)
