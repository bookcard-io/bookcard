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

"""Tests for deletion module."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from bookcard.models.core import Book
from bookcard.repositories.calibre.deletion import BookDeletionOperations
from tests.repositories.calibre.conftest import MockFileManager, MockSessionManager

if TYPE_CHECKING:
    from bookcard.repositories.calibre.retry import SQLiteRetryPolicy


class TestBookDeletionOperations:
    """Test suite for BookDeletionOperations."""

    def test_delete_book_not_found(
        self, in_memory_db: Session, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test delete_book raises when book not found."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        operations = BookDeletionOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
        )

        with pytest.raises(ValueError, match="book_not_found"):
            operations.delete_book(book_id=999)

    def test_delete_book_without_files(
        self,
        in_memory_db: Session,
        sample_book: Book,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test delete_book without deleting files."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        operations = BookDeletionOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
        )

        assert sample_book.id is not None
        operations.delete_book(book_id=sample_book.id, delete_files_from_drive=False)

        # Verify book is deleted
        book = in_memory_db.exec(select(Book).where(Book.id == sample_book.id)).first()
        assert book is None

    def test_delete_book_with_files(
        self,
        in_memory_db: Session,
        sample_book: Book,
        temp_library_path: Path,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test delete_book with file deletion."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        from unittest.mock import patch

        assert sample_book.id is not None
        # Create a mock directory for deletion
        test_dir = temp_library_path / "test_dir"
        test_dir.mkdir(parents=True, exist_ok=True)
        with patch.object(
            file_manager,
            "collect_book_files",
            return_value=([Path("/tmp/test.epub")], test_dir),
        ):
            operations = BookDeletionOperations(
                session_manager=session_manager,
                retry_policy=retry_policy,
                file_manager=file_manager,
            )

            operations.delete_book(
                book_id=sample_book.id,
                delete_files_from_drive=True,
                library_path=temp_library_path,
            )

        # Verify book is deleted
        book = in_memory_db.exec(select(Book).where(Book.id == sample_book.id)).first()
        assert book is None

    def test_delete_book_rolls_back_on_error(
        self,
        in_memory_db: Session,
        sample_book: Book,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test delete_book rolls back on error."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        from unittest.mock import patch

        with patch.object(
            retry_policy, "commit", side_effect=SQLAlchemyError("Database error")
        ):
            operations = BookDeletionOperations(
                session_manager=session_manager,
                retry_policy=retry_policy,
                file_manager=file_manager,
            )

            assert sample_book.id is not None
            with pytest.raises(SQLAlchemyError):
                operations.delete_book(book_id=sample_book.id)

    def test_delete_book_with_empty_filesystem_paths(
        self,
        in_memory_db: Session,
        sample_book: Book,
        temp_library_path: Path,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test delete_book handles empty filesystem paths."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        from unittest.mock import patch

        assert sample_book.id is not None
        with patch.object(file_manager, "collect_book_files", return_value=([], None)):
            operations = BookDeletionOperations(
                session_manager=session_manager,
                retry_policy=retry_policy,
                file_manager=file_manager,
            )

            operations.delete_book(
                book_id=sample_book.id,
                delete_files_from_drive=True,
                library_path=temp_library_path,
            )

        # Verify book is deleted
        book = in_memory_db.exec(select(Book).where(Book.id == sample_book.id)).first()
        assert book is None

    def test_delete_book_executes_all_deletion_commands(
        self,
        in_memory_db: Session,
        sample_book: Book,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test delete_book executes all deletion commands."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        operations = BookDeletionOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
        )

        assert sample_book.id is not None
        operations.delete_book(book_id=sample_book.id)

        # Verify book is deleted
        book = in_memory_db.exec(select(Book).where(Book.id == sample_book.id)).first()
        assert book is None

    def test_raise_book_not_found(self) -> None:
        """Test _raise_book_not_found raises ValueError."""
        with pytest.raises(ValueError, match="book_not_found"):
            BookDeletionOperations._raise_book_not_found()

    def test_delete_book_with_none_library_path(
        self,
        in_memory_db: Session,
        sample_book: Book,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test delete_book handles None library_path when not deleting files."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        operations = BookDeletionOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
        )

        assert sample_book.id is not None
        operations.delete_book(
            book_id=sample_book.id, delete_files_from_drive=False, library_path=None
        )

        # Verify book is deleted
        book = in_memory_db.exec(select(Book).where(Book.id == sample_book.id)).first()
        assert book is None
