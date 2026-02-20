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

"""Tests for config service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import (
    EPUBFixerConfig,
    FileHandlingConfig,
    Library,
    ScheduledTasksConfig,
)
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import (
    BasicConfigService,
    EPUBFixerConfigService,
    FileHandlingConfigService,
    LibraryService,
    ScheduledTasksConfigService,
)
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
    """Test create_library creates library (is_active no longer managed by service)."""
    from unittest.mock import MagicMock, patch

    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    session.add_exec_result([])  # find_by_path() call

    # Mock the database initializer to prevent actual file system operations
    with (
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer"
        ) as mock_initializer_class,
        patch("pathlib.Path.exists") as mock_exists,
    ):
        mock_exists.return_value = False  # Database doesn't exist
        mock_initializer = MagicMock()
        mock_initializer_class.return_value = mock_initializer

        library = service.create_library(
            name="New Library",
            calibre_db_path="/path/to/library",
            is_active=True,
        )

        assert library.name == "New Library"


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

    updated = service.update_library(
        1,
        name="Updated Name",
        calibre_db_path="/updated/path",
        calibre_db_file="new_metadata.db",
        calibre_uuid="test-uuid",
        use_split_library=True,
        split_library_dir="/split/dir",
        auto_reconnect=False,
    )

    assert updated.name == "Updated Name"
    assert updated.calibre_db_path == "/updated/path"
    assert updated.calibre_db_file == "new_metadata.db"
    assert updated.calibre_uuid == "test-uuid"
    assert updated.use_split_library is True
    assert updated.split_library_dir == "/split/dir"
    assert updated.auto_reconnect is False


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


def test_handle_active_status_change_is_noop() -> None:
    """Test _handle_active_status_change is a no-op (deprecated)."""
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

    original_status = library.is_active
    service._handle_active_status_change(library, True)

    # No-op: is_active should remain unchanged
    assert library.is_active == original_status


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
    """Test set_active_library returns library (is_active no longer toggled)."""
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

    session.add(library)  # Add to session for get() lookup

    result = service.set_active_library(1)

    assert result is library


def test_set_active_library_not_found() -> None:
    """Test set_active_library raises ValueError when library not found."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.set_active_library(999)


def test_get_library_stats_success() -> None:
    """Test get_library_stats returns statistics (covers lines 404-413)."""
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
        "bookcard.services.config_service.CalibreBookRepository"
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
    """Test get_library_stats raises when library not found (covers lines 404-407)."""
    session = DummySession()
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    service = LibraryService(session, repo)  # type: ignore[arg-type]

    # No entity added, so get() will return None

    with pytest.raises(ValueError, match="library_not_found"):
        service.get_library_stats(999)


# ============================================================================
# Tests for create_library - missing coverage
# ============================================================================


@pytest.fixture
def library_service(session: DummySession) -> LibraryService:
    """Create a LibraryService instance for testing.

    Parameters
    ----------
    session : DummySession
        Test session.

    Returns
    -------
    LibraryService
        Library service instance.
    """
    repo = LibraryRepository(session)  # type: ignore[arg-type]
    return LibraryService(session, repo)  # type: ignore[arg-type]


def test_create_library_with_auto_generated_path(
    library_service: LibraryService,
) -> None:
    """Test create_library auto-generates path when calibre_db_path is None (covers line 150).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    """
    session = library_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # find_by_path() call - no existing library

    with (
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer"
        ) as mock_initializer_class,
        patch("pathlib.Path.exists") as mock_exists,
        patch(
            "bookcard.services.config_service.LibraryService._get_default_library_directory"
        ) as mock_get_dir,
        patch(
            "bookcard.services.config_service.LibraryService._sync_shelves_for_library"
        ),
    ):
        mock_exists.return_value = False
        mock_get_dir.return_value = "/default/lib/dir"
        mock_initializer = MagicMock()
        mock_initializer_class.return_value = mock_initializer

        library = library_service.create_library(name="Test Library")

        assert library.name == "Test Library"
        assert library.calibre_db_path is not None
        mock_initializer.initialize.assert_called_once()


def test_create_library_existing_database_invalid(
    library_service: LibraryService,
) -> None:
    """Test create_library raises ValueError when existing database is invalid (covers lines 167-171).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    """
    session = library_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # find_by_path() call

    with (
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer.validate_existing_database"
        ) as mock_validate,
        patch("pathlib.Path.exists") as mock_exists,
    ):
        mock_exists.return_value = True
        mock_validate.return_value = False

        with pytest.raises(ValueError, match="Invalid Calibre database"):
            library_service.create_library(
                name="Test Library",
                calibre_db_path="/path/to/library",
            )


