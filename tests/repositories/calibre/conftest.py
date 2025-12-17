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

"""Shared fixtures for Calibre repository tests."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from bookcard.models.core import (
    Author,
    Book,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from bookcard.models.media import Data
from bookcard.repositories.calibre.retry import SQLiteRetryPolicy
from bookcard.repositories.interfaces import (
    IBookMetadataService,
    IBookRelationshipManager,
    IBookSearchService,
    IFileManager,
    ILibraryStatisticsService,
    ISessionManager,
)
from bookcard.services.book_metadata import BookMetadata

if TYPE_CHECKING:
    from collections.abc import Iterator


class MockSessionManager(ISessionManager):
    """Mock session manager for testing."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._disposed = False

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        yield self._session

    def dispose(self) -> None:
        self._disposed = True


class MockFileManager(IFileManager):
    """Mock file manager for testing."""

    def __init__(self) -> None:
        self.saved_files: list[dict] = []
        self.saved_covers: list[dict] = []
        self.collected_files: list[tuple[list[Path], Path | None]] = []
        self.moved_dirs: list[dict] = []

    def save_book_file(
        self,
        file_path: Path,
        library_path: Path,
        book_path_str: str,
        title_dir: str,
        file_format: str,
    ) -> None:
        self.saved_files.append({
            "file_path": file_path,
            "library_path": library_path,
            "book_path_str": book_path_str,
            "title_dir": title_dir,
            "file_format": file_format,
        })

    def save_book_cover(
        self,
        cover_data: bytes,
        library_path: Path,
        book_path_str: str,
    ) -> bool:
        self.saved_covers.append({
            "cover_data": cover_data,
            "library_path": library_path,
            "book_path_str": book_path_str,
        })
        return True

    def collect_book_files(
        self,
        session: Session,
        book_id: int,
        book_path: str,
        library_path: Path,
    ) -> tuple[list[Path], Path | None]:
        return self.collected_files.pop(0) if self.collected_files else ([], None)

    def move_book_directory(
        self,
        old_book_path: str,
        new_book_path: str,
        library_path: Path,
    ) -> None:
        self.moved_dirs.append({
            "old_book_path": old_book_path,
            "new_book_path": new_book_path,
            "library_path": library_path,
        })


