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

"""Tests for formats module."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from sqlmodel import select

from bookcard.models.media import Data
from bookcard.repositories.calibre.formats import BookFormatOperations
from tests.repositories.calibre.conftest import MockFileManager, MockSessionManager

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.core import Book
    from bookcard.repositories.calibre.retry import SQLiteRetryPolicy


class TestBookFormatOperations:
    """Test suite for BookFormatOperations."""

    def test_add_format_book_not_found(
        self, in_memory_db: Session, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test add_format raises when book not found."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=tmp_path.parent,
        )

        with pytest.raises(ValueError, match="book_not_found"):
            operations.add_format(book_id=999, file_path=tmp_path, file_format="epub")

        tmp_path.unlink()

    def test_add_format_file_not_found(
        self, in_memory_db: Session, sample_book: Book, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test add_format raises when file not found."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
        )

        assert sample_book.id is not None
        with pytest.raises(ValueError, match="File not found"):
            operations.add_format(
                book_id=sample_book.id,
                file_path=Path("/nonexistent/file.epub"),
                file_format="epub",
            )

    def test_add_format_new_format(
        self, in_memory_db: Session, sample_book: Book, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test add_format adds new format."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        pathing.sanitize_title_dir.return_value = "Test Book"
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"test content")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=tmp_path.parent,
        )

        assert sample_book.id is not None
        operations.add_format(
            book_id=sample_book.id, file_path=tmp_path, file_format="epub"
        )

        # Verify format was added
        data = in_memory_db.exec(
            select(Data).where(Data.book == sample_book.id, Data.format == "EPUB")
        ).first()
        assert data is not None
        assert data.format == "EPUB"

        tmp_path.unlink()

    def test_add_format_replace_existing(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test add_format replaces existing format when replace=True."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        pathing.sanitize_title_dir.return_value = "Test Book"
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"new content")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=tmp_path.parent,
        )

        assert sample_book.id is not None
        operations.add_format(
            book_id=sample_book.id,
            file_path=tmp_path,
            file_format="epub",
            replace=True,
        )

        # Verify format was updated
        data = in_memory_db.exec(
            select(Data).where(Data.book == sample_book.id, Data.format == "EPUB")
        ).first()
        assert data is not None
        assert data.uncompressed_size == tmp_path.stat().st_size

        tmp_path.unlink()

    def test_add_format_raises_on_existing_format(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test add_format raises when format exists and replace=False."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        pathing.sanitize_title_dir.return_value = "Test Book"
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"test content")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=tmp_path.parent,
        )

        assert sample_book.id is not None
        with pytest.raises(FileExistsError):
            operations.add_format(
                book_id=sample_book.id,
                file_path=tmp_path,
                file_format="epub",
                replace=False,
            )

        tmp_path.unlink()

    def test_delete_format_book_not_found(
        self, in_memory_db: Session, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test delete_format raises when book not found."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
        )

        with pytest.raises(ValueError, match="book_not_found"):
            operations.delete_format(book_id=999, file_format="epub")

    def test_delete_format_format_not_found(
        self, in_memory_db: Session, sample_book: Book, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test delete_format raises when format not found."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
        )

        assert sample_book.id is not None
        with pytest.raises(ValueError, match=r"Format.*not found"):
            operations.delete_format(book_id=sample_book.id, file_format="pdf")

    def test_delete_format_without_file_deletion(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test delete_format without deleting file."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
        )

        assert sample_book.id is not None
        operations.delete_format(
            book_id=sample_book.id,
            file_format="epub",
            delete_file_from_drive=False,
        )

        # Verify format was deleted
        data = in_memory_db.exec(
            select(Data).where(Data.book == sample_book.id, Data.format == "EPUB")
        ).first()
        assert data is None

    def test_delete_format_strips_dot_from_format(
        self,
        in_memory_db: Session,
        sample_book: Book,
        sample_data: Data,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test delete_format strips dot from format."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
        )

        assert sample_book.id is not None
        operations.delete_format(
            book_id=sample_book.id, file_format=".epub", delete_file_from_drive=False
        )

        # Verify format was deleted
        data = in_memory_db.exec(
            select(Data).where(Data.book == sample_book.id, Data.format == "EPUB")
        ).first()
        assert data is None

    @pytest.mark.parametrize(
        ("file_format", "expected_format"),
        [
            ("epub", "EPUB"),
            ("EPUB", "EPUB"),
            (".epub", "EPUB"),
            (".EPUB", "EPUB"),
            ("pdf", "PDF"),
        ],
    )
    def test_add_format_normalizes_format(
        self,
        in_memory_db: Session,
        sample_book: Book,
        file_format: str,
        expected_format: str,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test add_format normalizes format (parametrized)."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        pathing = MagicMock()
        pathing.sanitize_title_dir.return_value = "Test Book"
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"test content")

        operations = BookFormatOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            pathing=pathing,
            calibre_db_path=tmp_path.parent,
        )

        assert sample_book.id is not None
        operations.add_format(
            book_id=sample_book.id, file_path=tmp_path, file_format=file_format
        )

        # Verify format was normalized
        data = in_memory_db.exec(
            select(Data).where(
                Data.book == sample_book.id, Data.format == expected_format
            )
        ).first()
        assert data is not None

        tmp_path.unlink()