def test_create_library_existing_database_valid(
    library_service: LibraryService,
) -> None:
    """Test create_library succeeds when existing database is valid (covers lines 167-171).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    """
    session = library_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # find_by_path() call

    with (
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer.validate_existing_database"
        ) as mock_validate,
        patch("pathlib.Path.exists") as mock_exists,
        patch(
            "bookcard.services.config_service.LibraryService._sync_shelves_for_library"
        ),
    ):
        mock_exists.return_value = True
        mock_validate.return_value = True

        library = library_service.create_library(
            name="Test Library",
            calibre_db_path="/path/to/library",
            is_active=True,
        )

        assert library.name == "Test Library"
        assert library.calibre_db_path == "/path/to/library"


def test_create_library_file_exists_error(
    library_service: LibraryService,
) -> None:
    """Test create_library handles FileExistsError during initialization (covers lines 180-187).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    """
    session = library_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # find_by_path() call

    with (
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer"
        ) as mock_initializer_class,
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer.validate_existing_database"
        ) as mock_validate,
        patch("pathlib.Path.exists") as mock_exists,
        patch(
            "bookcard.services.config_service.LibraryService._sync_shelves_for_library"
        ),
    ):
        mock_exists.return_value = False
        mock_initializer = MagicMock()
        mock_initializer.initialize.side_effect = FileExistsError("File exists")
        mock_initializer_class.return_value = mock_initializer
        mock_validate.return_value = True  # Valid after creation

        library = library_service.create_library(
            name="Test Library",
            calibre_db_path="/path/to/library",
            is_active=True,
        )

        assert library.name == "Test Library"


def test_create_library_file_exists_error_invalid_db(
    library_service: LibraryService,
) -> None:
    """Test create_library raises ValueError when FileExistsError and database is invalid (covers lines 180-187).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    """
    session = library_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # find_by_path() call

    with (
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer"
        ) as mock_initializer_class,
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer.validate_existing_database"
        ) as mock_validate,
        patch("pathlib.Path.exists") as mock_exists,
    ):
        mock_exists.return_value = False
        mock_initializer = MagicMock()
        mock_initializer.initialize.side_effect = FileExistsError("File exists")
        mock_initializer_class.return_value = mock_initializer
        mock_validate.return_value = False  # Invalid database

        with pytest.raises(ValueError, match="Invalid Calibre database"):
            library_service.create_library(
                name="Test Library",
                calibre_db_path="/path/to/library",
            )


@pytest.mark.parametrize(
    ("exception_class", "exception_msg"),
    [
        (PermissionError, "Permission denied"),
        (ValueError, "Invalid path"),
    ],
)
def test_create_library_initialization_errors(
    library_service: LibraryService,
    exception_class: type[Exception],
    exception_msg: str,
) -> None:
    """Test create_library handles PermissionError and ValueError during initialization (covers lines 188-190).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    exception_class : type[Exception]
        Exception class to raise.
    exception_msg : str
        Exception message.
    """
    session = library_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # find_by_path() call

    with (
        patch(
            "bookcard.services.config_service.CalibreDatabaseInitializer"
        ) as mock_initializer_class,
        patch("pathlib.Path.exists") as mock_exists,
    ):
        mock_exists.return_value = False
        mock_initializer = MagicMock()
        mock_initializer.initialize.side_effect = exception_class(exception_msg)
        mock_initializer_class.return_value = mock_initializer

        with pytest.raises(ValueError, match="Failed to initialize database"):
            library_service.create_library(
                name="Test Library",
                calibre_db_path="/path/to/library",
            )


# ============================================================================
# Tests for _generate_library_path
# ============================================================================


@pytest.mark.parametrize(
    ("name", "existing_paths", "expected_suffix"),
    [
        ("My Library", [], ""),
        ("My Library", ["/default/lib/my-library"], "-1"),
        ("My Library", ["/default/lib/my-library", "/default/lib/my-library-1"], "-2"),
        ("Library@#$%", [], ""),  # Special chars removed
        ("", [], ""),  # Empty name defaults to "library"
        ("   ", [], ""),  # Whitespace-only defaults to "library"
    ],
)
def test_generate_library_path(
    library_service: LibraryService,
    name: str,
    existing_paths: list[str],
    expected_suffix: str,
) -> None:
    """Test _generate_library_path generates correct paths (covers lines 231-248).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    name : str
        Library name to generate path for.
    existing_paths : list[str]
        List of existing paths to simulate conflicts.
    expected_suffix : str
        Expected suffix in generated path.
    """
    session = library_service._session

    # Setup find_by_path results for conflict checking
    for existing_path in existing_paths:
        existing_lib = Library(
            id=len(session.added) + 1,  # type: ignore[possibly-missing-attribute]
            name="Existing",
            calibre_db_path=existing_path,
            calibre_db_file="metadata.db",
        )
        session.add_exec_result([existing_lib])  # type: ignore[possibly-missing-attribute]

    # Add one more empty result for the final call
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]

    with (
        patch(
            "bookcard.services.config_service.LibraryService._get_default_library_directory"
        ) as mock_get_dir,
    ):
        mock_get_dir.return_value = "/default/lib/dir"

        result = library_service._generate_library_path(name)

        assert result.startswith("/default/lib/dir/")
        if expected_suffix:
            assert result.endswith(expected_suffix)


