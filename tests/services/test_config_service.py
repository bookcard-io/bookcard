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

"""Tests for config service."""

from __future__ import annotations

import pytest

from fundamental.models.config import Library
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.config_service import LibraryService
from tests.conftest import DummySession


def test_list_libraries_delegates_to_repo() -> None:
    """Test list_libraries delegates to repository (covers line 69)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

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

    result = service.list_libraries()

    assert len(result) == 2


def test_get_active_library_delegates_to_repo() -> None:
    """Test get_active_library delegates to repository (covers line 79)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    active_library = Library(
        id=1,
        name="Active Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    session.add_exec_result([active_library])

    result = service.get_active_library()

    assert result is not None
    assert result.is_active is True


def test_get_library_delegates_to_repo() -> None:
    """Test get_library delegates to repository (covers line 94)."""
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

    result = service.get_library(1)

    assert result is not None
    assert result.id == 1


def test_create_library_path_already_exists() -> None:
    """Test create_library raises ValueError when path exists (covers lines 137-140)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    existing_library = Library(
        id=1,
        name="Existing Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    session.add_exec_result([existing_library])  # find_by_path() call

    with pytest.raises(ValueError, match="library_path_already_exists"):
        service.create_library(
            name="New Library",
            calibre_db_path="/path/to/library",
        )


def test_create_library_set_as_active() -> None:
    """Test create_library deactivates others when is_active=True (covers lines 143-144)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    active_library = Library(
        id=1,
        name="Active Library",
        calibre_db_path="/path1",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    session.add_exec_result([])  # find_by_path() call
    session.add_exec_result([active_library])  # find active libraries

    library = service.create_library(
        name="New Library",
        calibre_db_path="/path/to/library",
        is_active=True,
    )

    assert library.is_active is True
    assert active_library.is_active is False


def test_update_library_success() -> None:
    """Test update_library succeeds with all parameters (covers lines 210-223)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Original Name",
        calibre_db_path="/original/path",
        calibre_db_file="metadata.db",
        calibre_uuid=None,
        use_split_library=False,
        split_library_dir=None,
        auto_reconnect=True,
        is_active=False,
    )

    session.add(library)  # Add to session for get() lookup
    session.add_exec_result([])  # find_by_path() call (no conflict)
    session.add_exec_result([])  # list_all() call in _deactivate_all_libraries (if is_active is set)

    updated = service.update_library(
        1,
        name="Updated Name",
        calibre_db_path="/updated/path",
        calibre_db_file="new_metadata.db",
        calibre_uuid="test-uuid",
        use_split_library=True,
        split_library_dir="/split/dir",
        auto_reconnect=False,
        is_active=True,
    )

    assert updated.name == "Updated Name"
    assert updated.calibre_db_path == "/updated/path"
    assert updated.calibre_db_file == "new_metadata.db"
    assert updated.calibre_uuid == "test-uuid"
    assert updated.use_split_library is True
    assert updated.split_library_dir == "/split/dir"
    assert updated.auto_reconnect is False
    assert updated.is_active is True


def test_update_library_not_found() -> None:
    """Test update_library raises ValueError when library not found (covers lines 205-208)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.update_library(999, name="New Name")


def test_validate_and_update_path_none() -> None:
    """Test _validate_and_update_path returns early when calibre_db_path is None (covers line 248)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    original_path = library.calibre_db_path
    service._validate_and_update_path(library, 1, None)

    # Path should remain unchanged
    assert library.calibre_db_path == original_path


def test_validate_and_update_path_no_change() -> None:
    """Test _validate_and_update_path returns early when path unchanged (covers lines 247-251)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    # Library passed directly, no get() call needed

    service._validate_and_update_path(library, 1, "/path/to/library")

    # Should not call find_by_path when path unchanged
    assert library.calibre_db_path == "/path/to/library"


def test_validate_and_update_path_updates_path() -> None:
    """Test _validate_and_update_path updates path when valid (covers line 258)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Library 1",
        calibre_db_path="/path1",
        calibre_db_file="metadata.db",
    )

    session.add_exec_result([])  # find_by_path() call - no conflict

    service._validate_and_update_path(library, 1, "/new/path")

    assert library.calibre_db_path == "/new/path"


def test_validate_and_update_path_conflict() -> None:
    """Test _validate_and_update_path raises ValueError on conflict (covers lines 253-256)."""
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

    # Library passed directly, no get() call needed
    session.add_exec_result([existing_library])  # find_by_path() call

    with pytest.raises(ValueError, match="library_path_already_exists"):
        service._validate_and_update_path(library, 1, "/path2")


def test_update_library_fields_updates_all() -> None:
    """Test _update_library_fields updates all provided fields (covers lines 290-301)."""
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

    service._update_library_fields(
        library,
        name="Updated Name",
        calibre_db_file="new_metadata.db",
        calibre_uuid="test-uuid",
        use_split_library=True,
        split_library_dir="/split/dir",
        auto_reconnect=False,
    )

    assert library.name == "Updated Name"
    assert library.calibre_db_file == "new_metadata.db"
    assert library.calibre_uuid == "test-uuid"
    assert library.use_split_library is True
    assert library.split_library_dir == "/split/dir"
    assert library.auto_reconnect is False


def test_handle_active_status_change_activates() -> None:
    """Test _handle_active_status_change activates library (covers lines 317-323)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=False,
    )

    active_library = Library(
        id=2,
        name="Active Library",
        calibre_db_path="/path2",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    session.add_exec_result([
        active_library
    ])  # list_all() call in _deactivate_all_libraries

    service._handle_active_status_change(library, True)

    assert library.is_active is True
    assert active_library.is_active is False


def test_handle_active_status_change_none() -> None:
    """Test _handle_active_status_change returns early when is_active is None (covers line 318)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    original_status = library.is_active
    service._handle_active_status_change(library, None)

    # Status should remain unchanged
    assert library.is_active == original_status


def test_handle_active_status_change_deactivates() -> None:
    """Test _handle_active_status_change deactivates library (covers lines 338-343)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    service._handle_active_status_change(library, False)

    assert library.is_active is False


def test_deactivate_all_libraries() -> None:
    """Test _deactivate_all_libraries deactivates all (covers lines 363-374)."""
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

    service._deactivate_all_libraries()

    assert active_lib1.is_active is False
    assert active_lib2.is_active is False


def test_delete_library_success() -> None:
    """Test delete_library succeeds (covers lines 338-343)."""
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
    """Test delete_library raises ValueError when library not found (covers lines 338-341)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.delete_library(999)


def test_set_active_library_success() -> None:
    """Test set_active_library succeeds (covers lines 363-374)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=False,
    )

    active_library = Library(
        id=2,
        name="Active Library",
        calibre_db_path="/path2",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    session.add(library)  # Add to session for get() lookup
    session.add_exec_result([
        active_library
    ])  # list_all() call in _deactivate_all_libraries

    result = service.set_active_library(1)

    assert result.is_active is True
    assert active_library.is_active is False


def test_set_active_library_not_found() -> None:
    """Test set_active_library raises ValueError when library not found (covers lines 363-366)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.set_active_library(999)


def test_deactivate_all_libraries_no_active() -> None:
    """Test _deactivate_all_libraries handles no active libraries (covers lines 378-382)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([])

    service._deactivate_all_libraries()  # Should not raise
