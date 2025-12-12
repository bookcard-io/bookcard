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

"""Additional tests for formats module to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from sqlmodel import Session, select

from fundamental.models.core import Book
from fundamental.models.media import Data
from fundamental.repositories.calibre.formats import BookFormatOperations
from tests.repositories.calibre.conftest import MockFileManager, MockSessionManager

if TYPE_CHECKING:
    from fundamental.repositories.calibre.retry import SQLiteRetryPolicy


class TestBookFormatOperationsAdditional:
    """Additional tests for BookFormatOperations to achieve 100% coverage."""

    def test_delete_format_with_file_deletion(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test delete_format deletes file from drive."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        # Create actual book directory and file
        book_dir = temp_library_path / sample_book.path
        book_dir.mkdir(parents=True, exist_ok=True)
        assert sample_book.id is not None
        test_file = book_dir / f"{sample_data.name or sample_book.id}.epub"
        test_file.write_text("test content")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=temp_library_path,
        )

        operations.delete_format(
            book_id=sample_book.id,
            file_format="epub",
            delete_file_from_drive=True,
        )

        # Verify format was deleted from database
        data = in_memory_db.exec(
            select(Data).where(Data.book == sample_book.id, Data.format == "EPUB")
        ).first()
        assert data is None

    def test_delete_format_file_with_none_book_id(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test _delete_format_file handles None book id."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=temp_library_path,
        )

        book_no_id = Book(
            id=None, title="Test", uuid="test", timestamp=datetime.now(UTC)
        )
        operations._delete_format_file(
            book=book_no_id,
            format_record=sample_data,
            file_format_upper="EPUB",
        )
        # Should return early without error

    def test_delete_format_file_with_nonexistent_dir(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test _delete_format_file handles nonexistent directory."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=temp_library_path,
        )

        assert sample_book.id is not None
        sample_book.path = "Nonexistent/Path"
        operations._delete_format_file(
            book=sample_book,
            format_record=sample_data,
            file_format_upper="EPUB",
        )
        # Should return early without error

    def test_find_format_file_path_by_name(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test _find_format_file_path finds file by name."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        book_dir = temp_library_path / sample_book.path
        book_dir.mkdir(parents=True, exist_ok=True)
        test_file = book_dir / f"{sample_data.name}.epub"
        test_file.write_text("test")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=temp_library_path,
        )

        assert sample_book.id is not None
        result = operations._find_format_file_path(
            book_dir=book_dir,
            format_record=sample_data,
            book_id=sample_book.id,
            format_upper="EPUB",
        )
        assert result == test_file

    def test_find_format_file_path_by_id(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test _find_format_file_path finds file by book id."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        book_dir = temp_library_path / sample_book.path
        book_dir.mkdir(parents=True, exist_ok=True)
        assert sample_book.id is not None
        test_file = book_dir / f"{sample_book.id}.epub"
        test_file.write_text("test")

        # Use format_record without name
        format_no_name = Data(
            book=sample_book.id,
            format="EPUB",
            uncompressed_size=1000,
            name=None,
        )

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=temp_library_path,
        )

        result = operations._find_format_file_path(
            book_dir=book_dir,
            format_record=format_no_name,
            book_id=sample_book.id,
            format_upper="EPUB",
        )
        assert result == test_file

    def test_find_format_file_path_by_iteration(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test _find_format_file_path finds file by directory iteration."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        book_dir = temp_library_path / sample_book.path
        book_dir.mkdir(parents=True, exist_ok=True)
        # Create file with different name
        test_file = book_dir / "different_name.epub"
        test_file.write_text("test")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=temp_library_path,
        )

        assert sample_book.id is not None
        result = operations._find_format_file_path(
            book_dir=book_dir,
            format_record=sample_data,
            book_id=sample_book.id,
            format_upper="EPUB",
        )
        assert result == test_file

    def test_find_format_file_path_returns_none(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test _find_format_file_path returns None when file not found."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        book_dir = temp_library_path / sample_book.path
        book_dir.mkdir(parents=True, exist_ok=True)
        # Create file with different format
        test_file = book_dir / "test.pdf"
        test_file.write_text("test")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=temp_library_path,
        )

        assert sample_book.id is not None
        result = operations._find_format_file_path(
            book_dir=book_dir,
            format_record=sample_data,
            book_id=sample_book.id,
            format_upper="EPUB",
        )
        assert result is None

    def test_delete_format_file_handles_oserror(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test _delete_format_file handles OSError gracefully."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        book_dir = temp_library_path / sample_book.path
        book_dir.mkdir(parents=True, exist_ok=True)
        test_file = book_dir / f"{sample_data.name or sample_book.id}.epub"
        test_file.write_text("test")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=temp_library_path,
        )

        assert sample_book.id is not None
        with patch.object(Path, "unlink", side_effect=OSError("Permission denied")):
            # Should not raise, just log warning
            operations._delete_format_file(
                book=sample_book,
                format_record=sample_data,
                file_format_upper="EPUB",
            )

    def test_get_library_path_with_file(
        self,
        in_memory_db: Session,
        sample_book: Book,
        retry_policy: SQLiteRetryPolicy,
        temp_library_path: Path,
    ) -> None:
        """Test _get_library_path when calibre_db_path is a file."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()

        db_file = temp_library_path / "metadata.db"
        db_file.touch()

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=db_file,
        )

        result = operations._get_library_path()
        assert result == temp_library_path
