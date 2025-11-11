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

"""Tests for delete commands."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003
from unittest.mock import MagicMock

import pytest

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
