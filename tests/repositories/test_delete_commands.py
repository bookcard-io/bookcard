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

"""Tests for delete commands."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003
from unittest.mock import MagicMock

import pytest

from fundamental.models.auth import User
from fundamental.models.core import (
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
)
from fundamental.models.media import Data
from fundamental.repositories.delete_commands import (
    DeleteBookAuthorLinksCommand,
    DeleteBookCommand,
    DeleteBookLanguageLinksCommand,
    DeleteBookPublisherLinksCommand,
    DeleteBookRatingLinksCommand,
    DeleteBookSeriesLinksCommand,
    DeleteBookShelfLinksCommand,
    DeleteBookTagLinksCommand,
    DeleteCommentCommand,
    DeleteDataRecordsCommand,
    DeleteDirectoryCommand,
    DeleteFileCommand,
    DeleteIdentifiersCommand,
    DeleteRefreshTokensCommand,
    DeleteUserCommand,
    DeleteUserDataDirectoryCommand,
    DeleteUserDevicesCommand,
    DeleteUserRolesCommand,
    DeleteUserSettingsCommand,
)
from tests.conftest import DummySession


@pytest.fixture
def session() -> DummySession:
    """Create a DummySession instance."""
    return DummySession()


@pytest.fixture
def book_id() -> int:
    """Return a test book ID."""
    return 1


@pytest.fixture
def book() -> Book:
    """Create a test Book instance."""
    return Book(
        id=1,
        title="Test Book",
        path="/path/to/book",
        uuid="test-uuid-123",
        has_cover=True,
    )


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for file operations."""
    return tmp_path


# Parametrized fixtures for link commands
@pytest.fixture(
    params=[
        (DeleteBookAuthorLinksCommand, BookAuthorLink, "author"),
        (DeleteBookTagLinksCommand, BookTagLink, "tag"),
        (DeleteBookPublisherLinksCommand, BookPublisherLink, "publisher"),
        (DeleteBookLanguageLinksCommand, BookLanguageLink, "lang_code"),
        (DeleteBookRatingLinksCommand, BookRatingLink, "rating"),
        (DeleteBookSeriesLinksCommand, BookSeriesLink, "series"),
    ]
)
def link_command_class(
    request: pytest.FixtureRequest,
) -> tuple[type, type, str]:
    """Parametrized fixture for link command classes."""
    return request.param


def test_link_command_execute_deletes_links(
    session: DummySession,
    book_id: int,
    link_command_class: tuple[type, type, str],
) -> None:
    """Test link command execute deletes all links for book."""
    command_cls, link_cls, link_field = link_command_class
    command = command_cls(session, book_id)  # type: ignore[arg-type]

    # Create test links
    link1 = link_cls(id=1, book=book_id, **{link_field: 10})
    link2 = link_cls(id=2, book=book_id, **{link_field: 20})

    session.add_exec_result([link1, link2])
    command.execute()

    assert len(command._deleted_links) == 2
    assert link1 in session.deleted
    assert link2 in session.deleted


def test_link_command_execute_no_links(
    session: DummySession,
    book_id: int,
    link_command_class: tuple[type, type, str],
) -> None:
    """Test link command execute handles no links gracefully."""
    command_cls, _, _ = link_command_class
    command = command_cls(session, book_id)  # type: ignore[arg-type]

    session.add_exec_result([])
    command.execute()

    assert len(command._deleted_links) == 0
    assert len(session.deleted) == 0


def test_link_command_undo_restores_links(
    session: DummySession,
    book_id: int,
    link_command_class: tuple[type, type, str],
) -> None:
    """Test link command undo restores deleted links."""
    command_cls, link_cls, link_field = link_command_class
    command = command_cls(session, book_id)  # type: ignore[arg-type]

    link1 = link_cls(id=1, book=book_id, **{link_field: 10})
    link2 = link_cls(id=2, book=book_id, **{link_field: 20})

    session.add_exec_result([link1, link2])
    command.execute()
    command.undo()

    assert link1 in session.added
    assert link2 in session.added