class MockBookRelationshipManager(IBookRelationshipManager):
    """Mock relationship manager for testing."""

    def __init__(self) -> None:
        self.updated_authors: list[dict] = []
        self.updated_series: list[dict] = []
        self.updated_tags: list[dict] = []
        self.updated_identifiers: list[dict] = []
        self.updated_publishers: list[dict] = []
        self.updated_languages: list[dict] = []
        self.updated_ratings: list[dict] = []
        self.added_metadata: list[dict] = []

    def update_authors(
        self,
        session: Session,
        book_id: int,
        author_names: list[str],
    ) -> None:
        self.updated_authors.append({
            "session": session,
            "book_id": book_id,
            "author_names": author_names,
        })

    def update_series(
        self,
        session: Session,
        book_id: int,
        series_name: str | None = None,
        series_id: int | None = None,
    ) -> None:
        self.updated_series.append({
            "session": session,
            "book_id": book_id,
            "series_name": series_name,
            "series_id": series_id,
        })

    def update_tags(
        self,
        session: Session,
        book_id: int,
        tag_names: list[str],
    ) -> None:
        self.updated_tags.append({
            "session": session,
            "book_id": book_id,
            "tag_names": tag_names,
        })

    def update_identifiers(
        self,
        session: Session,
        book_id: int,
        identifiers: list[dict[str, str]],
    ) -> None:
        self.updated_identifiers.append({
            "session": session,
            "book_id": book_id,
            "identifiers": identifiers,
        })

    def update_publisher(
        self,
        session: Session,
        book_id: int,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
    ) -> None:
        self.updated_publishers.append({
            "session": session,
            "book_id": book_id,
            "publisher_name": publisher_name,
            "publisher_id": publisher_id,
        })

    def update_languages(
        self,
        session: Session,
        book_id: int,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
    ) -> None:
        self.updated_languages.append({
            "session": session,
            "book_id": book_id,
            "language_codes": language_codes,
            "language_ids": language_ids,
        })

    def update_rating(
        self,
        session: Session,
        book_id: int,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> None:
        self.updated_ratings.append({
            "session": session,
            "book_id": book_id,
            "rating_value": rating_value,
            "rating_id": rating_id,
        })

    def add_metadata(
        self,
        session: Session,
        book_id: int,
        metadata: BookMetadata,
    ) -> None:
        self.added_metadata.append({
            "session": session,
            "book_id": book_id,
            "metadata": metadata,
        })


class MockBookMetadataService(IBookMetadataService):
    """Mock metadata service for testing."""

    def __init__(self) -> None:
        self.extracted_metadata: list[dict] = []

    def extract_metadata(
        self,
        file_path: Path,
        file_format: str,
    ) -> tuple[BookMetadata, bytes | None]:
        metadata = MagicMock(spec=BookMetadata)
        metadata.title = "Test Book"
        metadata.author = "Test Author"
        metadata.pubdate = datetime.now(UTC)
        metadata.series_index = 1.0
        metadata.sort_title = None
        self.extracted_metadata.append({
            "file_path": file_path,
            "file_format": file_format,
        })
        return metadata, b"cover_data"


class MockBookSearchService(IBookSearchService):
    """Mock search service for testing."""

    def search_suggestions(
        self,
        session: Session,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        return {
            "books": [{"id": 1, "name": "Book 1"}],
            "authors": [{"id": 1, "name": "Author 1"}],
            "tags": [{"id": 1, "name": "Tag 1"}],
            "series": [{"id": 1, "name": "Series 1"}],
        }


class MockLibraryStatisticsService(ILibraryStatisticsService):
    """Mock statistics service for testing."""

    def get_statistics(self, session: Session) -> dict[str, int | float]:
        return {
            "total_books": 10,
            "total_series": 5,
            "total_authors": 8,
            "total_tags": 12,
            "total_ratings": 6,
            "total_content_size": 1000000,
        }


@pytest.fixture
def in_memory_db() -> Iterator[Session]:
    """Create an in-memory SQLite database session.

    Yields
    ------
    Session
        SQLModel session connected to in-memory database.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def session_manager(in_memory_db: Session) -> MockSessionManager:
    """Create a mock session manager.

    Parameters
    ----------
    in_memory_db : Session
        In-memory database session.

    Returns
    -------
    MockSessionManager
        Mock session manager.
    """
    return MockSessionManager(in_memory_db)


@pytest.fixture
def file_manager() -> MockFileManager:
    """Create a mock file manager.

    Returns
    -------
    MockFileManager
        Mock file manager.
    """
    return MockFileManager()


@pytest.fixture
def relationship_manager() -> MockBookRelationshipManager:
    """Create a mock relationship manager.

    Returns
    -------
    MockBookRelationshipManager
        Mock relationship manager.
    """
    return MockBookRelationshipManager()


@pytest.fixture
def metadata_service() -> MockBookMetadataService:
    """Create a mock metadata service.

    Returns
    -------
    MockBookMetadataService
        Mock metadata service.
    """
    return MockBookMetadataService()


@pytest.fixture
def search_service() -> MockBookSearchService:
    """Create a mock search service.

    Returns
    -------
    MockBookSearchService
        Mock search service.
    """
    return MockBookSearchService()


@pytest.fixture
def statistics_service() -> MockLibraryStatisticsService:
    """Create a mock statistics service.

    Returns
    -------
    MockLibraryStatisticsService
        Mock statistics service.
    """
    return MockLibraryStatisticsService()


@pytest.fixture
def retry_policy() -> SQLiteRetryPolicy:
    """Create a retry policy for testing.

    Returns
    -------
    SQLiteRetryPolicy
        Retry policy instance.
    """
    return SQLiteRetryPolicy(max_retries=3)


@pytest.fixture
def temp_library_path() -> Iterator[Path]:
    """Create a temporary library path.

    Yields
    ------
    Path
        Temporary library directory path.
    """
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_book(in_memory_db: Session) -> Book:
    """Create a sample book in the database.

    Parameters
    ----------
    in_memory_db : Session
        Database session.

    Returns
    -------
    Book
        Sample book instance.
    """
    book = Book(
        id=1,
        title="Test Book",
        sort="Test Book",
        author_sort="Test Author",
        timestamp=datetime.now(UTC),
        pubdate=datetime.now(UTC),
        series_index=1.0,
        flags=1,
        uuid="test-uuid",
        path="Test Author/Test Book",
        has_cover=False,
        last_modified=datetime.now(UTC),
    )
    in_memory_db.add(book)
    in_memory_db.commit()
    in_memory_db.refresh(book)
    return book


@pytest.fixture
def sample_author(in_memory_db: Session) -> Author:
    """Create a sample author in the database.

    Parameters
    ----------
    in_memory_db : Session
        Database session.

    Returns
    -------
    Author
        Sample author instance.
    """
    author = Author(id=1, name="Test Author", sort="Test Author")
    in_memory_db.add(author)
    in_memory_db.commit()
    in_memory_db.refresh(author)
    return author


@pytest.fixture
def sample_series(in_memory_db: Session) -> Series:
    """Create a sample series in the database.

    Parameters
    ----------
    in_memory_db : Session
        Database session.

    Returns
    -------
    Series
        Sample series instance.
    """
    series = Series(id=1, name="Test Series")
    in_memory_db.add(series)
    in_memory_db.commit()
    in_memory_db.refresh(series)
    return series


@pytest.fixture
def sample_tag(in_memory_db: Session) -> Tag:
    """Create a sample tag in the database.

    Parameters
    ----------
    in_memory_db : Session
        Database session.

    Returns
    -------
    Tag
        Sample tag instance.
    """
    tag = Tag(id=1, name="Test Tag")
    in_memory_db.add(tag)
    in_memory_db.commit()
    in_memory_db.refresh(tag)
    return tag


@pytest.fixture
def sample_publisher(in_memory_db: Session) -> Publisher:
    """Create a sample publisher in the database.

    Parameters
    ----------
    in_memory_db : Session
        Database session.

    Returns
    -------
    Publisher
        Sample publisher instance.
    """
    publisher = Publisher(id=1, name="Test Publisher")
    in_memory_db.add(publisher)
    in_memory_db.commit()
    in_memory_db.refresh(publisher)
    return publisher


@pytest.fixture
def sample_language(in_memory_db: Session) -> Language:
    """Create a sample language in the database.

    Parameters
    ----------
    in_memory_db : Session
        Database session.

    Returns
    -------
    Language
        Sample language instance.
    """
    language = Language(id=1, lang_code="en")
    in_memory_db.add(language)
    in_memory_db.commit()
    in_memory_db.refresh(language)
    return language


@pytest.fixture
def sample_rating(in_memory_db: Session) -> Rating:
    """Create a sample rating in the database.

    Parameters
    ----------
    in_memory_db : Session
        Database session.

    Returns
    -------
    Rating
        Sample rating instance.
    """
    rating = Rating(id=1, rating=5)
    in_memory_db.add(rating)
    in_memory_db.commit()
    in_memory_db.refresh(rating)
    return rating


@pytest.fixture
def sample_data(in_memory_db: Session, sample_book: Book) -> Data:
    """Create a sample data record in the database.

    Parameters
    ----------
    in_memory_db : Session
        Database session.
    sample_book : Book
        Book to associate data with.

    Returns
    -------
    Data
        Sample data instance.
    """
    data = Data(
        book=sample_book.id,
        format="EPUB",
        uncompressed_size=1000,
        name="Test Book",
    )
    in_memory_db.add(data)
    in_memory_db.commit()
    in_memory_db.refresh(data)
    return data