# ============================================================================
# Tests for _parse_library_path
# ============================================================================


@pytest.mark.parametrize(
    ("path", "default_filename", "expected_dir", "expected_file"),
    [
        ("/path/to/file.db", "metadata.db", "/path/to", "file.db"),  # File path
        ("/path/to/dir", "metadata.db", "/path/to/dir", "metadata.db"),  # Directory
        (
            "/path/to/nonexistent.db",
            "metadata.db",
            "/path/to",
            "nonexistent.db",
        ),  # File-like (has extension)
        (
            "/path/to/nonexistent",
            "metadata.db",
            "/path/to/nonexistent",
            "metadata.db",
        ),  # Dir-like (no extension)
    ],
)
def test_parse_library_path(
    path: str,
    default_filename: str,
    expected_dir: str,
    expected_file: str,
) -> None:
    """Test _parse_library_path parses different path types (covers lines 276, 279, 283, 286-288).

    Parameters
    ----------
    path : str
        Path to parse.
    default_filename : str
        Default filename to use.
    expected_dir : str
        Expected directory path.
    expected_file : str
        Expected filename.
    """
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.is_file") as mock_is_file,
        patch("pathlib.Path.is_dir") as mock_is_dir,
    ):
        # Simulate different scenarios
        if path.endswith(".db") and "nonexistent" not in path:
            # Existing file
            mock_exists.return_value = True
            mock_is_file.return_value = True
            mock_is_dir.return_value = False
        elif "nonexistent" not in path:
            # Existing directory
            mock_exists.return_value = True
            mock_is_file.return_value = False
            mock_is_dir.return_value = True
        else:
            # Non-existent path
            mock_exists.return_value = False
            mock_is_file.return_value = False
            mock_is_dir.return_value = False

        result_dir, result_file = LibraryService._parse_library_path(
            path, default_filename
        )

        assert result_dir == expected_dir
        assert result_file == expected_file


def test_parse_library_path_oserror() -> None:
    """Test _parse_library_path handles OSError (covers lines 286-288).

    Returns
    -------
    None
    """
    with patch("pathlib.Path.exists", side_effect=OSError("Permission denied")):
        result_dir, result_file = LibraryService._parse_library_path(
            "/path/to/test", "metadata.db"
        )

        assert result_dir == "/path/to/test"
        assert result_file == "metadata.db"


def test_parse_library_path_valueerror() -> None:
    """Test _parse_library_path handles ValueError (covers lines 286-288).

    Returns
    -------
    None
    """
    with patch("pathlib.Path.exists", side_effect=ValueError("Invalid path")):
        result_dir, result_file = LibraryService._parse_library_path(
            "/path/to/test", "metadata.db"
        )

        assert result_dir == "/path/to/test"
        assert result_file == "metadata.db"


# ============================================================================
# Tests for _get_default_library_directory
# ============================================================================


def test_get_default_library_directory_with_env_var() -> None:
    """Test _get_default_library_directory uses environment variable (covers lines 304-306).

    Returns
    -------
    None
    """
    with patch(
        "bookcard.services.config_service.os.getenv",
        return_value="/custom/lib/dir",
    ) as mock_getenv:
        result = LibraryService._get_default_library_directory()
        assert result == "/custom/lib/dir"
        mock_getenv.assert_called_once_with("BOOKCARD_DEFAULT_LIBRARY_DIR")


def test_get_default_library_directory_without_env_var() -> None:
    """Test _get_default_library_directory uses AppConfig when env var not set (covers lines 308-310).

    Returns
    -------
    None
    """
    with (
        patch(
            "bookcard.services.config_service.os.getenv", return_value=None
        ) as mock_getenv,
        patch("bookcard.services.config_service.AppConfig.from_env") as mock_config,
    ):
        mock_config_instance = MagicMock()
        mock_config_instance.data_directory = "/default/data/dir"
        mock_config.return_value = mock_config_instance

        result = LibraryService._get_default_library_directory()

        assert result == "/default/data/dir"
        mock_config.assert_called_once()
        mock_getenv.assert_called_once_with("BOOKCARD_DEFAULT_LIBRARY_DIR")


