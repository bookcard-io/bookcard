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

"""Tests for library service."""

from __future__ import annotations

import pytest

from fundamental.models.config import Library
from fundamental.repositories.library_repository import LibraryRepository
from fundamental.services.library_service import LibraryService
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
        set_as_active=False,
    )

    assert library.name == "Test Library"
    assert library.calibre_db_path == "/path/to/library"
    assert library.calibre_db_file == "metadata.db"
    assert library.use_split_library is False
    assert library.auto_reconnect is True
    assert library.is_active is False
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
    assert library.is_active is False


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


def test_create_library_set_as_active() -> None:
    """Test create_library deactivates all others when set_as_active=True."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # First call: no existing library
    session.add_exec_result([])
    # Second call: find active libraries (for deactivation)
    session.add_exec_result([])

    library = service.create_library(
        name="Active Library",
        calibre_db_path="/path/to/library",
        set_as_active=True,
    )

    assert library.is_active is True


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
        is_active=False,
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


def test_set_active_library_success() -> None:
    """Test set_active_library succeeds and deactivates others."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Library 1",
        calibre_db_path="/path1",
        calibre_db_file="metadata.db",
        is_active=False,
    )

    active_library = Library(
        id=2,
        name="Library 2",
        calibre_db_path="/path2",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    session.add(library)  # Add to session for get() lookup
    session.add_exec_result([active_library])  # find active libraries

    result = service.set_active_library(1)

    assert result.is_active is True
    assert active_library.is_active is False  # Other library deactivated


def test_set_active_library_not_found() -> None:
    """Test set_active_library raises ValueError when library not found."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.set_active_library(999)


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


def test_deactivate_all() -> None:
    """Test _deactivate_all deactivates all active libraries."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    active_lib1 = Library(
        id=1,
        name="Library 1",
        calibre_db_path="/path1",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    active_lib2 = Library(
        id=2,
        name="Library 2",
        calibre_db_path="/path2",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    session.add_exec_result([active_lib1, active_lib2])

    service._deactivate_all()

    assert active_lib1.is_active is False
    assert active_lib2.is_active is False


def test_deactivate_all_no_active_libraries() -> None:
    """Test _deactivate_all handles no active libraries gracefully."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([])

    service._deactivate_all()  # Should not raise