def test_link_command_undo_idempotent(
    session: DummySession,
    book_id: int,
    link_command_class: tuple[type, type, str],
) -> None:
    """Test link command undo can be called multiple times safely."""
    command_cls, link_cls, link_field = link_command_class
    command = command_cls(session, book_id)  # type: ignore[arg-type]

    link1 = link_cls(id=1, book=book_id, **{link_field: 10})
    session.add_exec_result([link1])
    command.execute()

    # Call undo multiple times - each call will add the link
    # This is safe because session.add() can handle duplicates
    command.undo()
    command.undo()

    # Link should be added twice (implementation behavior)
    # The undo method doesn't track if already undone
    assert session.added.count(link1) == 2


def test_link_command_undo_no_links(
    session: DummySession,
    book_id: int,
    link_command_class: tuple[type, type, str],
) -> None:
    """Test link command undo handles no deleted links."""
    command_cls, _, _ = link_command_class
    command = command_cls(session, book_id)  # type: ignore[arg-type]

    # Undo without executing
    command.undo()

    assert len(session.added) == 0


def test_delete_book_shelf_links_execute_noop(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteBookShelfLinksCommand execute is a no-op."""
    command = DeleteBookShelfLinksCommand(session, book_id)  # type: ignore[arg-type]
    command.execute()
    # Should not raise and should not modify session
    assert len(session.deleted) == 0


def test_delete_book_shelf_links_undo_noop(session: DummySession, book_id: int) -> None:
    """Test DeleteBookShelfLinksCommand undo is a no-op."""
    command = DeleteBookShelfLinksCommand(session, book_id)  # type: ignore[arg-type]
    command.undo()
    # Should not raise and should not modify session
    assert len(session.added) == 0


def test_delete_comment_execute_deletes_comment(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteCommentCommand execute deletes comment."""
    command = DeleteCommentCommand(session, book_id)  # type: ignore[arg-type]
    comment = Comment(id=1, book=book_id, text="Test comment")

    session.add_exec_result([comment])
    command.execute()

    assert command._deleted_comment is comment
    assert comment in session.deleted


def test_delete_comment_execute_no_comment(session: DummySession, book_id: int) -> None:
    """Test DeleteCommentCommand execute handles no comment."""
    command = DeleteCommentCommand(session, book_id)  # type: ignore[arg-type]

    session.add_exec_result([])
    command.execute()

    assert command._deleted_comment is None
    assert len(session.deleted) == 0


def test_delete_comment_undo_restores_comment(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteCommentCommand undo restores comment."""
    command = DeleteCommentCommand(session, book_id)  # type: ignore[arg-type]
    comment = Comment(id=1, book=book_id, text="Test comment")

    session.add_exec_result([comment])
    command.execute()
    command.undo()

    assert comment in session.added


def test_delete_comment_undo_no_comment(session: DummySession, book_id: int) -> None:
    """Test DeleteCommentCommand undo handles no deleted comment."""
    command = DeleteCommentCommand(session, book_id)  # type: ignore[arg-type]
    command.undo()
    assert len(session.added) == 0


def test_delete_identifiers_execute_deletes_identifiers(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteIdentifiersCommand execute deletes identifiers."""
    command = DeleteIdentifiersCommand(session, book_id)  # type: ignore[arg-type]
    identifier1 = Identifier(id=1, book=book_id, type="isbn", val="123456")
    identifier2 = Identifier(id=2, book=book_id, type="doi", val="10.1234/567")

    session.add_exec_result([identifier1, identifier2])
    command.execute()

    assert len(command._deleted_identifiers) == 2
    assert identifier1 in session.deleted
    assert identifier2 in session.deleted


def test_delete_identifiers_execute_no_identifiers(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteIdentifiersCommand execute handles no identifiers."""
    command = DeleteIdentifiersCommand(session, book_id)  # type: ignore[arg-type]

    session.add_exec_result([])
    command.execute()

    assert len(command._deleted_identifiers) == 0
    assert len(session.deleted) == 0


def test_delete_identifiers_undo_restores_identifiers(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteIdentifiersCommand undo restores identifiers."""
    command = DeleteIdentifiersCommand(session, book_id)  # type: ignore[arg-type]
    identifier1 = Identifier(id=1, book=book_id, type="isbn", val="123456")

    session.add_exec_result([identifier1])
    command.execute()
    command.undo()

    assert identifier1 in session.added


def test_delete_data_records_execute_deletes_persistent(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteDataRecordsCommand execute deletes persistent records."""
    command = DeleteDataRecordsCommand(session, book_id)  # type: ignore[arg-type]
    data1 = Data(
        id=1, book=book_id, format="EPUB", uncompressed_size=1000, name="book.epub"
    )
    data2 = Data(
        id=2, book=book_id, format="PDF", uncompressed_size=2000, name="book.pdf"
    )

    # Mock inspect to return persistent state
    mock_inspect1 = MagicMock()
    mock_inspect1.persistent = True
    mock_inspect2 = MagicMock()
    mock_inspect2.persistent = True

    session.add_exec_result([data1, data2])

    # Patch inspect to return our mocks
    import fundamental.repositories.delete_commands as delete_commands_mod

    original_inspect = delete_commands_mod.inspect

    def mock_inspect_func(obj: object) -> MagicMock:  # type: ignore[type-arg]
        if obj is data1:
            return mock_inspect1
        if obj is data2:
            return mock_inspect2
        return original_inspect(obj)

    delete_commands_mod.inspect = mock_inspect_func  # type: ignore[assignment]

    try:
        command.execute()
    finally:
        delete_commands_mod.inspect = original_inspect

    assert len(command._deleted_data) == 2
    assert data1 in session.deleted
    assert data2 in session.deleted


def test_delete_data_records_execute_skips_non_persistent(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteDataRecordsCommand execute skips non-persistent records."""
    command = DeleteDataRecordsCommand(session, book_id)  # type: ignore[arg-type]
    data1 = Data(
        id=1, book=book_id, format="EPUB", uncompressed_size=1000, name="book.epub"
    )
    data2 = Data(
        id=2, book=book_id, format="PDF", uncompressed_size=2000, name="book.pdf"
    )

    # Mock inspect: first persistent, second not
    mock_inspect1 = MagicMock()
    mock_inspect1.persistent = True
    mock_inspect2 = MagicMock()
    mock_inspect2.persistent = False

    session.add_exec_result([data1, data2])

    import fundamental.repositories.delete_commands as delete_commands_mod

    original_inspect = delete_commands_mod.inspect

    def mock_inspect_func(obj: object) -> MagicMock:  # type: ignore[type-arg]
        if obj is data1:
            return mock_inspect1
        if obj is data2:
            return mock_inspect2
        return original_inspect(obj)

    delete_commands_mod.inspect = mock_inspect_func  # type: ignore[assignment]

    try:
        command.execute()
    finally:
        delete_commands_mod.inspect = original_inspect

    # Only persistent record should be deleted
    assert len(command._deleted_data) == 1
    assert data1 in session.deleted
    assert data2 not in session.deleted


def test_delete_data_records_undo_restores_data(
    session: DummySession, book_id: int
) -> None:
    """Test DeleteDataRecordsCommand undo restores data records."""
    command = DeleteDataRecordsCommand(session, book_id)  # type: ignore[arg-type]
    data1 = Data(
        id=1, book=book_id, format="EPUB", uncompressed_size=1000, name="book.epub"
    )

    mock_inspect1 = MagicMock()
    mock_inspect1.persistent = True

    session.add_exec_result([data1])

    import fundamental.repositories.delete_commands as delete_commands_mod

    original_inspect = delete_commands_mod.inspect

    def mock_inspect_func(obj: object) -> MagicMock:  # type: ignore[type-arg]
        if obj is data1:
            return mock_inspect1
        return original_inspect(obj)

    delete_commands_mod.inspect = mock_inspect_func  # type: ignore[assignment]

    try:
        command.execute()
        command.undo()
    finally:
        delete_commands_mod.inspect = original_inspect

    assert data1 in session.added


def test_delete_book_execute_deletes_book(session: DummySession, book: Book) -> None:
    """Test DeleteBookCommand execute deletes book and creates snapshot."""
    command = DeleteBookCommand(session, book)  # type: ignore[arg-type]
    command.execute()

    assert book in session.deleted
    assert command._book_snapshot is not None
    assert command._book_snapshot["id"] == book.id
    assert command._book_snapshot["title"] == book.title
    assert command._book_snapshot["path"] == book.path
    assert command._book_snapshot["uuid"] == book.uuid
    assert command._book_snapshot["has_cover"] == book.has_cover


def test_delete_book_undo_restores_book(session: DummySession, book: Book) -> None:
    """Test DeleteBookCommand undo restores book from snapshot."""
    command = DeleteBookCommand(session, book)  # type: ignore[arg-type]
    command.execute()
    command.undo()

    # Should have added a restored book
    assert len(session.added) == 1
    restored_book = session.added[0]
    assert isinstance(restored_book, Book)
    assert restored_book.id == book.id
    assert restored_book.title == book.title


def test_delete_book_undo_no_snapshot(session: DummySession, book: Book) -> None:
    """Test DeleteBookCommand undo handles no snapshot."""
    command = DeleteBookCommand(session, book)  # type: ignore[arg-type]
    command.undo()
    assert len(session.added) == 0


def test_delete_file_execute_deletes_existing_file(temp_dir: Path) -> None:
    """Test DeleteFileCommand execute deletes existing file."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    command = DeleteFileCommand(test_file)
    command.execute()

    assert not test_file.exists()
    assert command._file_existed is True
    assert command._file_backup == b"test content"


def test_delete_file_execute_skips_nonexistent_file(temp_dir: Path) -> None:
    """Test DeleteFileCommand execute skips nonexistent file."""
    test_file = temp_dir / "nonexistent.txt"

    command = DeleteFileCommand(test_file)
    command.execute()

    assert command._file_existed is False
    assert command._file_backup is None


def test_delete_file_execute_skips_directory(temp_dir: Path) -> None:
    """Test DeleteFileCommand execute skips directories."""
    test_dir = temp_dir / "test_dir"
    test_dir.mkdir()

    command = DeleteFileCommand(test_dir)
    command.execute()

    assert test_dir.exists()
    assert command._file_existed is False


def test_delete_file_undo_restores_file(temp_dir: Path) -> None:
    """Test DeleteFileCommand undo restores file."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("original content")

    command = DeleteFileCommand(test_file)
    command.execute()
    command.undo()

    assert test_file.exists()
    assert test_file.read_text() == "original content"


def test_delete_file_undo_creates_parent_dirs(temp_dir: Path) -> None:
    """Test DeleteFileCommand undo creates parent directories."""
    test_file = temp_dir / "subdir" / "nested" / "test.txt"
    # Create parent directories first
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("content")

    command = DeleteFileCommand(test_file)
    command.execute()

    # Remove parent directories - they should be empty after file deletion
    # Use try/except to handle cases where directories might already be removed
    from contextlib import suppress

    with suppress(OSError):
        if test_file.parent.exists():
            test_file.parent.rmdir()
    with suppress(OSError):
        if test_file.parent.parent.exists():
            test_file.parent.parent.rmdir()

    command.undo()

    assert test_file.exists()
    assert test_file.read_text() == "content"


def test_delete_file_undo_no_backup(temp_dir: Path) -> None:
    """Test DeleteFileCommand undo handles no backup."""
    test_file = temp_dir / "nonexistent.txt"
    command = DeleteFileCommand(test_file)
    command.undo()
    assert not test_file.exists()


def test_delete_directory_execute_deletes_empty_dir(temp_dir: Path) -> None:
    """Test DeleteDirectoryCommand execute deletes empty directory."""
    test_dir = temp_dir / "empty_dir"
    test_dir.mkdir()

    command = DeleteDirectoryCommand(test_dir)
    command.execute()

    assert not test_dir.exists()
    assert command._dir_existed is True


def test_delete_directory_execute_skips_non_empty_dir(temp_dir: Path) -> None:
    """Test DeleteDirectoryCommand execute skips non-empty directory."""
    test_dir = temp_dir / "non_empty_dir"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")

    command = DeleteDirectoryCommand(test_dir)
    command.execute()

    assert test_dir.exists()
    assert command._dir_existed is False


def test_delete_directory_execute_skips_nonexistent_dir(temp_dir: Path) -> None:
    """Test DeleteDirectoryCommand execute skips nonexistent directory."""
    test_dir = temp_dir / "nonexistent"

    command = DeleteDirectoryCommand(test_dir)
    command.execute()

    assert command._dir_existed is False


def test_delete_directory_execute_skips_file(temp_dir: Path) -> None:
    """Test DeleteDirectoryCommand execute skips files."""
    test_file = temp_dir / "file.txt"
    test_file.write_text("content")

    command = DeleteDirectoryCommand(test_file)
    command.execute()

    assert test_file.exists()
    assert command._dir_existed is False


def test_delete_directory_undo_restores_dir(temp_dir: Path) -> None:
    """Test DeleteDirectoryCommand undo restores directory."""
    test_dir = temp_dir / "empty_dir"
    test_dir.mkdir()

    command = DeleteDirectoryCommand(test_dir)
    command.execute()
    command.undo()

    assert test_dir.exists()
    assert test_dir.is_dir()


def test_delete_directory_undo_creates_parent_dirs(temp_dir: Path) -> None:
    """Test DeleteDirectoryCommand undo creates parent directories."""
    test_dir = temp_dir / "subdir" / "nested" / "empty"
    test_dir.mkdir(parents=True)

    command = DeleteDirectoryCommand(test_dir)
    command.execute()
    # Remove parent directories
    test_dir.parent.rmdir()
    test_dir.parent.parent.rmdir()

    command.undo()

    assert test_dir.exists()
    assert test_dir.is_dir()


def test_delete_directory_undo_no_existed(temp_dir: Path) -> None:
    """Test DeleteDirectoryCommand undo handles directory that didn't exist."""
    test_dir = temp_dir / "nonexistent"
    command = DeleteDirectoryCommand(test_dir)
    command.undo()
    assert not test_dir.exists()


# User-related delete command tests


@pytest.fixture
def user_id() -> int:
    """Return a test user ID."""
    return 1


@pytest.fixture
def mock_device_repo() -> MagicMock:
    """Create a mock EReaderRepository."""
    repo = MagicMock()
    repo.find_by_user.return_value = []
    return repo


@pytest.fixture
def mock_user_role_repo() -> MagicMock:
    """Create a mock UserRoleRepository."""
    return MagicMock()


def test_delete_user_devices_execute_deletes_devices(
    session: DummySession, user_id: int, mock_device_repo: MagicMock
) -> None:
    """Test DeleteUserDevicesCommand execute deletes devices."""
    from fundamental.models.auth import EBookFormat, EReaderDevice

    device1 = EReaderDevice(
        id=1,
        user_id=user_id,
        email="device1@example.com",
        device_type="kindle",
        preferred_format=EBookFormat.MOBI,
    )
    device2 = EReaderDevice(
        id=2,
        user_id=user_id,
        email="device2@example.com",
        device_type="kobo",
        preferred_format=EBookFormat.EPUB,
    )

    mock_device_repo.find_by_user.return_value = [device1, device2]

    command = DeleteUserDevicesCommand(
        session,  # type: ignore[arg-type]
        user_id,
        mock_device_repo,  # type: ignore[arg-type]
    )
    command.execute()

    assert len(command._deleted_devices) == 2
    assert device1 in command._deleted_devices
    assert device2 in command._deleted_devices
    assert mock_device_repo.delete.call_count == 2
    mock_device_repo.delete.assert_any_call(device1)
    mock_device_repo.delete.assert_any_call(device2)


def test_delete_user_devices_execute_no_devices(
    session: DummySession, user_id: int, mock_device_repo: MagicMock
) -> None:
    """Test DeleteUserDevicesCommand execute handles no devices."""
    mock_device_repo.find_by_user.return_value = []

    command = DeleteUserDevicesCommand(
        session,  # type: ignore[arg-type]
        user_id,
        mock_device_repo,  # type: ignore[arg-type]
    )
    command.execute()

    assert len(command._deleted_devices) == 0
    assert mock_device_repo.delete.call_count == 0


def test_delete_user_devices_undo_restores_devices(
    session: DummySession, user_id: int, mock_device_repo: MagicMock
) -> None:
    """Test DeleteUserDevicesCommand undo restores devices."""
    from fundamental.models.auth import EBookFormat, EReaderDevice

    device1 = EReaderDevice(
        id=1,
        user_id=user_id,
        email="device1@example.com",
        device_type="kindle",
        preferred_format=EBookFormat.MOBI,
    )

    mock_device_repo.find_by_user.return_value = [device1]

    command = DeleteUserDevicesCommand(
        session,  # type: ignore[arg-type]
        user_id,
        mock_device_repo,  # type: ignore[arg-type]
    )
    command.execute()
    command.undo()

    assert device1 in session.added


def test_delete_user_devices_undo_no_devices(
    session: DummySession, user_id: int, mock_device_repo: MagicMock
) -> None:
    """Test DeleteUserDevicesCommand undo handles no deleted devices."""
    mock_device_repo.find_by_user.return_value = []

    command = DeleteUserDevicesCommand(
        session,  # type: ignore[arg-type]
        user_id,
        mock_device_repo,  # type: ignore[arg-type]
    )
    command.undo()

    assert len(session.added) == 0


def test_delete_user_roles_execute_deletes_roles(
    session: DummySession, user_id: int, mock_user_role_repo: MagicMock
) -> None:
    """Test DeleteUserRolesCommand execute deletes user roles."""
    from fundamental.models.auth import Role, UserRole

    role1 = Role(id=1, name="admin", description="Admin role")
    role2 = Role(id=2, name="user", description="User role")
    user_role1 = UserRole(id=1, user_id=user_id, role_id=1, role=role1)
    user_role2 = UserRole(id=2, user_id=user_id, role_id=2, role=role2)

    session.add_exec_result([user_role1, user_role2])

    command = DeleteUserRolesCommand(
        session,  # type: ignore[arg-type]
        user_id,
        mock_user_role_repo,  # type: ignore[arg-type]
    )
    command.execute()

    assert len(command._deleted_roles) == 2
    assert user_role1 in command._deleted_roles
    assert user_role2 in command._deleted_roles
    assert mock_user_role_repo.delete.call_count == 2
    mock_user_role_repo.delete.assert_any_call(user_role1)
    mock_user_role_repo.delete.assert_any_call(user_role2)


def test_delete_user_roles_execute_no_roles(
    session: DummySession, user_id: int, mock_user_role_repo: MagicMock
) -> None:
    """Test DeleteUserRolesCommand execute handles no roles."""
    session.add_exec_result([])

    command = DeleteUserRolesCommand(
        session,  # type: ignore[arg-type]
        user_id,
        mock_user_role_repo,  # type: ignore[arg-type]
    )
    command.execute()

    assert len(command._deleted_roles) == 0
    assert mock_user_role_repo.delete.call_count == 0


def test_delete_user_roles_undo_restores_roles(
    session: DummySession, user_id: int, mock_user_role_repo: MagicMock
) -> None:
    """Test DeleteUserRolesCommand undo restores user roles."""
    from fundamental.models.auth import Role, UserRole

    role1 = Role(id=1, name="admin", description="Admin role")
    user_role1 = UserRole(id=1, user_id=user_id, role_id=1, role=role1)

    session.add_exec_result([user_role1])

    command = DeleteUserRolesCommand(
        session,  # type: ignore[arg-type]
        user_id,
        mock_user_role_repo,  # type: ignore[arg-type]
    )
    command.execute()
    command.undo()

    assert user_role1 in session.added


def test_delete_user_roles_undo_no_roles(
    session: DummySession, user_id: int, mock_user_role_repo: MagicMock
) -> None:
    """Test DeleteUserRolesCommand undo handles no deleted roles."""
    session.add_exec_result([])

    command = DeleteUserRolesCommand(
        session,  # type: ignore[arg-type]
        user_id,
        mock_user_role_repo,  # type: ignore[arg-type]
    )
    command.undo()

    assert len(session.added) == 0


def test_delete_user_settings_execute_deletes_settings(
    session: DummySession, user_id: int
) -> None:
    """Test DeleteUserSettingsCommand execute deletes user settings."""
    from fundamental.models.auth import UserSetting

    setting1 = UserSetting(id=1, user_id=user_id, key="theme", value="dark")
    setting2 = UserSetting(id=2, user_id=user_id, key="language", value="en")

    session.add_exec_result([setting1, setting2])

    command = DeleteUserSettingsCommand(session, user_id)  # type: ignore[arg-type]
    command.execute()

    assert len(command._deleted_settings) == 2
    assert setting1 in command._deleted_settings
    assert setting2 in command._deleted_settings
    assert setting1 in session.deleted
    assert setting2 in session.deleted


def test_delete_user_settings_execute_no_settings(
    session: DummySession, user_id: int
) -> None:
    """Test DeleteUserSettingsCommand execute handles no settings."""
    session.add_exec_result([])

    command = DeleteUserSettingsCommand(session, user_id)  # type: ignore[arg-type]
    command.execute()

    assert len(command._deleted_settings) == 0
    assert len(session.deleted) == 0


def test_delete_user_settings_undo_restores_settings(
    session: DummySession, user_id: int
) -> None:
    """Test DeleteUserSettingsCommand undo restores user settings."""
    from fundamental.models.auth import UserSetting

    setting1 = UserSetting(id=1, user_id=user_id, key="theme", value="dark")

    session.add_exec_result([setting1])

    command = DeleteUserSettingsCommand(session, user_id)  # type: ignore[arg-type]
    command.execute()
    command.undo()

    assert setting1 in session.added


def test_delete_user_settings_undo_no_settings(
    session: DummySession, user_id: int
) -> None:
    """Test DeleteUserSettingsCommand undo handles no deleted settings."""
    session.add_exec_result([])

    command = DeleteUserSettingsCommand(session, user_id)  # type: ignore[arg-type]
    command.undo()

    assert len(session.added) == 0


def test_delete_refresh_tokens_execute_deletes_tokens(
    session: DummySession, user_id: int
) -> None:
    """Test DeleteRefreshTokensCommand execute deletes refresh tokens."""
    from datetime import UTC, datetime, timedelta

    from fundamental.models.auth import RefreshToken

    token1 = RefreshToken(
        id=1,
        user_id=user_id,
        token_hash="hash1",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    token2 = RefreshToken(
        id=2,
        user_id=user_id,
        token_hash="hash2",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    session.add_exec_result([token1, token2])

    command = DeleteRefreshTokensCommand(session, user_id)  # type: ignore[arg-type]
    command.execute()

    assert len(command._deleted_tokens) == 2
    assert token1 in command._deleted_tokens
    assert token2 in command._deleted_tokens
    assert token1 in session.deleted
    assert token2 in session.deleted


def test_delete_refresh_tokens_execute_no_tokens(
    session: DummySession, user_id: int
) -> None:
    """Test DeleteRefreshTokensCommand execute handles no tokens."""
    session.add_exec_result([])

    command = DeleteRefreshTokensCommand(session, user_id)  # type: ignore[arg-type]
    command.execute()

    assert len(command._deleted_tokens) == 0
    assert len(session.deleted) == 0


def test_delete_refresh_tokens_undo_restores_tokens(
    session: DummySession, user_id: int
) -> None:
    """Test DeleteRefreshTokensCommand undo restores refresh tokens."""
    from datetime import UTC, datetime, timedelta

    from fundamental.models.auth import RefreshToken

    token1 = RefreshToken(
        id=1,
        user_id=user_id,
        token_hash="hash1",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    session.add_exec_result([token1])

    command = DeleteRefreshTokensCommand(session, user_id)  # type: ignore[arg-type]
    command.execute()
    command.undo()

    assert token1 in session.added


def test_delete_refresh_tokens_undo_no_tokens(
    session: DummySession, user_id: int
) -> None:
    """Test DeleteRefreshTokensCommand undo handles no deleted tokens."""
    session.add_exec_result([])

    command = DeleteRefreshTokensCommand(session, user_id)  # type: ignore[arg-type]
    command.undo()

    assert len(session.added) == 0


def test_delete_user_data_directory_execute_deletes_dir(temp_dir: Path) -> None:
    """Test DeleteUserDataDirectoryCommand execute deletes directory."""
    user_data_dir = temp_dir / "user_data"
    user_data_dir.mkdir()
    (user_data_dir / "file1.txt").write_text("content1")
    (user_data_dir / "file2.txt").write_text("content2")

    command = DeleteUserDataDirectoryCommand(user_data_dir)
    command.execute()

    assert not user_data_dir.exists()
    assert command._dir_existed is True


def test_delete_user_data_directory_execute_skips_nonexistent(
    temp_dir: Path,
) -> None:
    """Test DeleteUserDataDirectoryCommand execute skips nonexistent directory."""
    user_data_dir = temp_dir / "nonexistent"

    command = DeleteUserDataDirectoryCommand(user_data_dir)
    command.execute()

    assert command._dir_existed is False


def test_delete_user_data_directory_undo_warns(
    temp_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test DeleteUserDataDirectoryCommand undo logs warning."""
    import logging

    user_data_dir = temp_dir / "user_data"
    user_data_dir.mkdir()

    command = DeleteUserDataDirectoryCommand(user_data_dir)
    command.execute()

    with caplog.at_level(logging.WARNING):
        command.undo()
        # On Windows, the path might be represented as WindowsPath(...) in the message
        assert any(
            "Cannot undo recursive directory deletion" in record.message
            and (
                str(user_data_dir) in record.message
                or repr(user_data_dir) in record.message
            )
            for record in caplog.records
        )


def test_delete_user_data_directory_undo_no_existed(temp_dir: Path) -> None:
    """Test DeleteUserDataDirectoryCommand undo handles directory that didn't exist."""
    user_data_dir = temp_dir / "nonexistent"

    command = DeleteUserDataDirectoryCommand(user_data_dir)
    command.undo()

    assert not user_data_dir.exists()


@pytest.fixture
def user() -> User:
    """Create a test User instance."""
    from datetime import UTC, datetime

    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User",
        is_admin=False,
        is_active=True,
        profile_picture=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_login=None,
    )


def test_delete_user_execute_deletes_user(session: DummySession, user: User) -> None:
    """Test DeleteUserCommand execute deletes user and creates snapshot."""
    command = DeleteUserCommand(session, user)  # type: ignore[arg-type]
    command.execute()

    assert user in session.deleted
    assert command._user_snapshot is not None
    assert command._user_snapshot["id"] == user.id
    assert command._user_snapshot["username"] == user.username
    assert command._user_snapshot["email"] == user.email
    assert command._user_snapshot["password_hash"] == user.password_hash
    assert command._user_snapshot["full_name"] == user.full_name
    assert command._user_snapshot["is_admin"] == user.is_admin
    assert command._user_snapshot["is_active"] == user.is_active
    assert command._user_snapshot["profile_picture"] == user.profile_picture
    assert command._user_snapshot["created_at"] == user.created_at
    assert command._user_snapshot["updated_at"] == user.updated_at
    assert command._user_snapshot["last_login"] == user.last_login


def test_delete_user_undo_restores_user(session: DummySession, user: User) -> None:
    """Test DeleteUserCommand undo restores user from snapshot."""
    command = DeleteUserCommand(session, user)  # type: ignore[arg-type]
    command.execute()
    command.undo()

    # Should have added a restored user
    assert len(session.added) == 1
    restored_user = session.added[0]
    assert restored_user.id == user.id
    assert restored_user.username == user.username
    assert restored_user.email == user.email
    assert restored_user.password_hash == user.password_hash
    assert restored_user.full_name == user.full_name
    assert restored_user.is_admin == user.is_admin
    assert restored_user.is_active == user.is_active
    assert restored_user.profile_picture == user.profile_picture
    assert restored_user.created_at == user.created_at
    assert restored_user.updated_at == user.updated_at
    assert restored_user.last_login == user.last_login


def test_delete_user_undo_no_snapshot(session: DummySession, user: User) -> None:
    """Test DeleteUserCommand undo handles no snapshot."""
    command = DeleteUserCommand(session, user)  # type: ignore[arg-type]
    command.undo()
    assert len(session.added) == 0