# ============================================================================
# Tests for EPUBFixerConfigService
# ============================================================================


@pytest.fixture
def epub_fixer_service(session: DummySession) -> EPUBFixerConfigService:
    """Create an EPUBFixerConfigService instance for testing.

    Parameters
    ----------
    session : DummySession
        Test session.

    Returns
    -------
    EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    return EPUBFixerConfigService(session)  # type: ignore[arg-type]


def test_epub_fixer_config_service_init(
    epub_fixer_service: EPUBFixerConfigService,
) -> None:
    """Test EPUBFixerConfigService initialization (covers line 612).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    assert epub_fixer_service._session is not None


def test_get_epub_fixer_config_existing(
    epub_fixer_service: EPUBFixerConfigService,
) -> None:
    """Test get_epub_fixer_config returns existing config (covers lines 624-625).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    session = epub_fixer_service._session
    existing_config = EPUBFixerConfig(id=1, enabled=True)
    session.add_exec_result([existing_config])  # type: ignore[possibly-missing-attribute]

    result = epub_fixer_service.get_epub_fixer_config()

    assert result == existing_config
    assert result.enabled is True


def test_get_epub_fixer_config_creates_default(
    epub_fixer_service: EPUBFixerConfigService,
) -> None:
    """Test get_epub_fixer_config creates default config when none exists (covers lines 624-632).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    session = epub_fixer_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # No existing config

    result = epub_fixer_service.get_epub_fixer_config()

    assert result is not None
    assert isinstance(result, EPUBFixerConfig)
    assert result in session.added  # type: ignore[possibly-missing-attribute]
    assert session.commit_count == 1  # type: ignore[possibly-missing-attribute]


@pytest.mark.parametrize(
    (
        "enabled",
        "backup_enabled",
        "backup_directory",
        "default_language",
        "skip_already_fixed",
        "skip_failed",
    ),
    [
        (True, None, None, None, None, None),
        (None, True, None, None, None, None),
        (None, None, "/backup/dir", None, None, None),
        (None, None, None, "fr", None, None),
        (None, None, None, None, True, None),
        (None, None, None, None, None, True),
        (True, True, "/backup", "en", True, True),
    ],
)
def test_update_epub_fixer_config(
    epub_fixer_service: EPUBFixerConfigService,
    enabled: bool | None,
    backup_enabled: bool | None,
    backup_directory: str | None,
    default_language: str | None,
    skip_already_fixed: bool | None,
    skip_failed: bool | None,
) -> None:
    """Test update_epub_fixer_config updates all fields (covers lines 666-684).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    enabled : bool | None
        Enabled flag to set.
    backup_enabled : bool | None
        Backup enabled flag to set.
    backup_directory : str | None
        Backup directory to set.
    default_language : str | None
        Default language to set.
    skip_already_fixed : bool | None
        Skip already fixed flag to set.
    skip_failed : bool | None
        Skip failed flag to set.
    """
    session = epub_fixer_service._session
    existing_config = EPUBFixerConfig(
        id=1,
        enabled=False,
        backup_enabled=False,
        backup_directory="/old/backup",
        default_language="en",
        skip_already_fixed=False,
        skip_failed=False,
    )
    session.add_exec_result([existing_config])  # type: ignore[possibly-missing-attribute]

    result = epub_fixer_service.update_epub_fixer_config(
        enabled=enabled,
        backup_enabled=backup_enabled,
        backup_directory=backup_directory,
        default_language=default_language,
        skip_already_fixed=skip_already_fixed,
        skip_failed=skip_failed,
    )

    if enabled is not None:
        assert result.enabled == enabled
    if backup_enabled is not None:
        assert result.backup_enabled == backup_enabled
    if backup_directory is not None:
        assert result.backup_directory == backup_directory
    if default_language is not None:
        assert result.default_language == default_language
    if skip_already_fixed is not None:
        assert result.skip_already_fixed == skip_already_fixed
    if skip_failed is not None:
        assert result.skip_failed == skip_failed

    assert session.commit_count == 1  # type: ignore[possibly-missing-attribute]


def test_is_epub_fixer_enabled(
    epub_fixer_service: EPUBFixerConfigService,
) -> None:
    """Test is_epub_fixer_enabled returns config value (covers lines 694-695).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    session = epub_fixer_service._session
    config = EPUBFixerConfig(id=1, enabled=True)
    session.add_exec_result([config])  # type: ignore[possibly-missing-attribute]
    session.add_exec_result([config])  # type: ignore[possibly-missing-attribute]  # Second call for is_epub_fixer_enabled

    result = epub_fixer_service.is_epub_fixer_enabled()

    assert result is True


def test_is_auto_fix_on_ingest_enabled_with_config(
    epub_fixer_service: EPUBFixerConfigService,
) -> None:
    """Test is_auto_fix_on_ingest_enabled returns config value when config exists (covers lines 705-709).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    session = epub_fixer_service._session
    # Create a library with auto-fix enabled
    from datetime import UTC, datetime

    from bookcard.models.config import Library

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/test/path",
        calibre_db_file="metadata.db",
        epub_fixer_auto_fix_on_ingest=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add_exec_result([library])  # type: ignore[possibly-missing-attribute]

    result = epub_fixer_service.is_auto_fix_on_ingest_enabled(library=library)

    assert result is True


