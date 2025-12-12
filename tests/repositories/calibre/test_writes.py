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

"""Tests for writes module."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, select

from fundamental.models.core import Author, Book
from fundamental.repositories.calibre.writes import BookWriteOperations

if TYPE_CHECKING:
    from fundamental.repositories.calibre.retry import SQLiteRetryPolicy
from tests.repositories.calibre.conftest import (
    MockBookMetadataService,
    MockBookRelationshipManager,
    MockFileManager,
    MockSessionManager,
)


class TestBookWriteOperations:
    """Test suite for BookWriteOperations."""

    def test_add_book_file_not_found(
        self, in_memory_db: Session, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test add_book raises when file not found."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        get_book_full = MagicMock()

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
            get_book_full=get_book_full,
        )

        with pytest.raises(ValueError, match="File not found"):
            operations.add_book(
                file_path=Path("/nonexistent/file.epub"),
                file_format="epub",
            )

    def test_add_book_creates_book(
        self,
        in_memory_db: Session,
        temp_library_path: Path,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test add_book creates book record."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        pathing.prepare_book_path_and_format.return_value = (
            "Author/Book",
            "Book",
            "EPUB",
        )
        pathing.normalize_title_and_author.return_value = ("Test Book", "Test Author")
        get_book_full = MagicMock()

        with NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"test content")

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=temp_library_path,
            get_book_full=get_book_full,
        )

        book_id = operations.add_book(
            file_path=tmp_path,
            file_format="epub",
            title="Test Book",
            author_name="Test Author",
            library_path=temp_library_path,
        )

        assert book_id is not None
        book = in_memory_db.exec(select(Book).where(Book.id == book_id)).first()
        assert book is not None
        assert book.title == "Test Book"

        tmp_path.unlink()

    def test_update_book_not_found(
        self, in_memory_db: Session, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test update_book returns None when book not found."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        get_book_full = MagicMock(return_value=None)

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
            get_book_full=get_book_full,
        )

        result = operations.update_book(book_id=999, title="New Title")
        assert result is None

    def test_update_book_updates_title(
        self,
        in_memory_db: Session,
        sample_book: Book,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test update_book updates title."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        pathing.calculate_book_path.return_value = "Author/Test Book"
        get_book_full = MagicMock()

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
            get_book_full=get_book_full,
        )

        assert sample_book.id is not None
        operations.update_book(book_id=sample_book.id, title="Updated Title")

        in_memory_db.refresh(sample_book)
        assert sample_book.title == "Updated Title"

    def test_update_book_updates_authors(
        self,
        in_memory_db: Session,
        sample_book: Book,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test update_book updates authors."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        pathing.calculate_book_path.return_value = "Author/Test Book"
        get_book_full = MagicMock()

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
            get_book_full=get_book_full,
        )

        assert sample_book.id is not None
        operations.update_book(
            book_id=sample_book.id, author_names=["New Author 1", "New Author 2"]
        )

        assert len(relationship_manager.updated_authors) == 1
        assert relationship_manager.updated_authors[0]["author_names"] == [
            "New Author 1",
            "New Author 2",
        ]

    def test_get_or_create_author_creates_new(
        self, in_memory_db: Session, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test _get_or_create_author creates new author."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        get_book_full = MagicMock()

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
            get_book_full=get_book_full,
        )

        author = operations._get_or_create_author(
            session=in_memory_db, author_name="New Author"
        )

        assert author.name == "New Author"
        assert author.id is not None

    def test_get_or_create_author_returns_existing(
        self,
        in_memory_db: Session,
        sample_author: Author,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test _get_or_create_author returns existing author."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        get_book_full = MagicMock()

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
            get_book_full=get_book_full,
        )

        author = operations._get_or_create_author(
            session=in_memory_db, author_name=sample_author.name
        )

        assert author.id == sample_author.id
        assert author.name == sample_author.name

    def test_create_book_record(
        self, in_memory_db: Session, retry_policy: SQLiteRetryPolicy
    ) -> None:
        """Test _create_book_record creates book."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        get_book_full = MagicMock()

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
            get_book_full=get_book_full,
        )

        book = operations._create_book_record(
            session=in_memory_db,
            title="Test Book",
            author_name="Test Author",
            book_path_str="Author/Book",
            pubdate=datetime.now(UTC),
        )

        assert book.title == "Test Book"
        assert book.id is not None

    def test_update_book_updates_multiple_fields(
        self,
        in_memory_db: Session,
        sample_book: Book,
        retry_policy: SQLiteRetryPolicy,
    ) -> None:
        """Test update_book updates multiple fields."""
        session_manager = MockSessionManager(in_memory_db)
        file_manager = MockFileManager()
        relationship_manager = MockBookRelationshipManager()
        metadata_service = MockBookMetadataService()
        pathing = MagicMock()
        pathing.calculate_book_path.return_value = "Author/Test Book"
        get_book_full = MagicMock()

        operations = BookWriteOperations(
            session_manager=session_manager,
            retry_policy=retry_policy,
            file_manager=file_manager,
            relationship_manager=relationship_manager,
            metadata_service=metadata_service,
            pathing=pathing,
            calibre_db_path=Path("/tmp"),
            get_book_full=get_book_full,
        )

        assert sample_book.id is not None
        new_pubdate = datetime.now(UTC)
        operations.update_book(
            book_id=sample_book.id,
            title="Updated Title",
            pubdate=new_pubdate,
            series_index=2.0,
        )

        in_memory_db.refresh(sample_book)
        assert sample_book.title == "Updated Title"
        # Compare dates without timezone (database stores naive datetime)
        assert sample_book.pubdate is not None
        assert sample_book.pubdate.replace(tzinfo=None) == new_pubdate.replace(
            tzinfo=None
        )
        assert sample_book.series_index == 2.0