def test_is_auto_fix_on_ingest_enabled_no_library(
    epub_fixer_service: EPUBFixerConfigService,
) -> None:
    """Test is_auto_fix_on_ingest_enabled returns False when library is None (covers lines 805-817).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    session = epub_fixer_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # No config

    result = epub_fixer_service.is_auto_fix_on_ingest_enabled()

    assert result is False


def test_is_daily_scan_enabled_with_config(
    epub_fixer_service: EPUBFixerConfigService,
) -> None:
    """Test is_daily_scan_enabled returns config value when config exists (covers lines 719-723).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    session = epub_fixer_service._session
    scheduled_config = ScheduledTasksConfig(id=1, epub_fixer_daily_scan=True)
    session.add_exec_result([scheduled_config])  # type: ignore[possibly-missing-attribute]

    result = epub_fixer_service.is_daily_scan_enabled()

    assert result is True


def test_is_daily_scan_enabled_no_config(
    epub_fixer_service: EPUBFixerConfigService,
) -> None:
    """Test is_daily_scan_enabled returns False when config is None (covers lines 719-723).

    Parameters
    ----------
    epub_fixer_service : EPUBFixerConfigService
        EPUB fixer config service instance.
    """
    session = epub_fixer_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # No config

    result = epub_fixer_service.is_daily_scan_enabled()

    assert result is False


# ============================================================================
# Tests for ScheduledTasksConfigService
# ============================================================================


@pytest.fixture
def scheduled_tasks_service(session: DummySession) -> ScheduledTasksConfigService:
    """Create a ScheduledTasksConfigService instance for testing.

    Parameters
    ----------
    session : DummySession
        Test session.

    Returns
    -------
    ScheduledTasksConfigService
        Scheduled tasks config service instance.
    """
    return ScheduledTasksConfigService(session)  # type: ignore[arg-type]


def test_scheduled_tasks_config_service_init(
    scheduled_tasks_service: ScheduledTasksConfigService,
) -> None:
    """Test ScheduledTasksConfigService initialization (covers line 743).

    Parameters
    ----------
    scheduled_tasks_service : ScheduledTasksConfigService
        Scheduled tasks config service instance.
    """
    assert scheduled_tasks_service._session is not None


def test_get_scheduled_tasks_config_existing(
    scheduled_tasks_service: ScheduledTasksConfigService,
) -> None:
    """Test get_scheduled_tasks_config returns existing config (covers lines 755-756).

    Parameters
    ----------
    scheduled_tasks_service : ScheduledTasksConfigService
        Scheduled tasks config service instance.
    """
    session = scheduled_tasks_service._session
    existing_config = ScheduledTasksConfig(id=1, start_time_hour=5)
    session.add_exec_result([existing_config])  # type: ignore[possibly-missing-attribute]

    result = scheduled_tasks_service.get_scheduled_tasks_config()

    assert result == existing_config
    assert result.start_time_hour == 5


def test_get_scheduled_tasks_config_creates_default(
    scheduled_tasks_service: ScheduledTasksConfigService,
) -> None:
    """Test get_scheduled_tasks_config creates default config when none exists (covers lines 755-763).

    Parameters
    ----------
    scheduled_tasks_service : ScheduledTasksConfigService
        Scheduled tasks config service instance.
    """
    session = scheduled_tasks_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # No existing config

    result = scheduled_tasks_service.get_scheduled_tasks_config()

    assert result is not None
    assert isinstance(result, ScheduledTasksConfig)
    assert result in session.added  # type: ignore[possibly-missing-attribute]
    assert session.commit_count == 1  # type: ignore[possibly-missing-attribute]


@pytest.mark.parametrize(
    (
        "start_time_hour",
        "duration_hours",
        "generate_book_covers",
        "generate_series_covers",
        "reconnect_database",
        "metadata_backup",
        "epub_fixer_daily_scan",
    ),
    [
        (5, None, None, None, None, None, None),
        (None, 8, None, None, None, None, None),
        (None, None, True, None, None, None, None),
        (None, None, None, True, None, None, None),
        (None, None, None, None, True, None, None),
        (None, None, None, None, None, True, None),
        (None, None, None, None, None, None, True),
        (6, 12, True, True, True, True, True),
    ],
)
def test_update_scheduled_tasks_config(
    scheduled_tasks_service: ScheduledTasksConfigService,
    start_time_hour: int | None,
    duration_hours: int | None,
    generate_book_covers: bool | None,
    generate_series_covers: bool | None,
    reconnect_database: bool | None,
    metadata_backup: bool | None,
    epub_fixer_daily_scan: bool | None,
) -> None:
    """Test update_scheduled_tasks_config updates all fields (covers lines 803-825).

    Parameters
    ----------
    scheduled_tasks_service : ScheduledTasksConfigService
        Scheduled tasks config service instance.
    start_time_hour : int | None
        Start time hour to set.
    duration_hours : int | None
        Duration hours to set.
    generate_book_covers : bool | None
        Generate book covers flag to set.
    generate_series_covers : bool | None
        Generate series covers flag to set.
    reconnect_database : bool | None
        Reconnect database flag to set.
    metadata_backup : bool | None
        Metadata backup flag to set.
    epub_fixer_daily_scan : bool | None
        EPUB fixer daily scan flag to set.
    """
    session = scheduled_tasks_service._session
    existing_config = ScheduledTasksConfig(
        id=1,
        start_time_hour=4,
        duration_hours=10,
        generate_book_covers=False,
        generate_series_covers=False,
        reconnect_database=False,
        metadata_backup=False,
        epub_fixer_daily_scan=False,
    )
    session.add_exec_result([existing_config])  # type: ignore[possibly-missing-attribute]

    result = scheduled_tasks_service.update_scheduled_tasks_config(
        start_time_hour=start_time_hour,
        duration_hours=duration_hours,
        generate_book_covers=generate_book_covers,
        generate_series_covers=generate_series_covers,
        reconnect_database=reconnect_database,
        metadata_backup=metadata_backup,
        epub_fixer_daily_scan=epub_fixer_daily_scan,
    )

    if start_time_hour is not None:
        assert result.start_time_hour == start_time_hour
    if duration_hours is not None:
        assert result.duration_hours == duration_hours
    if generate_book_covers is not None:
        assert result.generate_book_covers == generate_book_covers
    if generate_series_covers is not None:
        assert result.generate_series_covers == generate_series_covers
    if reconnect_database is not None:
        assert result.reconnect_database == reconnect_database
    if metadata_backup is not None:
        assert result.metadata_backup == metadata_backup
    if epub_fixer_daily_scan is not None:
        assert result.epub_fixer_daily_scan == epub_fixer_daily_scan

    assert session.commit_count == 1  # type: ignore[possibly-missing-attribute]


# ============================================================================
# Tests for BasicConfigService
# ============================================================================


@pytest.fixture
def basic_config_service(session: DummySession) -> BasicConfigService:
    """Create a BasicConfigService instance for testing.

    Parameters
    ----------
    session : DummySession
        Test session.

    Returns
    -------
    BasicConfigService
        Basic config service instance.
    """
    return BasicConfigService(session)  # type: ignore[arg-type]


def test_basic_config_service_init(
    basic_config_service: BasicConfigService,
) -> None:
    """Test BasicConfigService initialization (covers line 65).

    Parameters
    ----------
    basic_config_service : BasicConfigService
        Basic config service instance.
    """
    assert basic_config_service._session is not None


def test_get_basic_config_creates_default(
    basic_config_service: BasicConfigService,
) -> None:
    """Test get_basic_config creates default config when none exists (covers lines 69-76).

    Parameters
    ----------
    basic_config_service : BasicConfigService
        Basic config service instance.
    """
    session = basic_config_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # No existing config

    result = basic_config_service.get_basic_config()

    assert result is not None
    from bookcard.models.config import BasicConfig

    assert isinstance(result, BasicConfig)
    assert result in session.added  # type: ignore[possibly-missing-attribute]
    assert session.commit_count == 1  # type: ignore[possibly-missing-attribute]


def test_get_basic_config_existing(
    basic_config_service: BasicConfigService,
) -> None:
    """Test get_basic_config returns existing config (covers line 70).

    Parameters
    ----------
    basic_config_service : BasicConfigService
        Basic config service instance.
    """
    session = basic_config_service._session
    from bookcard.models.config import BasicConfig

    existing_config = BasicConfig(id=1, allow_anonymous_browsing=True)
    session.add_exec_result([existing_config])  # type: ignore[possibly-missing-attribute]

    result = basic_config_service.get_basic_config()

    assert result == existing_config
    assert result.allow_anonymous_browsing is True


@pytest.mark.parametrize(
    (
        "allow_anonymous_browsing",
        "allow_public_registration",
        "require_email_for_registration",
        "max_upload_size_mb",
    ),
    [
        (True, None, None, None),
        (None, True, None, None),
        (None, None, True, None),
        (None, None, None, 100),
        (True, True, True, 200),
    ],
)
def test_update_basic_config(
    basic_config_service: BasicConfigService,
    allow_anonymous_browsing: bool | None,
    allow_public_registration: bool | None,
    require_email_for_registration: bool | None,
    max_upload_size_mb: int | None,
) -> None:
    """Test update_basic_config updates all fields (covers lines 104-116).

    Parameters
    ----------
    basic_config_service : BasicConfigService
        Basic config service instance.
    allow_anonymous_browsing : bool | None
        Allow anonymous browsing flag to set.
    allow_public_registration : bool | None
        Allow public registration flag to set.
    require_email_for_registration : bool | None
        Require email for registration flag to set.
    max_upload_size_mb : int | None
        Max upload size in MB to set.
    """
    session = basic_config_service._session
    from bookcard.models.config import BasicConfig

    existing_config = BasicConfig(
        id=1,
        allow_anonymous_browsing=False,
        allow_public_registration=False,
        require_email_for_registration=False,
        max_upload_size_mb=50,
    )
    session.add_exec_result([existing_config])  # type: ignore[possibly-missing-attribute]

    result = basic_config_service.update_basic_config(
        allow_anonymous_browsing=allow_anonymous_browsing,
        allow_public_registration=allow_public_registration,
        require_email_for_registration=require_email_for_registration,
        max_upload_size_mb=max_upload_size_mb,
    )

    if allow_anonymous_browsing is not None:
        assert result.allow_anonymous_browsing == allow_anonymous_browsing
    if allow_public_registration is not None:
        assert result.allow_public_registration == allow_public_registration
    if require_email_for_registration is not None:
        assert result.require_email_for_registration == require_email_for_registration
    if max_upload_size_mb is not None:
        assert result.max_upload_size_mb == max_upload_size_mb

    assert session.commit_count == 1  # type: ignore[possibly-missing-attribute]


# ============================================================================
# Tests for LibraryService._update_library_fields with auto_metadata_enforcement
# ============================================================================


def test_update_library_fields_auto_metadata_enforcement(
    library_service: LibraryService,
) -> None:
    """Test _update_library_fields updates auto_metadata_enforcement (covers lines 622, 624).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    """
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        auto_metadata_enforcement=False,
    )

    library_service._update_library_fields(library, auto_metadata_enforcement=True)

    assert library.auto_metadata_enforcement is True


# ============================================================================
# Tests for LibraryService._update_auto_convert_fields
# ============================================================================


@pytest.mark.parametrize(
    (
        "auto_convert_on_ingest",
        "auto_convert_target_format",
        "auto_convert_ignored_formats",
        "auto_convert_backup_originals",
        "epub_fixer_auto_fix_on_ingest",
        "duplicate_handling",
    ),
    [
        (True, None, None, None, None, None),
        (None, "EPUB", None, None, None, None),
        (None, None, '["MOBI", "AZW3"]', None, None, None),
        (None, None, None, True, None, None),
        (None, None, None, None, True, None),
        (None, None, None, None, None, "IGNORE"),
        (True, "EPUB", '["MOBI"]', True, True, "OVERWRITE"),
    ],
)
def test_update_auto_convert_fields(
    library_service: LibraryService,
    auto_convert_on_ingest: bool | None,
    auto_convert_target_format: str | None,
    auto_convert_ignored_formats: str | None,
    auto_convert_backup_originals: bool | None,
    epub_fixer_auto_fix_on_ingest: bool | None,
    duplicate_handling: str | None,
) -> None:
    """Test _update_auto_convert_fields updates all fields (covers lines 657, 659, 661, 663, 665, 667).

    Parameters
    ----------
    library_service : LibraryService
        Library service instance.
    auto_convert_on_ingest : bool | None
        Auto convert on ingest flag to set.
    auto_convert_target_format : str | None
        Target format to set.
    auto_convert_ignored_formats : str | None
        Ignored formats to set.
    auto_convert_backup_originals : bool | None
        Backup originals flag to set.
    epub_fixer_auto_fix_on_ingest : bool | None
        EPUB fixer auto fix flag to set.
    duplicate_handling : str | None
        Duplicate handling strategy to set.
    """
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        auto_convert_on_ingest=False,
        auto_convert_target_format=None,
        auto_convert_ignored_formats=None,
        auto_convert_backup_originals=False,
        epub_fixer_auto_fix_on_ingest=False,
        duplicate_handling=None,
    )

    library_service._update_auto_convert_fields(
        library,
        auto_convert_on_ingest=auto_convert_on_ingest,
        auto_convert_target_format=auto_convert_target_format,
        auto_convert_ignored_formats=auto_convert_ignored_formats,
        auto_convert_backup_originals=auto_convert_backup_originals,
        epub_fixer_auto_fix_on_ingest=epub_fixer_auto_fix_on_ingest,
        duplicate_handling=duplicate_handling,
    )

    if auto_convert_on_ingest is not None:
        assert library.auto_convert_on_ingest == auto_convert_on_ingest
    if auto_convert_target_format is not None:
        assert library.auto_convert_target_format == auto_convert_target_format
    if auto_convert_ignored_formats is not None:
        assert library.auto_convert_ignored_formats == auto_convert_ignored_formats
    if auto_convert_backup_originals is not None:
        assert library.auto_convert_backup_originals == auto_convert_backup_originals
    if epub_fixer_auto_fix_on_ingest is not None:
        assert library.epub_fixer_auto_fix_on_ingest == epub_fixer_auto_fix_on_ingest
    if duplicate_handling is not None:
        assert library.duplicate_handling == duplicate_handling


# ============================================================================
# Tests for FileHandlingConfigService
# ============================================================================


@pytest.fixture
def file_handling_service(session: DummySession) -> FileHandlingConfigService:
    """Create a FileHandlingConfigService instance for testing.

    Parameters
    ----------
    session : DummySession
        Test session.

    Returns
    -------
    FileHandlingConfigService
        File handling config service instance.
    """
    return FileHandlingConfigService(session)  # type: ignore[arg-type]


def test_file_handling_config_service_init(
    file_handling_service: FileHandlingConfigService,
) -> None:
    """Test FileHandlingConfigService initialization (covers line 1063).

    Parameters
    ----------
    file_handling_service : FileHandlingConfigService
        File handling config service instance.
    """
    assert file_handling_service._session is not None


def test_get_file_handling_config_creates_default(
    file_handling_service: FileHandlingConfigService,
) -> None:
    """Test get_file_handling_config creates default config when none exists (covers lines 1075-1083).

    Parameters
    ----------
    file_handling_service : FileHandlingConfigService
        File handling config service instance.
    """
    session = file_handling_service._session
    session.add_exec_result([])  # type: ignore[possibly-missing-attribute]  # No existing config

    result = file_handling_service.get_file_handling_config()

    assert result is not None
    assert isinstance(result, FileHandlingConfig)
    assert result in session.added  # type: ignore[possibly-missing-attribute]
    assert session.commit_count == 1  # type: ignore[possibly-missing-attribute]


def test_get_allowed_upload_formats_empty(
    file_handling_service: FileHandlingConfigService,
) -> None:
    """Test get_allowed_upload_formats returns empty list when config is empty (covers line 1095).

    Parameters
    ----------
    file_handling_service : FileHandlingConfigService
        File handling config service instance.
    """
    session = file_handling_service._session
    config = FileHandlingConfig(id=1, allowed_upload_formats=None)
    session.add_exec_result([config])  # type: ignore[possibly-missing-attribute]

    result = file_handling_service.get_allowed_upload_formats()

    assert result == []


def test_get_allowed_upload_formats_with_formats(
    file_handling_service: FileHandlingConfigService,
) -> None:
    """Test get_allowed_upload_formats parses formats correctly (covers lines 1093-1097).

    Parameters
    ----------
    file_handling_service : FileHandlingConfigService
        File handling config service instance.
    """
    session = file_handling_service._session
    config = FileHandlingConfig(id=1, allowed_upload_formats="EPUB, MOBI, PDF, AZW3")
    session.add_exec_result([config])  # type: ignore[possibly-missing-attribute]

    result = file_handling_service.get_allowed_upload_formats()

    assert result == ["epub", "mobi", "pdf", "azw3"]


def test_is_format_allowed(
    file_handling_service: FileHandlingConfigService,
) -> None:
    """Test is_format_allowed checks format correctly (covers lines 1117-1119).

    Parameters
    ----------
    file_handling_service : FileHandlingConfigService
        File handling config service instance.
    """
    session = file_handling_service._session
    config = FileHandlingConfig(id=1, allowed_upload_formats="EPUB, MOBI, PDF")
    # Need to return config for both get_file_handling_config() calls
    session.add_exec_result([config])  # type: ignore[possibly-missing-attribute]
    session.add_exec_result([config])  # type: ignore[possibly-missing-attribute]

    assert file_handling_service.is_format_allowed("epub") is True
    assert file_handling_service.is_format_allowed(".EPUB") is True
    assert file_handling_service.is_format_allowed("mobi") is True
    # Use a format that's definitely not in the allowed list
    assert file_handling_service.is_format_allowed("xyz") is False
